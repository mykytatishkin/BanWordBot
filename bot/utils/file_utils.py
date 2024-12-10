import json

SETTINGS_FILE = "chat_settings.json"
CHATS_FILE = "chat_list.json"

def load_chat_settings():
    try:
        with open(SETTINGS_FILE, "r") as settings_file:
            return json.load(settings_file)
    except FileNotFoundError:
        return {}

def save_chat_settings(chat_settings):
    with open(SETTINGS_FILE, "w") as settings_file:
        json.dump(chat_settings, settings_file, indent=4)

def load_chat_list():
    try:
        with open(CHATS_FILE, "r") as chats_file:
            return json.load(chats_file)
    except FileNotFoundError:
        return {}

def save_chat_list(chat_list):
    with open(CHATS_FILE, "w") as chats_file:
        json.dump(chat_list, chats_file, indent=4)