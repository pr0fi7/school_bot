from telegram import KeyboardButton, ReplyKeyboardMarkup

registration_buttons = [
    [KeyboardButton("Зареєструватися 📝")],
    [KeyboardButton("Адміністратор 👩‍💼")],
    [KeyboardButton("Відмінити ❌")]
]
registration_keyboard = ReplyKeyboardMarkup(registration_buttons, resize_keyboard=True)

language_buttons = [
    [KeyboardButton("Англійська 🇬🇧"), KeyboardButton("Чеська 🇨🇿")],
    [KeyboardButton("Словацька 🇸🇰"), KeyboardButton("Іспанська 🇪🇸")],
    [KeyboardButton("Італійська 🇮🇹"), KeyboardButton("Німецька 🇩🇪")],
    [KeyboardButton("Французька 🇫🇷")],
]
language_keyboard = ReplyKeyboardMarkup(language_buttons, resize_keyboard=True)

admin_panel = [
    [KeyboardButton("Заявки учнів📜")],
    [KeyboardButton("Додати викладача ✅"), KeyboardButton("Видалити викладача ❌")],
    [KeyboardButton("Список учнів 🧑‍🎓"), KeyboardButton("Список викладачів 👨‍🏫")],
    [KeyboardButton("Назад")]
]
admin_keyboard = ReplyKeyboardMarkup(admin_panel, resize_keyboard=True)

conversation_buttons = [
    [KeyboardButton("Викладач 👨‍🏫")],
    [KeyboardButton("Адміністратор 👩‍💼")]
]
conversation_keyboard = ReplyKeyboardMarkup(conversation_buttons, resize_keyboard=True)

back_button = ReplyKeyboardMarkup(
    [[KeyboardButton("Назад")]],
    resize_keyboard=True,
)
