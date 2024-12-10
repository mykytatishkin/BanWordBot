import logging
import asyncio
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from bot.config import load_config
from bot.handlers import commands, messages, chat_events

# Загрузка конфигурации
config = load_config()
BOT_TOKEN = config["token"]

# Инициализация бота и диспетчера
bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# Регистрация обработчиков
dp.include_router(commands.router)
dp.include_router(messages.router)
dp.include_router(chat_events.router)

# Логирование
logging.basicConfig(level=logging.INFO)

async def main():
    logging.info("Бот запускается...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())