from telegram import Update
from telegram.ext import ContextTypes, CommandHandler

from .admin import show_admin_panel
from .conversation import show_pupil_panel, show_teacher_panel
from .messages import welcome_message
from .permissions import is_pupil, is_admin, is_teacher
from .registration import show_registration_panel


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.chat.type != "private":
        return

    user = update.effective_user

    if is_admin(user.id):
        await show_admin_panel(update, context)
        return

    elif is_teacher(user.id):
        await show_teacher_panel(update, context)
        return

    await update.message.reply_text(welcome_message(user.first_name))

    if is_pupil(user.id):
        await show_pupil_panel(update, context)
        return

    else:
        await show_registration_panel(update, context)
        return


def register_commands(application):
    application.add_handler(CommandHandler("start", start))
