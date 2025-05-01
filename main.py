import logging

from bot import build_application
from config.settings import db_params
from database.models import Database

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    handlers=[
        logging.FileHandler("logs/bot_log.txt", encoding="utf-8"),
        logging.StreamHandler()
    ]
)

if __name__ == "__main__":
    app = build_application()
    school_db = Database(db_params)
    app.run_polling()
