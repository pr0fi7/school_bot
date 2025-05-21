from bot import build_application
from config.settings import db_params
from database.models import Database
import os 
from dotenv import load_dotenv
import ast
load_dotenv()
ADMIN_ID_LIST = ast.literal_eval(os.getenv("ADMIN_ID_LIST"))

if __name__ == "__main__":
    app = build_application()
    school_db = Database(db_params)
    #populate_admins
    counter = 0 
    for admin_id in ADMIN_ID_LIST:
        if school_db.get_admin(admin_id):
            print(f"Admin with ID {admin_id} already exists.")
            continue
        counter += 1
        school_db.insert_admin(
            
            admin_id=admin_id,
            admin_name="Admin_" + str(counter),
            admin_surname="Admin_" + str(counter),
            admin_username="Admin_" + str(counter),
        )
    print("Bot works...")
    app.run_polling()
