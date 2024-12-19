import json
import os

SETTINGS_FILE = "bot/utils/chat_settings.json"
CHATS_FILE = "bot/utils/chat_list.json"

def load_json(file_path):
    """Загружает данные из JSON-файла. Если файла нет, создаёт пустой."""
    if not os.path.exists(file_path):
        save_json(file_path, {})
    with open(file_path, "r", encoding="utf-8") as file:
        try:
            return json.load(file)
        except json.JSONDecodeError:
            print(f"Ошибка загрузки JSON из {file_path}. Возвращён пустой словарь.")
            return {}

def save_json(file_path, data):
    """Сохраняет данные в JSON-файл."""
    with open(file_path, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=4, ensure_ascii=False)

def load_chat_list():
    """Загружает список чатов."""
    return load_json(CHATS_FILE)

def save_chat_list(data):
    """Сохраняет список чатов."""
    save_json(CHATS_FILE, data)

def load_chat_settings():
    """Загружает настройки чатов."""
    return load_json(SETTINGS_FILE)

def save_chat_settings(data):
    """Сохраняет настройки чатов."""
    save_json(SETTINGS_FILE, data)