import os
from dotenv import load_dotenv

from telegram.ext import ApplicationBuilder

# Turning on all functions of bot
from .commands import register_commands
from .handlers import register_handlers
from .messages import register_messages
from .monitor import register_monitor
from .permissions import register_permissions
from .registration import register_registration
from .utils import register_utils

load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")


def build_application():
    application = ApplicationBuilder().token(TOKEN).build()

    register_commands(application)
    register_handlers(application)
    register_messages(application)
    register_monitor(application)
    register_permissions(application)
    register_registration(application)
    register_utils(application)

    return application
