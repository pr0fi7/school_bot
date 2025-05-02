import os
from dotenv import load_dotenv

from telegram.ext import ApplicationBuilder

# Turning on all functions of bot
from .registration import register_registration
from .commands import register_commands
from .admin import register_admin

load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")


def build_application():
    application = ApplicationBuilder().token(TOKEN).build()

    register_commands(application)
    register_registration(application)
    register_admin(application)

    return application
