from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, CallbackQueryHandler, filters

from create_group import create_group
from database.models import school_db

from .permissions import is_admin
from .messages import declined_request, new_student_notification, teacher_new_pupil_notification, \
    student_assigned_teacher_notification, new_teacher_notification
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


# Requests section for pupils

async def handle_requests(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pupils = school_db.get_all_pupils()
    conversations = school_db.get_all_conversations()

    waiting = [
        pupil
        for pupil in pupils
        if pupil["pupil_id"] not in {conv["pupil_id"] for conv in conversations}
    ]

    if not waiting:
        await update.message.reply_text("Немає нових заявок ❌")
        return

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
        [InlineKeyboardButton("◀️ Назад", callback_data="request_prev"),
         InlineKeyboardButton("Далі ▶️", callback_data="request_next")],
        [InlineKeyboardButton("Відхилити ❌", callback_data=f"request_decline_{pupil['pupil_id']}"),
         InlineKeyboardButton("Призначити ✅", callback_data=f"request_assign_{pupil['pupil_id']}")]
    ])

    if update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=request_panel)
        await update.message.reply_text(
            text=f"Щоб повернутися до панелі, натисніть кнопку нижче 🔽",
            reply_markup=back_button
        )
    else:
        await update.message.reply_text(text, reply_markup=request_panel)
        await update.message.reply_text(
            text=f"Щоб повернутися до панелі, натисніть кнопку нижче 🔽",
            reply_markup=back_button
        )


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
    if not query:
        return
    await query.answer()

    parts = query.data.split("_")
    action, pupil_id = parts[1], int(parts[2])

    if action == "decline":
        pupil = school_db.get_pupil(pupil_id)

        school_db.delete_pupil(pupil_id)
        await query.edit_message_text("Заявку відхилено ❌")

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

    teachers = [
        teacher
        for teacher in school_db.get_all_teachers()
        if language in teacher["languages_teaching"].split(",")
           and teacher.get("group_id", 0) < 0
    ]
    if not teachers:
        await query.edit_message_text("Немає викладачів з такою мовою ❌")
        return

    context.user_data["assign_state_teachers"] = teachers

    context.user_data["pupil_id"] = pupil_id

    buttons = []
    for teacher in teachers:
        num = teacher["number"]
        label = f"{num}) {teacher['teacher_name']} {teacher['teacher_surname']}"
        buttons.append([
            InlineKeyboardButton(
                label,
                callback_data=f"assign_{teacher['teacher_id']}_{pupil_id}"
            )
        ])

    assign_panel = InlineKeyboardMarkup(buttons)
    await query.edit_message_text("Список викладачів (введіть номер або натисніть кнопку): 🔎",
                                  reply_markup=assign_panel)


async def handle_assign_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    teachers = context.user_data.get("assign_state_teachers")
    if not teachers:
        return

    # Check teacher by number

    text = update.message.text.strip()
    if text.isdigit():
        num = int(text)
        teacher = next((teacher for teacher in teachers if teacher["number"] == num), None)
        if teacher:
            await handle_assign_teacher(update, context)
            return

    # Check teacher by two words

    parts = text.split()

    if len(parts) == 2:
        name, surname = parts
        teacher = next(
            (teacher for teacher in teachers
             if teacher["teacher_name"].lower() == name.lower()
             and teacher["teacher_surname"].lower() == surname.lower()),
            None
        )
        if teacher:
            await handle_assign_teacher(update, context)
            return

    # Check teacher by one word (name or surname)

    term = parts[0].lower()
    filtered = [
        t for t in teachers
        if term in t["teacher_name"].lower() or term in t["teacher_surname"].lower()
    ]

    to_show = filtered if filtered else teachers

    buttons = [
        [InlineKeyboardButton(f"{teacher['number']}) {teacher['teacher_name']} {teacher['teacher_surname']}",
                              callback_data=f"assign_{teacher['teacher_id']}")]
        for teacher in to_show
    ]
    panel = InlineKeyboardMarkup(buttons)
    await update.message.reply_text(
        "Список викладачів (введіть номер або натисніть кнопку): 🔎",
        reply_markup=panel
    )


async def handle_assign_teacher(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query:
        await query.answer()

        await query.edit_message_text(
            "Викладача призначено! ✅"
        )

        await query.message.reply_text(
            "Повернення до адміністраторської панелі... 🔃",
            reply_markup=admin_keyboard
        )

        teacher_id = int(query.data.split("_")[1])
        teacher = school_db.get_teacher(teacher_id)
        if not teacher:
            return await query.edit_message_text("Викладач не знайдений ❌")

        pupil_id = context.user_data["pupil_id"]
        pupil = school_db.get_pupil(pupil_id)
        if not pupil:
            return await query.edit_message_text("Учень не знайдений ❌")

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

        await context.bot.send_message(
            chat_id=teacher["group_id"],
            message_thread_id=branch_id,
            text=teacher_new_pupil_notification(student_name, student_surname)
        )

        await context.bot.send_message(
            chat_id=pupil_id,
            text=student_assigned_teacher_notification(teacher_name, teacher_surname)
        )

    else:
        await query.edit_message_text("Невідома помилка ❌",
                                      reply_markup=admin_keyboard)

    for key in ("assign_state_teachers", "pupil_id", "admin_requests", "page_index"):
        context.user_data.pop(key, None)


# Requests section for teacher

async def handle_teacher_requests(update: Update, context: ContextTypes.DEFAULT_TYPE):
    teachers = school_db.get_all_teachers()
    pending = [t for t in teachers if t['group_id'] > 0]
    if not pending:
        return await update.message.reply_text("Немає нових заявок від викладачів ❌", reply_markup=back_button)

    context.user_data['admin_teacher_requests'] = pending
    context.user_data['teacher_page_index'] = 0
    await send_teacher_request(update, context)


async def send_teacher_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    index = context.user_data['teacher_page_index']
    queue = context.user_data['admin_teacher_requests']
    teacher = queue[index]
    text = (
        f"📋 Заявка вчителя {index + 1}/{len(queue)}\n"
        f"👤 {teacher['teacher_name']} {teacher['teacher_surname']}\n"
        f"🌐 Мова викладання: {teacher['languages_teaching']}"
    )
    panel = InlineKeyboardMarkup([
        [InlineKeyboardButton("◀️ Назад", callback_data="teacher_prev"),
         InlineKeyboardButton("Далі ▶️", callback_data="teacher_next")],
        [InlineKeyboardButton("Відхилити ❌", callback_data=f"teacher_decline_{teacher['teacher_id']}"),
         InlineKeyboardButton("Підтвердити ✅", callback_data=f"teacher_confirm_{teacher['teacher_id']}")]
    ])
    if update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=panel)
    else:
        await update.message.reply_text(
            text=f"Щоб повернутися до панелі, натисніть кнопку нижче 🔽",
            reply_markup=back_button
        )
        await update.message.reply_text(text, reply_markup=panel)


async def handle_teacher_navigation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    action = query.data.split('_')[1]
    total = len(context.user_data['admin_teacher_requests'])
    index = context.user_data['teacher_page_index']
    if action == 'prev':
        index = (index - 1) % total
    else:
        index = (index + 1) % total
    context.user_data['teacher_page_index'] = index
    await send_teacher_request(update, context)


async def handle_teacher_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    _, action, tid = query.data.split('_')
    teacher_id = int(tid)
    teacher = school_db.get_teacher(teacher_id)

    if action == "decline":
        await query.edit_message_text("Заявку викладача відхилено ❌")

        name = teacher["teacher_name"]
        surname = teacher["teacher_surname"]
        text = declined_request(name, surname)

        school_db.delete_teacher(teacher_id)

        await context.bot.send_message(
            chat_id=teacher_id,
            text=text
        )
        return

    title = f"{teacher['teacher_name']} {teacher['teacher_surname']} — {teacher['languages_teaching']}"
    bot_username = f"@{context.bot.username}"

    context.application.create_task(
        create_group(title, bot_username, teacher_id, teacher['languages_teaching'])
    )
    await query.edit_message_text("Заявку викладача підтверджено ✅")

    for key in ('admin_teacher_requests', 'teacher_page_index'):
        context.user_data.pop(key, None)


# Additional handlers

async def handle_admin_back(update: Update, context: ContextTypes.DEFAULT_TYPE):
    for key in (
            "assign_state_teachers", "admin_teacher_requests", "teacher_page_index", "pupil_id", "teacher_id",
            "admin_requests",
            "page_index"):
        context.user_data.pop(key, None)

    await update.message.reply_text(
        text="Дію відмінено ❌",
        reply_markup=admin_keyboard
    )


async def notify_all_admins(bot, name: str, surname: str, role: str, language: str):
    admins = school_db.get_all_admins()
    for admin in admins:
        tg_id = admin.get("admin_id")
        if tg_id:
            if role == "pupil":
                text = new_student_notification(name, surname, language)
                await bot.send_message(
                    chat_id=tg_id,
                    text=text,
                    reply_markup=admin_keyboard
                )
            else:
                text = new_teacher_notification(name, surname, language)
                await bot.send_message(
                    chat_id=tg_id,
                    text=text,
                    reply_markup=admin_keyboard
                )


def register_admin(application):
    application.add_handler(CommandHandler("admin", show_admin_panel))

    application.add_handler(MessageHandler(filters.Text("Заявки учнів 📜"), handle_requests))
    application.add_handler(MessageHandler(filters.Text("Заявки викладачів 📜"), handle_teacher_requests))
    application.add_handler(MessageHandler(filters.Text("◀️ Назад"), handle_admin_back))

    application.add_handler(CallbackQueryHandler(handle_request_navigation, pattern=r"^request_(prev|next)$"))
    application.add_handler(CallbackQueryHandler(handle_request_action, pattern=r"^request_(decline|assign)_\d+$"))

    application.add_handler(CallbackQueryHandler(handle_teacher_navigation, pattern=r"^teacher_(prev|next)$"))
    application.add_handler(CallbackQueryHandler(handle_teacher_action, pattern=r"^teacher_(decline|confirm)_\d+$"))

    application.add_handler(
        CallbackQueryHandler(handle_assign_teacher, pattern=r"^assign_\d+(_\d+)?$")
    )

    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND,
                                           handle_assign_text))

    application.bot_data["notify_all_admins"] = notify_all_admins
