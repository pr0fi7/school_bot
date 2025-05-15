from bot import build_application
from config.settings import db_params
from database.models import Database
import os 
from dotenv import load_dotenv
load_dotenv()
ADMIN_ID_LIST = int(os.getenv("ADMIN_ID"))

if __name__ == "__main__":
    app = build_application()
    school_db = Database(db_params)
    #populate_admins
    for admin_id in ADMIN_ID_LIST:
        school_db.insert_admin(
            admin_id=admin_id,
            admin_name="Admin",
            admin_surname="Admin",
            admin_username="Admin",
        )
    print("Bot works...")
    app.run_polling()
