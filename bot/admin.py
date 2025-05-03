from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, CallbackQueryHandler, filters

from database.models import school_db

from .permissions import is_admin
from .messages import declined_request, new_student_notification, teacher_new_pupil_notification, \
    student_assigned_teacher_notification
from .keyboards import admin_keyboard, back_button


# Connecting all buttons

async def show_admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    if not is_admin(user.id):
        return

    await update.message.reply_text(
        text=f"Вітаємо Вас, {user.full_name}, на панелі керування!",
        reply_markup=admin_keyboard
    )


# Requests section

async def handle_requests(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pupils = school_db.get_all_pupils()
    conversations = school_db.get_all_conversations()

    waiting = [
        pupil
        for pupil in pupils
        if pupil["pupil_id"] not in {conv["pupil_id"] for conv in conversations}
    ]

    if not waiting:
        await update.message.reply_text("❌ Немає нових заявок.")
        return

    await update.message.reply_text(
        text=f"Для відміни перевірки заявок - натиснути кнопку Назад",
        reply_markup=back_button
    )

    context.user_data["admin_requests"] = waiting
    context.user_data["page_index"] = 0
    await send_request(update, context)


async def send_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    index = context.user_data["page_index"]
    queue = context.user_data["admin_requests"]
    pupil = queue[index]

    text = (
        f"📋 Заявка {index + 1}/{len(queue)}\n"
        f"👤 {pupil['pupil_name']} {pupil['pupil_surname']}\n"
        f"🌐 Мова: {pupil['languages_learning']}"
    )

    request_panel = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("«", callback_data="request_prev"),
            InlineKeyboardButton("»", callback_data="request_next"),
        ],
        [
            InlineKeyboardButton("Відхилити ❌", callback_data=f"request_decline_{pupil['pupil_id']}"),
            InlineKeyboardButton("Призначити ✅", callback_data=f"request_assign_{pupil['pupil_id']}")
        ]
    ])

    if update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=request_panel)
    else:
        await update.message.reply_text(text, reply_markup=request_panel)


async def handle_request_navigation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    action = query.data.split("_")[1]
    index = context.user_data["page_index"]
    total = len(context.user_data["admin_requests"])
    context.user_data["page_index"] = (
        (index - 1) % total if action == "prev"
        else
        (index + 1) % total
    )
    await send_request(update, context)


async def handle_request_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    parts = query.data.split("_")
    action, pupil_id = parts[1], int(parts[2])

    if action == "decline":
        pupil = school_db.get_pupil(pupil_id)

        school_db.delete_pupil(pupil_id)
        await query.edit_message_text("❌ Заявку відхилено.")

        name = pupil["pupil_name"]
        surname = pupil["pupil_surname"]
        text = declined_request(name, surname)

        await context.bot.send_message(
            chat_id=pupil_id,
            text=text
        )
        return

    requests = context.user_data["admin_requests"]
    index = context.user_data["page_index"]
    language = requests[index]["languages_learning"]

    teachers = [teacher for teacher in school_db.get_all_teachers()
                if language in teacher["languages_teaching"].split(",")]

    if not teachers:
        await query.edit_message_text("❌ Немає викладачів з такою мовою.")
        return

    context.user_data["pupil_id"] = pupil_id

    assign_panel = InlineKeyboardMarkup([
        [InlineKeyboardButton(f"{t['teacher_name']} {t['teacher_surname']}",
                              callback_data=f"assign_{t['teacher_id']}")]
        for t in teachers
    ])
    await query.edit_message_text("👋 Оберіть викладача:", reply_markup=assign_panel)


async def handle_assign_finish(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    teacher_id = int(query.data.split("_")[1])
    teacher = school_db.get_teacher(teacher_id)
    if not teacher:
        return await query.edit_message_text("❌ Помилка: викладач не знайдений.")

    pupil_id = context.user_data["pupil_id"]
    pupil = school_db.get_pupil(pupil_id)
    if not pupil:
        return await query.edit_message_text("❌ Помилка: учень не знайдений.")

    student_name = pupil["pupil_name"]
    student_surname = pupil["pupil_surname"]
    teacher_name = teacher["teacher_name"]
    teacher_surname = teacher["teacher_surname"]
    topic_name = f"{student_name} {student_surname}"

    topic = await context.bot.create_forum_topic(
        chat_id=teacher["group_id"],
        name=topic_name
    )
    branch_id = topic.message_thread_id

    school_db.insert_conversation(
        group_id=teacher["group_id"],
        branch_id=branch_id,
        teacher_id=teacher_id,
        pupil_id=pupil_id,
        conversation_data=[]
    )

    await query.edit_message_text("✅ Викладача призначено!")

    await context.bot.send_message(
        chat_id=teacher["group_id"],
        message_thread_id=branch_id,
        text=teacher_new_pupil_notification(student_name, student_surname)
    )

    await context.bot.send_message(
        chat_id=pupil["pupil_id"],
        text=student_assigned_teacher_notification(teacher_name, teacher_surname)
    )


# Support commands

async def notify_all_admins(bot, name: str, surname: str, language: str):
    admins = school_db.get_all_admins()
    for admin in admins:
        tg_id = admin.get("admin_id")
        if tg_id:
            text = new_student_notification(name, surname, language)
            await bot.send_message(chat_id=tg_id, text=text)


async def handle_admin_back(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.pop("admin_requests", None)
    context.user_data.pop("page_index", None)

    await update.message.reply_text(
        text="Дію відмінено",
        reply_markup=admin_keyboard
    )


def register_admin(application):
    application.add_handler(CommandHandler("admin", show_admin_panel))

    application.add_handler(MessageHandler(filters.Text("Заявки учнів 📜"), handle_requests))
    application.add_handler(MessageHandler(filters.Text("Назад ◀️"), handle_admin_back))

    application.add_handler(CallbackQueryHandler(handle_request_navigation, pattern=r"^request_(prev|next)$"))
    application.add_handler(CallbackQueryHandler(handle_request_action, pattern=r"^request_(decline|assign)_\d+$"))
    application.add_handler(CallbackQueryHandler(handle_assign_finish,
                                                 pattern=r"^assign_\d+$"))

    application.bot_data["notify_all_admins"] = notify_all_admins
