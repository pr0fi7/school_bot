from telegram import KeyboardButton, ReplyKeyboardMarkup

from database.models import school_db

# Shared single buttons

cancel_button = ReplyKeyboardMarkup(
    [[KeyboardButton("Відмінити ❌")]],
    resize_keyboard=True,
)

back_button = ReplyKeyboardMarkup(
    [[KeyboardButton("◀️ Назад")]],
    resize_keyboard=True,
)

# ONLY FOR LANGUAGES

# config = school_db.get_config('languages')
# all_langs = config.get('languages', {})
# row_size = 2
# language_buttons = []
# row = []

# for lang_code, info in all_langs.items():
#     text = f"{info['label']} {info['emoji']}"
#     row.append(KeyboardButton(text))

#     if len(row) == row_size:
#         language_buttons.append(row)
#         row = []

# if row:
#     language_buttons.append(row)

language_buttons = [
    [KeyboardButton("🇬🇧 Англійська")],
    [KeyboardButton("🇺🇸 Американська англійська")],
    [KeyboardButton("🇵🇱 Польська")],
    [KeyboardButton("🇸🇰 Словацька")],
    [KeyboardButton("🇨🇿 Чеська")],
    [KeyboardButton("🇩🇪 Німецька")],
    [KeyboardButton("🇫🇷 Французька")],
    [KeyboardButton("🇪🇸 Іспанська")],
    [KeyboardButton("🇮🇹 Італійська")],
]
language_keyboard = ReplyKeyboardMarkup(language_buttons, resize_keyboard=True)


# All other keyboards

registration_buttons = [
    [KeyboardButton("Зареєструватися як учень 📝")],
    [KeyboardButton("Зареєструватися як вчитель 📝")],
    # [KeyboardButton("Зареєструватися як адміністратор 📝")],
    [KeyboardButton("Написати адміністратору 👩‍💼")]
]
registration_keyboard = ReplyKeyboardMarkup(registration_buttons, resize_keyboard=True)

admin_panel = [
    [KeyboardButton("Заявки учнів 📜"), KeyboardButton("Заявки викладачів 📜")],
    [KeyboardButton("Знайти чат 🔎"), KeyboardButton("Запити 📜")],
    [KeyboardButton("Повідомити усіх вчителів 🔔"), KeyboardButton("Повідомити усіх учнів 🔔")],
    [KeyboardButton("Керувати призначеннями ⚙️") ]


]
admin_keyboard = ReplyKeyboardMarkup(admin_panel, resize_keyboard=True)

teacher_buttons = [
    # [KeyboardButton("Повідомити моїх учнів 🔔")],
    [KeyboardButton("Написати адміністратору 👩‍💼")]
]
teacher_keyboard = ReplyKeyboardMarkup(teacher_buttons, resize_keyboard=True)

pupil_buttons = [
    [KeyboardButton("Написати викладачеві 👨‍🏫")],
    [KeyboardButton("Написати адміністратору 👩‍💼")]
]
pupil_keyboard = ReplyKeyboardMarkup(pupil_buttons, resize_keyboard=True)

# After teacher broadcast:
delete_teachers_kb = ReplyKeyboardMarkup(
    [[ KeyboardButton("Видалити сповіщення вчителям") ]],
    one_time_keyboard=True,
    resize_keyboard=True
)

# After pupil broadcast:
delete_pupils_kb = ReplyKeyboardMarkup(
    [[ KeyboardButton("Видалити сповіщення учням") ]],
    one_time_keyboard=True,
    resize_keyboard=True
)