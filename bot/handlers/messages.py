from aiogram import Router
from aiogram.types import Message
from bot.utils.file_utils import load_chat_list, load_chat_settings, save_chat_settings

router = Router()

chat_list = load_chat_list()
chat_settings = load_chat_settings()

@router.message(lambda msg: msg.chat.type == "private" and msg.text == "Список чатов")
async def list_chats(message: Message):
    if not chat_list:
        await message.answer("Бот еще не добавлен ни в один чат.")
        return

    chat_info = "\n".join([f"{chat_id}: {name}" for chat_id, name in chat_list.items()])
    await message.answer(f"Список чатов:\n{chat_info}\n\nВыберите ID чата для настройки.")

@router.message(lambda msg: msg.chat.type == "private" and msg.text == "Добавить ключевое слово")
async def add_keyword_prompt(message: Message):
    await message.answer("Отправьте команду в формате:\n/add_keyword <chat_id> <ключевое_слово>")

@router.message(lambda msg: msg.chat.type == "private" and msg.text and msg.text.startswith("/add_keyword"))
async def add_keyword(message: Message):
    try:
        # Извлекаем параметры из команды
        _, chat_id, keyword = message.text.split(" ", 2)

        # Проверяем, есть ли настройки для указанного чата
        if chat_id not in chat_settings:
            chat_settings[chat_id] = {"keywords": [], "banned_users": []}

        # Добавляем ключевое слово, если его еще нет
        if keyword not in chat_settings[chat_id]["keywords"]:
            chat_settings[chat_id]["keywords"].append(keyword)
            save_chat_settings(chat_settings)  # Сохраняем настройки в файл
            await message.answer(f"Ключевое слово '{keyword}' добавлено для чата {chat_id}.")
        else:
            await message.answer(f"Ключевое слово '{keyword}' уже существует в чате {chat_id}.")
    except ValueError:
        await message.answer("Используйте формат: /add_keyword <chat_id> <ключевое_слово>")
    except Exception as e:
        await message.answer(f"Ошибка: {e}")

@router.message(lambda msg: msg.chat.type == "private" and msg.text == "Удалить ключевое слово")
async def remove_keyword_prompt(message: Message):
    await message.answer("Отправьте команду в формате:\n/remove_keyword <chat_id> <ключевое_слово>")

@router.message(lambda msg: msg.chat.type == "private" and msg.text == "Список ключевых слов")
async def remove_keyword_prompt(message: Message):
    await message.answer("Отправьте команду в формате:\n/list_keywords <chat_id>")


@router.message(lambda msg: msg.chat.type == "private" and msg.text and msg.text.startswith("/list_keywords"))
async def list_keywords(message: Message):
    try:
        # Извлекаем chat_id из команды
        _, chat_id = message.text.split(" ", 1)

        if chat_id not in chat_settings:
            await message.answer(f"Чат с ID {chat_id} не найден.")
            return

        keywords = chat_settings[chat_id].get("keywords", [])
        if not keywords:
            await message.answer(f"В чате с ID {chat_id} нет ключевых слов.")
            return

        await message.answer(f"Ключевые слова для чата {chat_id}:\n" + "\n".join(keywords))
    except ValueError:
        await message.answer("Используйте формат: /list_keywords <chat_id>")