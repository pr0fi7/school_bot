from telegram import Update
from telegram.ext import MessageHandler, filters, CallbackContext


async def student_chat(update: Update, context: CallbackContext):
    user = update.effective_user

async def teacher_chat(update: Update, context: CallbackContext):
    user = update.effective_user

async def register_conversation(application):
    application.add_handler(MessageHandler(filters.ChatType.GROUP | filters.ChatType.SUPERGROUP & ~filters.COMMAND), student_chat)
