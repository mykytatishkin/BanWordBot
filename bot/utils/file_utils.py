import json

SETTINGS_FILE = "chat_settings.json"
CHATS_FILE = "chat_list.json"

def load_chat_settings():
    try:
        with open(SETTINGS_FILE, "r", encoding="utf-8") as file:
            return json.load(file)
    except FileNotFoundError:
        return {}
    except json.JSONDecodeError:
        return {}

def save_chat_settings(data):
    with open(SETTINGS_FILE, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=4, ensure_ascii=False)
def load_chat_list():
    try:
        with open(CHATS_FILE, "r") as chats_file:
            return json.load(chats_file)
    except FileNotFoundError:
        return {}

def save_chat_list(chat_list):
    with open(CHATS_FILE, "w") as chats_file:
        json.dump(chat_list, chats_file, indent=4)

