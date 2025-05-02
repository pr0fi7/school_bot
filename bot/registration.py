from telegram import Update, ReplyKeyboardRemove
from telegram.ext import ContextTypes, MessageHandler, filters, ConversationHandler

from database.models import school_db

from .permissions import is_pupil, is_admin, is_teacher
from .handlers import language_keyboard, registration_keyboard
from .admin import notify_all_admins

NAME, SURNAME, LANGUAGE = range(3)


# Connecting all buttons

async def show_registration_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Натисніть кнопку нижче, щоб розпочати реєстрацію:",
        reply_markup=registration_keyboard
    )


async def show_language_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Оберіть мову, що плануєте вивчати",
        reply_markup=language_keyboard
    )


# Signing up one by one: from name to language

async def handle_start_registration(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if is_pupil(user_id) or is_admin(user_id) or is_teacher(user_id):
        return ConversationHandler.END

    await update.message.reply_text("Введіть, будь ласка, ім’я:", reply_markup=ReplyKeyboardRemove())
    return NAME


async def handle_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["name"] = update.message.text
    await update.message.reply_text("Введіть, будь ласка, прізвище:")
    return SURNAME


async def handle_surname(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["surname"] = update.message.text
    await show_language_panel(update, context)
    return LANGUAGE


async def handle_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["language"] = update.message.text.rsplit(" ", 1)[0]
    user_id = update.effective_user.id
    name = context.user_data["name"]
    surname = context.user_data["surname"]
    language = context.user_data["language"]
    await update.message.reply_text(f"✅ Дякуємо, {name} {surname}!\nМова: {language}.\nОчікуйте підтвердження.",
                                    reply_markup=ReplyKeyboardRemove())

    await notify_all_admins(
        bot=context.bot,
        name=name,
        surname=surname,
        language=language
    )

    school_db.insert_pupil(user_id, name, surname, language)

    return ConversationHandler.END


async def handle_timeout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Відміна реєстрації.",
                                    reply_markup=registration_keyboard)
    return ConversationHandler.END


def register_registration(application):
    conv = ConversationHandler(
        entry_points=[
            MessageHandler(filters.Text("Зареєструватися 📝"), handle_start_registration)
        ],
        states={
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_name),
                   MessageHandler(filters.Text("Відмінити ❌"), handle_timeout)],
            SURNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_surname),
                      MessageHandler(filters.Text("Відмінити ❌"), handle_timeout)],
            LANGUAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_language),
                       MessageHandler(filters.Text("Відмінити ❌"), handle_timeout)],
        },
        fallbacks=[
            MessageHandler(filters.Text("Відмінити ❌"), handle_timeout)
        ],
        conversation_timeout=120
    )
    application.add_handler(conv)
