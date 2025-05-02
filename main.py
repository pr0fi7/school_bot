from bot import build_application
from config.settings import db_params
from database.models import Database

if __name__ == "__main__":
    app = build_application()
    school_db = Database(db_params)
    print("Bot works...")
    app.run_polling()
