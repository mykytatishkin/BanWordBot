import json
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.types import Message, ChatMemberUpdated, ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import Command
from aiogram.filters.chat_member_updated import ChatMemberUpdatedFilter
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.utils.keyboard import ReplyKeyboardBuilder

# Загрузка токена из config.json
with open("config.json", "r") as config_file:
    config = json.load(config_file)
    BOT_TOKEN = config["token"]

# Инициализация бота и диспетчера
bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# Логирование
logging.basicConfig(level=logging.INFO)

# Загрузка настроек чатов и списка чатов
SETTINGS_FILE = "chat_settings.json"
CHATS_FILE = "chat_list.json"

try:
    with open(SETTINGS_FILE, "r") as settings_file:
        chat_settings = json.load(settings_file)
except FileNotFoundError:
    chat_settings = {}

try:
    with open(CHATS_FILE, "r") as chats_file:
        chat_list = json.load(chats_file)
except FileNotFoundError:
    chat_list = {}


# Функция для сохранения настроек
def save_settings():
    with open(SETTINGS_FILE, "w") as settings_file:
        json.dump(chat_settings, settings_file, indent=4)


# Функция для сохранения списка чатов
def save_chat_list():
    with open(CHATS_FILE, "w") as chats_file:
        json.dump(chat_list, chats_file, indent=4)


# Основная клавиатура
def main_menu():
    builder = ReplyKeyboardBuilder()
    builder.row(
        KeyboardButton(text="Список чатов"),
        KeyboardButton(text="Добавить ключевое слово"),
        KeyboardButton(text="Удалить ключевое слово")
    )
    builder.row(KeyboardButton(text="Список ключевых слов"))
    return builder.as_markup(resize_keyboard=True)

@dp.message(lambda msg: msg.text == "Список ключевых слов")
async def list_keywords_prompt(message: Message):
    await message.answer("Отправьте команду в формате:\n/list_keywords <chat_id>\nПример:\n/list_keywords -1002264996867")

# Обработка команды /start
@dp.message(Command("start"))
async def handle_start(message: Message):
    await message.answer(
        "Привет! Я помогу вам настроить автоматическую модерацию чатов. Используйте кнопки ниже для взаимодействия.",
        reply_markup=main_menu()
    )


# Вывод списка чатов
@dp.message(lambda msg: msg.text == "Список чатов")
async def list_chats(message: Message):
    if not chat_list:
        await message.answer("Бот еще не добавлен ни в один чат.")
        return

    chat_info = "\n".join([f"{chat_id}: {name}" for chat_id, name in chat_list.items()])
    await message.answer(f"Список чатов:\n{chat_info}\n\nВыберите ID чата для настройки.")


# Добавление ключевого слова
@dp.message(lambda msg: msg.text == "Добавить ключевое слово")
async def add_keyword_prompt(message: Message):
    await message.answer("Отправьте команду в формате:\n/add_keyword <chat_id> <ключевое_слово>")


# Удаление ключевого слова
@dp.message(lambda msg: msg.text == "Удалить ключевое слово")
async def remove_keyword_prompt(message: Message):
    await message.answer("Отправьте команду в формате:\n/remove_keyword <chat_id> <ключевое_слово>")


# Команда для отображения списка ключевых слов
@dp.message(Command("list_keywords"))
async def list_keywords(message: Message):
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer("Использование: /list_keywords <chat_id>")
        return

    chat_id = args[1]

    if chat_id not in chat_settings:
        await message.answer(f"Чат с ID {chat_id} не найден или не настроен.")
        return

    keywords = chat_settings[chat_id].get("keywords", [])
    if keywords:
        await message.answer(f"Ключевые слова для чата {chat_id}: {', '.join(keywords)}")
    else:
        await message.answer(f"Для чата {chat_id} ключевые слова отсутствуют.")


# Обработка сообщений для удаления запрещённых слов
@dp.message()
async def delete_prohibited_message(message: Message):
    chat_id = str(message.chat.id)
    user_id = message.from_user.id

    # Проверяем, есть ли настройки для чата
    if chat_id not in chat_settings:
        return

    # Получаем ключевые слова для чата
    keywords = chat_settings[chat_id].get("keywords", [])
    if not keywords:
        return

    # Проверяем, содержит ли сообщение запрещённые слова
    for keyword in keywords:
        if keyword.lower() in message.text.lower():
            try:
                # Удаляем сообщение
                await message.delete()
                logging.info(f"Удалено сообщение с запрещённым словом '{keyword}' в чате {chat_id}.")

                # Пытаемся заблокировать пользователя
                try:
                    await bot.ban_chat_member(chat_id, user_id)
                    logging.info(f"Пользователь {user_id} забанен в чате {chat_id}.")

                    # Сохраняем ID забаненного пользователя
                    chat_settings[chat_id].setdefault("banned_users", []).append(user_id)
                    save_settings()
                except Exception as ban_error:
                    logging.error(f"Ошибка при блокировке пользователя {user_id}: {ban_error}")

                return
            except Exception as delete_error:
                logging.error(f"Не удалось удалить сообщение: {delete_error}")
                return

# Обработка добавления бота в чат
@dp.chat_member(ChatMemberUpdatedFilter(member_status_changed=["member", "administrator"]))
async def handle_new_chat_member(event: ChatMemberUpdated):
    chat_id = str(event.chat.id)
    if event.new_chat_member.user.id == bot.id:  # Проверяем, что бот был добавлен в чат
        chat_list[chat_id] = event.chat.title or "Группа без названия"
        save_chat_list()
        logging.info(f"Чат {chat_list[chat_id]} добавлен для отслеживания.")


# Запуск бота
async def main():
    logging.info("Бот запускается...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())