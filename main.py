import json
import logging
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ChatMemberHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

# Настройка логирования
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Файлы для хранения данных
SETTINGS_FILE = "chat_settings.json"
CONFIG_FILE = "config.json"

# Загрузка конфигурации из config.json
def load_config():
    try:
        with open(CONFIG_FILE, "r") as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        logger.error("Файл config.json не найден или поврежден.")
        raise


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

# Глобальная переменная для отслеживания выбранной группы
selected_groups = {}


# Команда /start для отправки приветственного сообщения
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Добро пожаловать! Используйте меню команд Telegram для управления ботом. /list_groups"
    )


# Команда для просмотра списка групп
async def list_groups(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not chat_settings:
        await update.message.reply_text("Нет доступных групп.")
        return

    keyboard = []
    for group_id, settings in chat_settings.items():
        group_name = settings.get("group_name", "Без названия")
        keyboard.append([InlineKeyboardButton(f"{group_name} [{group_id}]", callback_data=f"select_group:{group_id}")])

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Выберите группу для настройки:", reply_markup=reply_markup)


# Обработчик кнопок
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data.startswith("select_group:"):
        group_id = query.data.split(":")[1]
        selected_groups[query.from_user.id] = group_id
        keyboard = [
            [InlineKeyboardButton("Добавить ключевые слова", callback_data="add_keywords")],
            [InlineKeyboardButton("Удалить ключевые слова", callback_data="remove_keywords")],
            [InlineKeyboardButton("Просмотреть настройки", callback_data="view_settings")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(f"Настройка группы {group_id}:", reply_markup=reply_markup)

    elif query.data == "add_keywords":
        await query.edit_message_text("Введите ключевые слова через пробел:")
        context.user_data["action"] = "add_keywords"

    elif query.data == "remove_keywords":
        await query.edit_message_text("Введите ключевые слова для удаления через пробел:")
        context.user_data["action"] = "remove_keywords"

    elif query.data == "view_settings":
        user_id = query.from_user.id
        group_id = selected_groups.get(user_id)
        if not group_id:
            await query.edit_message_text("Группа не выбрана.")
            return

        settings = chat_settings.get(group_id, {})
        keywords = settings.get("keywords", [])
        group_name = settings.get("group_name", "Без названия")
        await query.edit_message_text(f"Настройки группы {group_name} [{group_id}]:\nКлючевые слова: {', '.join(keywords)}")


# Обработчик текстовых сообщений для добавления/удаления ключевых слов
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    action = context.user_data.get("action")
    group_id = selected_groups.get(user_id)

    if not group_id:
        await update.message.reply_text("Группа не выбрана. Используйте меню команд для выбора группы.")
        return

    if action == "add_keywords":
        keywords = update.message.text.split()
        chat_settings[group_id].setdefault("keywords", []).extend(keywords)
        save_settings()
        await update.message.reply_text(f"Ключевые слова добавлены в группу {group_id}: {', '.join(keywords)}")
    elif action == "remove_keywords":
        keywords_to_remove = update.message.text.split()
        current_keywords = chat_settings[group_id].get("keywords", [])
        removed_keywords = [kw for kw in keywords_to_remove if kw in current_keywords]
        chat_settings[group_id]["keywords"] = [kw for kw in current_keywords if kw not in removed_keywords]
        save_settings()
        await update.message.reply_text(f"Удалены ключевые слова из группы {group_id}: {', '.join(removed_keywords)}")

    # Очистка действия после обработки
    context.user_data.pop("action", None)


# Обработчик для добавления новой группы
async def handle_group_update(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.my_chat_member.chat
    if chat.type in ["group", "supergroup"]:
        group_id = str(chat.id)
        group_name = chat.title or "Без названия"

        if group_id not in chat_settings:
            chat_settings[group_id] = {
                "group_name": group_name,
                "keywords": []
            }
            save_settings()
            logger.info(f"Добавлена новая группа: {group_name} [{group_id}]")

            # Отправляем сообщение в группу
            # await context.bot.send_message(
            #     chat_id=group_id,
            #     text=f"Группа '{group_name}' [{group_id}] добавлена в настройки бота. Вы можете настроить её через меню команд Telegram."
            # )


# Установка меню команд Telegram
async def set_bot_commands(application: Application):
    commands = [
        BotCommand("start", "Начать работу с ботом"),
        BotCommand("list_groups", "Показать список групп"),
    ]
    await application.bot.set_my_commands(commands)
    logger.info("Меню команд Telegram успешно установлено.")


# Основная функция запуска
def main():
    # Загружаем конфигурацию
    config = load_config()
    bot_token = config["telegram_token"]

    # Создаем приложение
    application = Application.builder().token(bot_token).build()

    # Команды
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("list_groups", list_groups))

    # Обработчики кнопок и текстовых сообщений
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    # Обработчик изменений чата, чтобы добавить группу
    application.add_handler(ChatMemberHandler(handle_group_update, filters.StatusUpdate.LEFT_CHAT_MEMBER))

    # Запуск приложения
    application.run_polling()

    # Установка меню команд Telegram
    asyncio.run(set_bot_commands(application))


if __name__ == '__main__':
    main()