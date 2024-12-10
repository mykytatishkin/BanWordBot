from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def main_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="Список чатов"),
                KeyboardButton(text="Добавить ключевое слово"),
                KeyboardButton(text="Удалить ключевое слово"),
            ],
            [KeyboardButton(text="Список ключевых слов")],
        ],
        resize_keyboard=True
    )