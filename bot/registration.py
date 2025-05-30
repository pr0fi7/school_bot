import re

from telegram import Update, ReplyKeyboardRemove
from telegram.ext import ContextTypes, MessageHandler, filters, ConversationHandler
import datetime
from database.models import school_db

from .permissions import is_pupil, is_admin, is_teacher
from .keyboards import language_keyboard, registration_keyboard, cancel_button, language_buttons
from .admin import notify_all_admins

# Info for registration

NAME, SURNAME, LANGUAGE, BIRTHDAY = range(4)

config = school_db.get_config('languages')
all_langs =  [btn.text
                  for row in language_buttons
                  for btn in row]

# then build your regex from that
import re
pattern = r'^(?:' + '|'.join(map(re.escape, all_langs)) + r')$'

# valid_lang_texts = [f"{info['emoji']} {info['label']}" for info in all_langs.values()]
# pattern = r'^(' + '|'.join(map(re.escape, valid_lang_texts)) + r')$'

birthday_pattern = r'^\d{4}-\d{2}-\d{2}$'


# Connecting all buttons

async def show_registration_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Натисніть кнопку нижче, щоб розпочати реєстрацію:",
        reply_markup=registration_keyboard
    )


# Signing up one by one: from name to language

async def handle_start_registration(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if is_pupil(user_id) or is_admin(user_id) or is_teacher(user_id):
        return ConversationHandler.END

    text = update.message.text
    if text == "Зареєструватися як учень 📝":
        context.user_data['role'] = 'pupil'
        prompt = ("Вітаю! 👋\n"
                  "Скажіть, будь ласка, як Вас звати:")
    elif text == "Зареєструватися як вчитель 📝":
        context.user_data['role'] = 'teacher'
        prompt = ("Вітаю, вчителю! 👋\n"
                  "Скажіть, будь ласка, як Вас звати:")
    # elif text == "Зареєструватися як адміністратор 📝":
    #     context.user_data['role'] = 'admin'
    #     prompt = ("Вітаю, адміністратору! 👋\n"
    #     "Скажіть, будь ласка, як Вас звати:")

    await update.message.reply_text(prompt, reply_markup=cancel_button)
    return NAME


async def handle_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["name"] = update.message.text
    await update.message.reply_text(f"Чудово, {update.message.text}! 🙌\n"
                                    f"Тепер, будь ласка, введіть своє прізвище:",
                                    reply_markup=cancel_button)
    return SURNAME


async def handle_surname(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["surname"] = update.message.text
    role = context.user_data['role']

    if role == 'pupil':
        text = "Яку мову Ви мрієте опанувати? Обирай зі списку: ⬇️"
    elif role == 'teacher':
        text = "Яку мову Ви плануєте викладати? Обирай зі списку: ⬇️"
    # elif role == 'admin':
    #     name = context.user_data["name"]
    #     surname = context.user_data["surname"]
    #     user_id = update.effective_user.id

    #     school_db.insert_admin(user_id, name, surname, admin_username=name)
    #     await update.message.reply_text(
    #         "Вітаємо в команді! 🎉\n"
    #         "Ваша реєстрація завершена. Ви можете почати працювати з ботом.",
    #         reply_markup=ReplyKeyboardRemove()
    #     )
    #     return ConversationHandler.END

    await update.message.reply_text(text, reply_markup=language_keyboard)
    return LANGUAGE



async def handle_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    name = context.user_data["name"]
    surname = context.user_data["surname"]
    role = context.user_data["role"]
    language = update.message.text.rsplit(" ", 1)[0]


    if role == 'pupil':
        # 1) save without birthdate
        school_db.insert_pupil(user_id, name, surname, language)

        # 2) ask for the birthdate and move to BIRTHDAY
        await update.message.reply_text(
            "Чудово! 🙌\n"
            "Тепер, будь ласка, введіть свою дату народження у форматі YYYY-MM-DD\n"
            "Наприклад: 2000-01-01",
            reply_markup=cancel_button
        )
        return BIRTHDAY
    
    elif role == 'teacher':

        await update.message.reply_text(
            f"Дякуємо за реєстрацію, {name} {surname}!🎉\n"
            f"Очікуйте підтвердження протягом певного часу⏳",
            reply_markup=ReplyKeyboardRemove()
        )
        school_db.insert_teacher(user_id, name, surname, language)

        await notify_all_admins(
            bot=context.bot,
            name=name,
            surname=surname,
            role=role,
            language=language
        )

        return ConversationHandler.END

async def handle_birthday(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    try:
        birth_date = datetime.datetime.strptime(text, "%Y-%m-%d").date()
    except ValueError:
        return await handle_invalid_birthday(update, context)

    user_id = update.effective_user.id
    school_db.update_pupil_birthday(user_id, birth_date)

    await update.message.reply_text(
        "Реєстрація завершена! 🎉\n"
        f"Ми зберегли вашу дату народження: {birth_date}\n"
        "Очікуйте підтвердження.",
        reply_markup=ReplyKeyboardRemove()
    )
    await notify_all_admins(
        bot=context.bot,
        name=context.user_data["name"],
        surname=context.user_data["surname"],
        role='pupil',
        language=context.user_data.get("language")
    )
    return ConversationHandler.END

# Handlers for errors

async def handle_invalid_birthday(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Неправильний формат. Будь ласка, введіть у форматі YYYY-MM-DD",
        reply_markup=cancel_button
    )
    return BIRTHDAY

async def handle_timeout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Реєстрацію скасовано ❌",
        reply_markup=registration_keyboard
    )
    return ConversationHandler.END


async def handle_invalid_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Обери, будь ласка, одну з мов за допомогою кнопки ⚠️",
        reply_markup=language_keyboard
    )
    return LANGUAGE


def register_registration(application):
    conv = ConversationHandler(
        entry_points=[
            MessageHandler(filters.Text("Зареєструватися як учень 📝"), handle_start_registration),
            MessageHandler(filters.Text("Зареєструватися як вчитель 📝"), handle_start_registration),
            # MessageHandler(filters.Text("Зареєструватися як адміністратор 📝"), handle_start_registration),
        ],
        states={
            NAME: [
                MessageHandler(filters.Regex(r'^Відмінити ❌$'), handle_timeout),
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_name),
            ],
            SURNAME: [
                MessageHandler(filters.Regex(r'^Відмінити ❌$'), handle_timeout),
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_surname),
            ],
            LANGUAGE: [
                MessageHandler(filters.Regex(r'^Відмінити ❌$'), handle_timeout),
                MessageHandler(filters.Regex(pattern), handle_language),
                MessageHandler(filters.TEXT & ~filters.Regex(pattern), handle_invalid_language),
            ],
            BIRTHDAY: [
                MessageHandler(filters.Regex(r'^Відмінити ❌$'), handle_timeout),
                MessageHandler(filters.Regex(birthday_pattern), handle_birthday),
                MessageHandler(filters.TEXT & ~filters.Regex(birthday_pattern), handle_invalid_birthday),
            ]

        },
        fallbacks=[
            MessageHandler(filters.Text("Відмінити ❌"), handle_timeout)
        ],
        conversation_timeout=120
    )
    application.add_handler(conv)
