from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def main_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="Список чатов"),
                KeyboardButton(text="Моментальное резервное копирование"),
            ],
            [
                KeyboardButton(text="Импорт настроек для chat_list.json"),
                KeyboardButton(text="Импорт настроек для chat_settings.json"),
            ],
        ],
        resize_keyboard=True
    )