import logging
import asyncio
import json
import os
from datetime import datetime, time as dt_time
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from bot.config import load_config
from bot.handlers import commands, messages, chat_events

# Загрузка конфигурации
config = load_config()
BOT_TOKEN = config["token"]

# Пути к JSON-файлам
JSON_FILES = ["chat_list.json", "chat_settings.json"]

# ID чата для отправки резервного копирования
BACKUP_CHAT_ID = config.get("backup_chat_id")  # Добавьте этот параметр в конфигурацию

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

# Асинхронная функция для резервного копирования
async def backup_and_send():
    while True:
        now = datetime.now()
        target_time = dt_time(hour=23, minute=59)  # Время запуска задачи
        target_datetime = datetime.combine(now.date(), target_time)

        # Если текущее время уже прошло целевое, установите на следующий день
        if now.time() > target_time:
            target_datetime = target_datetime.replace(day=now.day + 1)

        # Рассчитать, сколько ждать до следующего запуска
        wait_time = (target_datetime - now).total_seconds()
        logging.info(f"Резервное копирование начнется через {wait_time} секунд.")
        await asyncio.sleep(wait_time)

        # Выполнение резервного копирования
        try:
            current_time = datetime.now().strftime("%H:%M")
            date = datetime.now().strftime("%d.%m.%Y")
            message = f"Время на часах: {current_time}\nСообщение:\n**Резервное копирование данных за {date}**\n"

            for file_name in JSON_FILES:
                if os.path.exists(file_name):
                    with open(file_name, "r", encoding="utf-8") as f:
                        content = json.dumps(json.load(f), ensure_ascii=False, indent=4)
                    message += f"\n{file_name}\n```\n{content}\n```\n"
                else:
                    message += f"\n{file_name} не найден.\n"

            await bot.send_message(chat_id=BACKUP_CHAT_ID, text=message, parse_mode="Markdown")
            logging.info("Резервное копирование успешно выполнено и отправлено.")
        except Exception as e:
            logging.error(f"Ошибка при резервном копировании: {e}")

async def main():
    logging.info("Бот запускается...")

    # Создание задачи для резервного копирования
    asyncio.create_task(backup_and_send())

    try:
        await dp.start_polling(bot)
    except Exception as e:
        logging.error(f"Ошибка запуска бота: {e}")

if __name__ == "__main__":
    asyncio.run(main())