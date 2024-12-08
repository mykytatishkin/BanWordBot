import json
import logging
from telegram import Update, ChatMember
from telegram.ext import Application, CommandHandler, MessageHandler, ChatMemberHandler, ContextTypes, filters
from telegram.error import BadRequest

# Настройка логирования
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Имя файла для хранения данных
SETTINGS_FILE = "chat_settings.json"


# Загрузка настроек из JSON-файла
def load_settings():
    try:
        with open(SETTINGS_FILE, "r") as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        logger.warning("Файл настроек не найден или поврежден. Создаю новый.")
        return {}


# Сохранение настроек в JSON-файл
def save_settings():
    with open(SETTINGS_FILE, "w") as file:
        json.dump(chat_settings, file, indent=4)
        logger.info("Настройки успешно сохранены в файл.")


# Глобальная переменная для хранения настроек
chat_settings = load_settings()


# Проверка, является ли пользователь администратором
async def is_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    chat_id = update.message.chat_id
    user_id = update.message.from_user.id

    # Получаем статус пользователя
    chat_member = await context.bot.get_chat_member(chat_id, user_id)
    return chat_member.status in [ChatMember.ADMINISTRATOR, ChatMember.OWNER]


# Команда для добавления ключевых слов
async def set_keywords(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        await update.message.reply_text("Только администраторы могут использовать эту команду.")
        return

    chat_id = str(update.message.chat_id)
    if chat_id not in chat_settings:
        chat_settings[chat_id] = {'keywords': [], 'banned_users': []}

    keywords = context.args
    if keywords:
        chat_settings[chat_id]['keywords'].extend(keywords)
        save_settings()
        await update.message.reply_text(f"Ключевые слова добавлены: {', '.join(keywords)}")
        logger.info(f"Добавлены ключевые слова для чата {chat_id}: {', '.join(keywords)}")
    else:
        await update.message.reply_text("Пожалуйста, укажите ключевые слова после команды.")
        logger.info(f"Не указаны ключевые слова в чате {chat_id}")


# Команда для удаления ключевых слов
async def remove_keywords(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        await update.message.reply_text("Только администраторы могут использовать эту команду.")
        return

    chat_id = str(update.message.chat_id)
    if chat_id not in chat_settings:
        await update.message.reply_text("Настройки для этого чата не найдены.")
        return

    keywords_to_remove = context.args
    if not keywords_to_remove:
        await update.message.reply_text("Пожалуйста, укажите ключевые слова для удаления.")
        return

    current_keywords = chat_settings[chat_id]['keywords']
    removed_keywords = [kw for kw in keywords_to_remove if kw in current_keywords]

    if removed_keywords:
        chat_settings[chat_id]['keywords'] = [kw for kw in current_keywords if kw not in removed_keywords]
        save_settings()
        await update.message.reply_text(f"Удалены ключевые слова: {', '.join(removed_keywords)}")
        logger.info(f"Удалены ключевые слова для чата {chat_id}: {', '.join(removed_keywords)}")
    else:
        await update.message.reply_text("Указанные ключевые слова не найдены.")


# Обработчик для проверки сообщений
async def check_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.message.chat_id)
    if chat_id in chat_settings:
        keywords = chat_settings[chat_id].get('keywords', [])
        message_text = update.message.text.lower()
        for keyword in keywords:
            if keyword.lower() in message_text:
                try:
                    user_id = update.message.from_user.id
                    username = update.message.from_user.username

                    # Удаляем сообщение
                    await update.message.delete()

                    # Баним пользователя бессрочно
                    await context.bot.ban_chat_member(chat_id, user_id, until_date=None)

                    # Добавляем пользователя в список заблокированных
                    banned_user_info = {
                        "user_id": user_id,
                        "username": username or "unknown"
                    }
                    chat_settings[chat_id].setdefault("banned_users", []).append(banned_user_info)
                    save_settings()  # Сохраняем изменения

                    # Отправляем сообщение о бане
                    await context.bot.send_message(
                        chat_id=chat_id,
                        text=f"Пользователь @{username} был забанен за использование запрещенного слова."
                    )
                    logger.info(f"Пользователь @{username} (ID: {user_id}) забанен в чате {chat_id}")
                except BadRequest as e:
                    logger.error(f"Ошибка при удалении сообщения или бане пользователя: {e}")
                    await context.bot.send_message(
                        chat_id=chat_id,
                        text="Ошибка при удалении сообщения или бане пользователя."
                    )
                return


# Обработчик для проверки входа пользователей
async def handle_chat_member_update(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.chat_member.chat.id)
    new_member = update.chat_member.new_chat_member

    # Проверяем, если это добавление нового участника
    if new_member.status in ["member", "administrator"]:
        user_id = new_member.user.id
        username = new_member.user.username or "unknown"

        # Проверяем, если пользователь в списке заблокированных
        if chat_id in chat_settings and "banned_users" in chat_settings[chat_id]:
            banned_users = chat_settings[chat_id]["banned_users"]
            if any(banned_user["user_id"] == user_id for banned_user in banned_users):
                try:
                    # Удаляем пользователя из чата
                    await context.bot.ban_chat_member(chat_id, user_id, until_date=None)
                    await context.bot.send_message(
                        chat_id=chat_id,
                        text=f"Пользователь @{username} был автоматически удален из чата за повторный вход."
                    )
                    logger.info(f"Пользователь @{username} (ID: {user_id}) удален из чата {chat_id} за повторный вход.")
                except BadRequest as e:
                    logger.error(f"Ошибка при удалении пользователя @{username} (ID: {user_id}): {e}")


# Команда для отображения текущих настроек
async def get_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.message.chat_id)
    if chat_id in chat_settings:
        keywords = chat_settings[chat_id].get('keywords', [])
        await update.message.reply_text(f"Ключевые слова: {', '.join(keywords)}")
        logger.info(f"Отправлены настройки для чата {chat_id}: {', '.join(keywords)}")
    else:
        await update.message.reply_text("Настройки для этого чата не найдены.")
        logger.info(f"Запрос настроек для чата {chat_id}, но настроек не найдено")


# Команда /start для отображения списка доступных команд
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    commands = """
Добро пожаловать! Вот список доступных команд:
/start - Показать этот список команд
/set_keywords <слово1> <слово2> ... - Добавить ключевые слова для бана (только администраторы)
/remove_keywords <слово1> <слово2> ... - Удалить ключевые слова (только администраторы)
/get_settings - Показать текущие настройки
"""
    await update.message.reply_text(commands)
    logger.info(f"Пользователь {update.message.from_user.username} вызвал команду /start")


# Основная функция запуска
def main():
    # Вставьте токен вашего бота
    bot_token = "7641198018:AAERdwp9s3DK4_EYaqZto87KdCJTrnvpDyw"

    # Создаем приложение
    application = Application.builder().token(bot_token).build()

    # Команды
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("set_keywords", set_keywords))
    application.add_handler(CommandHandler("remove_keywords", remove_keywords))
    application.add_handler(CommandHandler("get_settings", get_settings))

    # Обработчик сообщений
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, check_message))

    # Обработчик изменений участников чата
    application.add_handler(ChatMemberHandler(handle_chat_member_update))

    # Лог о запуске бота
    logger.info("Бот запущен. Ожидаю события...")

    # Запуск бота
    application.run_polling()


if __name__ == '__main__':
    main()