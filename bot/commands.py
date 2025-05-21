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
        return await show_admin_panel(update, context)

    if is_teacher(user.id):
        return await show_teacher_panel(update, context)

    await update.message.reply_text(welcome_message(user.first_name))

    # Pass the DB connection in here (or access it inside is_pupil)
    if is_pupil(user.id):
        return await show_pupil_panel(update, context)

    # Otherwise they truly aren’t registered yet
    return await show_registration_panel(update, context)



def register_commands(application):
    application.add_handler(CommandHandler("start", start))
