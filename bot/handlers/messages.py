from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters.callback_data import CallbackData
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from bot.utils.file_utils import load_chat_list, load_chat_settings, save_chat_settings, save_chat_list
from datetime import datetime
from aiogram.fsm.state import State, StatesGroup
import json
import logging


logging.basicConfig(level=logging.INFO)
router = Router()
storage = MemoryStorage()  # Используем FSM Storage

chat_list = load_chat_list()
chat_settings = load_chat_settings()

class ImportStates(StatesGroup):
    waiting_for_chat_list = State()
    waiting_for_chat_settings = State()

# Определяем состояние для FSM
class AddKeywordStates(StatesGroup):
    waiting_for_keyword = State()
    waiting_for_keyword_removal = State()

# CallbackData для обработки выбора чата и настроек
class ChatCallbackData(CallbackData, prefix="chat"):
    chat_id: str
    action: str

async def update_message(callback, text, reply_markup=None):
    current_text = callback.message.text
    current_markup = callback.message.reply_markup

    # Проверяем, изменилось ли сообщение или разметка
    if current_text == text and current_markup == reply_markup:
        logging.info("Сообщение и разметка не изменились, обновление пропущено.")
        return

    # Обновляем сообщение
    await callback.message.edit_text(text, reply_markup=reply_markup)

# Список чатов
@router.message(F.chat.type == "private", F.text == "Список чатов")
@router.message(F.chat.type == "private", F.text == "Список чатов")
async def list_chats(message: Message):
    chat_list = load_chat_list()  # Перезагружаем chat_list из файла

    if not chat_list:
        await message.answer("Бот еще не добавлен ни в один чат.")
        return

    buttons = [
        [
            InlineKeyboardButton(text=name, callback_data=ChatCallbackData(chat_id=chat_id, action="select").pack())
        ]
        for chat_id, name in chat_list.items()
    ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    await message.answer("Выберите чат для настройки:", reply_markup=keyboard)

# Обработка выбора чата
@router.callback_query(ChatCallbackData.filter(F.action == "select"))
async def chat_selected(callback: CallbackQuery, callback_data: ChatCallbackData):
    chat_id = callback_data.chat_id

    buttons = [
        [
            InlineKeyboardButton(
                text="➕ Добавить слово",
                callback_data=ChatCallbackData(chat_id=chat_id, action="add_keyword").pack()
            ),
            InlineKeyboardButton(
                text="➖ Удалить слово",
                callback_data=ChatCallbackData(chat_id=chat_id, action="remove_keyword").pack()
            ),
        ],
        [
            InlineKeyboardButton(
                text="📋 Список слов",
                callback_data=ChatCallbackData(chat_id=chat_id, action="list_keywords").pack()
            ),
            InlineKeyboardButton(
                text="❌ Удалить из отслеживаемых",
                callback_data=ChatCallbackData(chat_id=chat_id, action="remove_from_tracking").pack()
            ),
        ],
    ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

    # Обновляем сообщение, используя функцию update_message
    await update_message(
        callback,
        text=f"Вы выбрали чат {chat_id}. Выберите действие:",
        reply_markup=keyboard
    )

# Добавление ключевого слова
@router.callback_query(ChatCallbackData.filter(F.action == "add_keyword"))
async def add_keyword_start(callback: CallbackQuery, callback_data: ChatCallbackData, state: FSMContext):
    chat_id = callback_data.chat_id
    await state.update_data(chat_id=chat_id)  # Сохраняем ID чата в FSM
    await state.set_state(AddKeywordStates.waiting_for_keyword)
    await callback.message.answer(f"Введите ключевое слово для добавления в чат {chat_id}.")

@router.message(AddKeywordStates.waiting_for_keyword)
async def add_keyword_finish(message: Message, state: FSMContext):
    data = await state.get_data()
    chat_id = data.get("chat_id")
    keyword = message.text.strip()

    chat_settings = load_chat_settings()  # Перезагружаем настройки

    if not chat_id:
        logging.error("Чат не выбран, но функция add_keyword_finish вызвана.")
        await message.answer("Чат не выбран. Вернитесь в меню и выберите чат.")
        await state.clear()
        return

    if chat_id not in chat_settings:
        chat_settings[chat_id] = {"keywords": [], "banned_users": []}
    if keyword not in chat_settings[chat_id]["keywords"]:
        chat_settings[chat_id]["keywords"].append(keyword)
        save_chat_settings(chat_settings)
        logging.info(f"Добавлено ключевое слово '{keyword}' для чата {chat_id}.")
        await message.answer(f"Ключевое слово '{keyword}' добавлено для чата {chat_id}.")
    else:
        logging.warning(f"Ключевое слово '{keyword}' уже существует для чата {chat_id}.")
        await message.answer(f"Ключевое слово '{keyword}' уже существует в чате {chat_id}.")

    await state.clear()

# Удаление ключевого слова
@router.callback_query(ChatCallbackData.filter(F.action == "remove_keyword"))
async def remove_keyword_start(callback: CallbackQuery, callback_data: ChatCallbackData, state: FSMContext):
    chat_id = callback_data.chat_id
    await state.update_data(chat_id=chat_id)  # Сохраняем ID чата в FSM
    await state.set_state(AddKeywordStates.waiting_for_keyword_removal)
    await callback.message.answer(f"Введите ключевое слово для удаления из чата {chat_id}.")

@router.message(AddKeywordStates.waiting_for_keyword_removal)
async def remove_keyword_finish(message: Message, state: FSMContext):
    data = await state.get_data()
    chat_id = data.get("chat_id")
    keyword = message.text.strip()

    if not chat_id:
        await message.answer("Чат не выбран. Вернитесь в меню и выберите чат.")
        await state.clear()
        return

    if chat_id in chat_settings and keyword in chat_settings[chat_id].get("keywords", []):
        chat_settings[chat_id]["keywords"].remove(keyword)
        save_chat_settings(chat_settings)
        await message.answer(f"Ключевое слово '{keyword}' удалено из чата {chat_id}.")
    else:
        await message.answer(f"Ключевое слово '{keyword}' не найдено в чате {chat_id}.")

    await state.clear()

# Список ключевых слов
@router.callback_query(ChatCallbackData.filter(F.action == "list_keywords"))
async def list_keywords(callback: CallbackQuery, callback_data: ChatCallbackData):
    chat_settings = load_chat_settings()  # Перезагружаем настройки
    chat_id = callback_data.chat_id
    keywords = chat_settings.get(chat_id, {}).get("keywords", [])

    if keywords:
        await callback.message.answer(f"Ключевые слова для чата {chat_id}:\n" + "\n".join(keywords))
    else:
        await callback.message.answer(f"В чате {chat_id} нет ключевых слов.")

@router.message(F.text == "Моментальное резервное копирование")
async def instant_backup_handler(message: Message):
    try:
        current_time = datetime.now().strftime("%H:%M")
        date = datetime.now().strftime("%d.%m.%Y")

        # Заголовок сообщения
        message_text = (
            f"<b>Время на часах:</b> {current_time}\n"
            f"<b>Моментальное резервное копирование за {date}</b>\n\n"
        )

        # Загрузка данных для резервного копирования
        json_data = {
            "chat-list.json": load_chat_list(),  # Заменяем chat_list.json на chat-list.json
            "chat-settings.json": load_chat_settings(),  # Заменяем chat_settings.json на chat-settings.json
        }

        # Форматирование данных
        for file_name, content in json_data.items():
            # Преобразуем JSON в текст и заменяем "_" на "-"
            content_str = json.dumps(content, ensure_ascii=False, indent=4).replace("_", "-")
            message_text += (
                f"<b>{file_name}</b>\n"
                f"<pre>{content_str}</pre>\n\n"
            )

        # Отправка сообщения
        await message.answer(message_text, parse_mode="HTML")
    except Exception as e:
        await message.answer(f"Ошибка при моментальном резервном копировании: {e}")

# Импорт для chat_list.json
@router.message(F.text == "Импорт настроек для chat_list.json")
async def import_chat_list_start(message: Message, state: FSMContext):
    await state.set_state(ImportStates.waiting_for_chat_list)
    await message.answer("Отправьте JSON-данные для обновления chat_list.json.")

@router.message(ImportStates.waiting_for_chat_list)
async def import_chat_list(message: Message, state: FSMContext):
    try:
        # Проверка и загрузка JSON
        data = json.loads(message.text)
        if not isinstance(data, dict):
            raise ValueError("Ожидается JSON-объект (словарь).")

        # Обновление chat_list.json
        save_chat_list(data)
        logging.info("chat_list.json успешно обновлён.")
        await message.answer("chat_list.json успешно обновлён.")
    except json.JSONDecodeError:
        await message.answer("Ошибка: Неверный формат JSON. Попробуйте снова.")
    except Exception as e:
        logging.error(f"Ошибка при обновлении chat_list.json: {e}")
        await message.answer(f"Ошибка при обновлении chat_list.json: {e}")
    finally:
        await state.clear()

# Импорт для chat_settings.json
@router.message(F.text == "Импорт настроек для chat_settings.json")
async def import_chat_settings_start(message: Message, state: FSMContext):
    await state.set_state(ImportStates.waiting_for_chat_settings)
    await message.answer("Отправьте JSON-данные для обновления chat_settings.json.")

@router.message(ImportStates.waiting_for_chat_settings)
async def import_chat_settings(message: Message, state: FSMContext):
    try:
        # Проверка и загрузка JSON
        data = json.loads(message.text)
        if not isinstance(data, dict):
            raise ValueError("Ожидается JSON-объект (словарь).")

        # Обновление chat_settings.json
        save_chat_settings(data)
        logging.info("chat_settings.json успешно обновлён.")
        await message.answer("chat_settings.json успешно обновлён.")
    except json.JSONDecodeError:
        await message.answer("Ошибка: Неверный формат JSON. Попробуйте снова.")
    except Exception as e:
        logging.error(f"Ошибка при обновлении chat_settings.json: {e}")
        await message.answer(f"Ошибка при обновлении chat_settings.json: {e}")
    finally:
        await state.clear()

@router.callback_query(ChatCallbackData.filter(F.action == "remove_from_tracking"))
async def remove_from_tracking(callback: CallbackQuery, callback_data: ChatCallbackData):
    chat_id = callback_data.chat_id

    try:
        # Загружаем данные из файлов
        chat_list = load_chat_list()  # Убедитесь, что эта функция работает корректно
        chat_settings = load_chat_settings()

        # Удаляем чат из chat_list.json
        if chat_id in chat_list:
            del chat_list[chat_id]
            save_chat_list(chat_list)

        # Удаляем настройки чата из chat_settings.json
        if chat_id in chat_settings:
            del chat_settings[chat_id]
            save_chat_settings(chat_settings)

        # Уведомляем пользователя
        await callback.message.edit_text(f"Чат {chat_id} успешно удалён из отслеживаемых.")
    except Exception as e:
        logging.error(f"Ошибка при удалении чата {chat_id}: {e}")
        await callback.message.answer(f"Произошла ошибка: {e}")