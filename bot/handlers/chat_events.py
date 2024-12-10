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
    # Проверяем, стал ли бот администратором
    if event.new_chat_member.status in ("administrator", "creator"):
        chat_id = event.chat.id
        chat_title = event.chat.title or "Без названия"

        if str(chat_id) not in chat_list:
            # Добавляем чат в список
            chat_list[str(chat_id)] = chat_title
            save_chat_list(chat_list)

            # Создаем настройки для нового чата
            if str(chat_id) not in chat_settings:
                chat_settings[str(chat_id)] = {"keywords": [], "banned_users": []}
                save_chat_settings(chat_settings)

            await event.bot.send_message(chat_id, "Чат добавлен в список для модерации.")


@router.message()
async def moderate_messages(message: Message):
    chat_id = str(message.chat.id)
    if chat_id in chat_settings:
        # Проверяем наличие запрещенных слов
        keywords = chat_settings.get(chat_id, {}).get("keywords", [])
        if any(keyword in message.text.lower() for keyword in keywords):
            # Удаляем сообщение
            await message.delete()

            # Баним пользователя
            try:
                await message.bot.ban_chat_member(chat_id=chat_id, user_id=message.from_user.id)

                # Обновляем настройки (добавляем пользователя в список забаненных)
                chat_settings[chat_id]["banned_users"].append(message.from_user.id)
                save_chat_settings(chat_settings)

                # Отправляем уведомление в чат
                await message.answer(
                    f"Пользователь {message.from_user.full_name} был заблокирован за использование запрещенных слов.")
            except Exception as e:
                await message.answer(f"Не удалось заблокировать пользователя: {e}")