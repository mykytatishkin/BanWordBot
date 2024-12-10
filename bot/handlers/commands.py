from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command
from bot.keyboards.main_menu import main_menu

router = Router()

@router.message(Command("start"))
async def handle_start(message: Message):
    await message.answer(
        text="Привет! Я помогу вам настроить автоматическую модерацию чатов. Используйте кнопки ниже для взаимодействия.",
        reply_markup=main_menu()
    )