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

            # await event.bot.send_message(chat_id, "Чат добавлен в список для модерации.")


@router.message()
async def moderate_messages(message: Message):
    if not message.text:
        return  # Игнорируем сообщения без текста (например, фото, видео, стикеры и т.д.)

    chat_id = str(message.chat.id)

    # Проверяем, есть ли настройки для текущего чата
    if chat_id in chat_settings:
        # Получаем ключевые слова для чата
        keywords = chat_settings[chat_id].get("keywords", [])

        # Если в сообщении есть запрещенные слова
        if any(keyword in message.text.lower() for keyword in keywords):
            try:
                # Удаляем сообщение
                await message.delete()

                # Баним пользователя
                await message.bot.ban_chat_member(chat_id=chat_id, user_id=message.from_user.id)

                # Сохраняем ID пользователя в список забаненных
                chat_settings[chat_id]["banned_users"].append(message.from_user.id)
                save_chat_settings(chat_settings)

                # Уведомляем о бане
                # await message.answer(
                #    f"Пользователь {message.from_user.full_name} был заблокирован за использование запрещенных слов."
                # )
            except Exception as e:
                print(f"Произошла ошибка при бане пользователя: {e}")
                # await message.answer(f"Произошла ошибка при бане пользователя: {e}")

@router.my_chat_member()
async def handle_bot_removal(event: ChatMemberUpdated):
    chat_id = str(event.chat.id)

    # Если бот был удалён из чата
    if event.new_chat_member.status == "left":
        # Удаляем чат из chat_list.json
        if chat_id in chat_list:
            del chat_list[chat_id]
            save_chat_list(chat_list)

        # Удаляем настройки чата из chat_settings.json
        if chat_id in chat_settings:
            del chat_settings[chat_id]
            save_chat_settings(chat_settings)

        print(f"Бот был удалён из чата {chat_id}. Он больше не отслеживается.")