from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters.callback_data import CallbackData
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from bot.utils.file_utils import load_chat_list, load_chat_settings, save_chat_settings
import logging

logging.basicConfig(level=logging.INFO)
router = Router()
storage = MemoryStorage()  # Используем FSM Storage

chat_list = load_chat_list()
chat_settings = load_chat_settings()

# Определяем состояние для FSM
class AddKeywordStates(StatesGroup):
    waiting_for_keyword = State()
    waiting_for_keyword_removal = State()

# CallbackData для обработки выбора чата и настроек
class ChatCallbackData(CallbackData, prefix="chat"):
    chat_id: str
    action: str

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
        InlineKeyboardButton(text="Добавить ключевое слово", callback_data=ChatCallbackData(chat_id=chat_id, action="add_keyword").pack()),
        InlineKeyboardButton(text="Удалить ключевое слово", callback_data=ChatCallbackData(chat_id=chat_id, action="remove_keyword").pack()),
        InlineKeyboardButton(text="Список ключевых слов", callback_data=ChatCallbackData(chat_id=chat_id, action="list_keywords").pack()),
    ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=[buttons])
    await callback.message.edit_text(f"Вы выбрали чат {chat_id}. Выберите действие:", reply_markup=keyboard)

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