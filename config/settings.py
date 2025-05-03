import json
import os

from dotenv import load_dotenv

load_dotenv()

# Load environment variables from .env file for the db connection
db_params = {
    "dbname": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "host": os.getenv("DB_HOST"),
    "port": os.getenv("DB_PORT"),
}

# get trigger words from JSON file
with open("config/trigger_words.json", "r", encoding="utf-8") as file:
    trigger_words = file.read()
    trigger_words = json.loads(trigger_words)
    trigger_words_list = trigger_words["trigger_words"]