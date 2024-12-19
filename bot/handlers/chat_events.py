from aiogram import Router
from aiogram.types import ChatMemberUpdated, Message
from bot.utils.file_utils import load_chat_list, save_chat_list, load_chat_settings, save_chat_settings

router = Router()

# Загружаем данные
chat_list = load_chat_list()
chat_settings = load_chat_settings()

# Обработчик: Добавление чата в список при выдаче админских прав
@router.my_chat_member()
async def add_chat_to_list(event: ChatMemberUpdated):
    print(f"Получено событие изменения прав: {event.chat.id}, статус: {event.new_chat_member.status}")

    # Проверяем, стал ли бот администратором
    if event.new_chat_member.status in ("administrator", "creator"):
        chat_id = str(event.chat.id)
        chat_title = event.chat.title or "Без названия"

        if chat_id not in chat_list:
            # Добавляем чат в список
            chat_list[chat_id] = chat_title
            save_chat_list(chat_list)
            print(f"Чат добавлен: {chat_id} - {chat_title}")

        # Создаём настройки для нового чата, если их ещё нет
        if chat_id not in chat_settings:
            chat_settings[chat_id] = {"keywords": [], "banned_users": []}
            save_chat_settings(chat_settings)
            print(f"Созданы настройки для чата: {chat_id} - {chat_settings[chat_id]}")

@router.message()
async def moderate_messages(message: Message):
    print(f"Получено сообщение из чата {message.chat.id}: {message.text}")
    if not message.text:
        print("Сообщение не содержит текста, игнорируем.")
        return

    chat_id = str(message.chat.id)
    chat_settings = load_chat_settings()

    # Проверяем, есть ли настройки для текущего чата
    if chat_id in chat_settings:
        keywords = chat_settings[chat_id].get("keywords", [])
        print(f"Ключевые слова для чата {chat_id}: {keywords}")

        # Если сообщение содержит запрещённые слова
        if any(keyword.lower() in message.text.lower() for keyword in keywords):
            try:
                # Удаляем сообщение
                await message.delete()
                print(f"Удалено сообщение: {message.text}")
            except Exception as e:
                print(f"Ошибка при удалении сообщения: {e}")

@router.my_chat_member()
async def handle_bot_removal(event: ChatMemberUpdated):
    chat_id = str(event.chat.id)

    # Если бот был удалён из чата
    if event.new_chat_member.status == "left":
        print(f"Бот удалён из чата: {chat_id}")

        # Удаляем чат из chat_list.json
        if chat_id in chat_list:
            del chat_list[chat_id]
            save_chat_list(chat_list)
            print(f"Чат удалён из списка: {chat_id}")

        # Удаляем настройки чата из chat_settings.json
        if chat_id in chat_settings:
            del chat_settings[chat_id]
            save_chat_settings(chat_settings)
            print(f"Настройки чата удалены: {chat_id}")