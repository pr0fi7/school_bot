from telegram import Update
from telegram.ext import MessageHandler, filters, CallbackContext, ContextTypes

from bot.keyboards import pupil_keyboard
from bot.permissions import is_pupil, is_teacher


# Connecting all buttons

async def show_pupil_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    if is_pupil(user.id):
        await update.message.reply_text(
            "Оберіть опцію нижче, з ким ви хочете зв'язатися",
            reply_markup=pupil_keyboard
        )


async def show_teacher_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    if not is_teacher(user.id):
        await update.message.reply_text(
            "Оберіть опцію нижче, з ким ви хочете зв'язатися",
            reply_markup=pupil_keyboard
        )


# All conversations

async def student_to_teacher_chat(update: Update, context: CallbackContext):
    user = update.effective_user


async def student_to_admin_chat(update: Update, context: CallbackContext):
    user = update.effective_user


async def teacher_to_student_chat(update: Update, context: CallbackContext):
    user = update.effective_user


async def admin_to_student_chat(update: Update, context: CallbackContext):
    user = update.effective_user


# All notifications


# All mass mailing


def register_conversation(application):
    return
