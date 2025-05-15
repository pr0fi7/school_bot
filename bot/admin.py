from datetime import datetime

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, CallbackQueryHandler, filters

from create_group import create_group
from database.models import school_db

from .permissions import is_admin
from .messages import declined_request, new_student_notification, teacher_new_pupil_notification, \
    student_assigned_teacher_notification, new_teacher_notification
from .keyboards import admin_keyboard, back_button, pupil_keyboard
import aiogram
from aiogram.methods.delete_forum_topic import DeleteForumTopic



# Connecting all buttons


async def show_admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    if not is_admin(user.id):
        return

    await update.message.reply_text(
        text=f"Вітаємо Вас, {user.full_name}, на панелі керування!",
        reply_markup=admin_keyboard
    )


# Request section for pupils

async def handle_pupil_requests(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
    await send_pupil_request(update, context)


async def send_pupil_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    index = context.user_data["page_index"]
    queue = context.user_data["admin_requests"]
    pupil = queue[index]

    text = (
        f"Заявка {index + 1}/{len(queue)} 📋\n"
        f"{pupil['pupil_name']} {pupil['pupil_surname']} 👤\n"
        f"Мова: {pupil['languages_learning']} 🌐"
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


async def handle_pupil_request_navigation(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
    await send_pupil_request(update, context)


async def handle_pupil_request_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
            text=student_assigned_teacher_notification(teacher_name, teacher_surname),
            reply_markup=pupil_keyboard
        )

    else:
        await query.edit_message_text("Невідома помилка ❌",
                                      reply_markup=admin_keyboard)

    for key in ("assign_state_teachers", "pupil_id", "admin_requests", "page_index"):
        context.user_data.pop(key, None)


async def open_assignment_manager(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    # fetch all active pupil–teacher links
    convos = school_db.get_all_conversations()
    if not convos:
        return await update.message.reply_text(
            "Наразі немає жодного призначення.",
            reply_markup=admin_keyboard
        )

    for c in convos:
        teacher = school_db.get_teacher(c["teacher_id"])
        pupil   = school_db.get_pupil(c["pupil_id"])
        label = f"{pupil['pupil_name']} {pupil['pupil_surname']} → " \
                f"{teacher['teacher_name']} {teacher['teacher_surname']}"

        buttons = [
            InlineKeyboardButton(
                "Зняти призначення ❌",
                callback_data=f"clear_{teacher['teacher_id']}_{pupil['pupil_id']}"
            )
        ]
        kb = InlineKeyboardMarkup([buttons])
        await update.message.reply_text(label, reply_markup=kb)


async def handle_clear_assignment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    # parse “clear_<teacher_id>_<pupil_id>`
    _, raw_tid, raw_pid = query.data.split("_")
    teacher_id = int(raw_tid)
    pupil_id   = int(raw_pid)

    # — look up the DB record —
    conv = school_db.get_conversation_by_teacher_and_pupil(teacher_id, pupil_id)
    if not conv:
        return await query.edit_message_text(
            "❗️ Це призначення вже скасовано.",
            reply_markup=admin_keyboard
        )

    # — delete the link —
    school_db.delete_conversation(conv["conversation_id"])

    # — remove the topic —
    bot = aiogram.Bot(token=context.bot.token)
    await bot(DeleteForumTopic(chat_id=conv["group_id"],
                                message_thread_id=conv["branch_id"]))

    # remove inline buttons on the _same_ message:
    await query.edit_message_text(
        "Призначення успішно знято ❌",
        reply_markup=None
    )
    # then send your normal admin keyboard fresh:
    await context.bot.send_message(
        chat_id=update.effective_user.id,
        text="Оберіть дію:",
        reply_markup=admin_keyboard
    )


    # — notify both sides —
    teacher = school_db.get_teacher(teacher_id)
    pupil   = school_db.get_pupil(pupil_id)

    await context.bot.send_message(
        chat_id=teacher_id,
        text=(
            f"Адміністратор зняв призначення учня "
            f"{pupil['pupil_name']} {pupil['pupil_surname']}."
        )
    )
    await context.bot.send_message(
        chat_id=pupil_id,
        text=(
            "Ваше призначення до викладача "
            f"{teacher['teacher_name']} {teacher['teacher_surname']} знято."
        ),
        reply_markup=pupil_keyboard
    )

# Request section for teacher

async def handle_teacher_requests(update: Update, context: ContextTypes.DEFAULT_TYPE):
    teachers = school_db.get_all_teachers()
    pending = [t for t in teachers if t['group_id'] > 0]
    if not pending:
        return await update.message.reply_text("Немає нових заявок від викладачів ❌")

    context.user_data['admin_teacher_requests'] = pending
    context.user_data['teacher_page_index'] = 0
    await send_teacher_request(update, context)


async def send_teacher_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    index = context.user_data['teacher_page_index']
    queue = context.user_data['admin_teacher_requests']
    teacher = queue[index]
    text = (
        f"Заявка вчителя {index + 1}/{len(queue)} 📋\n"
        f"{teacher['teacher_name']} {teacher['teacher_surname']} 👤\n"
        f"Мова викладання: {teacher['languages_teaching']} 🌐"
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

    await show_admin_panel(update, context)

    for key in ('admin_teacher_requests', 'teacher_page_index'):
        context.user_data.pop(key, None)


# Find a chat by pupil or teacher

async def start_chat_search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    context.user_data["chat_search"] = True
    await update.message.reply_text("Введіть ім'я або прізвище учня чи вчителя 🔎", reply_markup=back_button)


async def handle_chat_search_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get("chat_search"):
        return

    term = update.message.text.strip().lower().split()
    buttons = []
    if len(term) == 2:
        name, surname = term
        teacher = next((
            t for t in school_db.get_all_teachers()
            if t["teacher_name"].lower() == name and t["teacher_surname"].lower() == surname
        ), None)
        if teacher:
            buttons.append([
                InlineKeyboardButton(f"Вчитель: {teacher['teacher_name']} {teacher['teacher_surname']}",
                                     callback_data=f"open_chat_teacher_{teacher['teacher_id']}")
            ])
        else:
            pupil = next((
                p for p in school_db.get_all_pupils()
                if p["pupil_name"].lower() == name and p["pupil_surname"].lower() == surname
            ), None)
            if pupil:
                buttons.append([
                    InlineKeyboardButton(f"Учень: {pupil['pupil_name']} {pupil['pupil_surname']}",
                                         callback_data=f"open_chat_pupil_{pupil['pupil_id']}")
                ])

    if not buttons and len(term) >= 1:
        key = term[0]
        for t in school_db.get_all_teachers():
            if key in t["teacher_name"].lower() or key in t["teacher_surname"].lower():
                buttons.append([
                    InlineKeyboardButton(
                        f"Вчитель: {t['teacher_name']} {t['teacher_surname']}",
                        callback_data=f"open_chat_teacher_{t['teacher_id']}"
                    )
                ])
        for p in school_db.get_all_pupils():
            if key in p["pupil_name"].lower() or key in p["pupil_surname"].lower():
                buttons.append([
                    InlineKeyboardButton(
                        f"Учень: {p['pupil_name']} {p['pupil_surname']}",
                        callback_data=f"open_chat_pupil_{p['pupil_id']}"
                    )
                ])

    if not buttons:
        return await update.message.reply_text("❌ Нічого не знайдено. Спробуйте інше ім'я.")

    panel = InlineKeyboardMarkup(buttons)
    await update.message.reply_text("Оберіть чат:", reply_markup=panel)


async def handle_open_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data.split("_")
    role, uid = data[2], int(data[3])

    if role == "teacher":
        teacher = school_db.get_teacher(uid)
        link = teacher.get("telegram_invite")
        text = f"Чат викладача:\n{link}"
    else:
        conv = school_db.get_conversation_by_pupil(uid)
        if not conv:
            return await query.edit_message_text("❌ Для цього учня чат ще не створено.")
        teacher = school_db.get_teacher(conv["teacher_id"])
        link = teacher.get("telegram_invite")
        text = f"Чат учня (через викладача {teacher['teacher_name']}):\n{link}"

    await query.message.reply_text(text, reply_markup=admin_keyboard)


# Answer to requests

async def handle_admin_requests(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return

    queue = []
    for pupil in school_db.get_all_pupils():
        for request in pupil.get("requests_to_admin") or []:
            queue.append({**request, "role": "Учень", "user_id": pupil["pupil_id"]})
    for teacher in school_db.get_all_teachers():
        for request in teacher.get("requests_to_admin") or []:
            queue.append({**request, "role": "Викладач", "user_id": teacher["teacher_id"]})

    if not queue:
        return await update.message.reply_text("Немає нових запитів ❌", reply_markup=admin_keyboard)

    await update.message.reply_text(
        "Перегляньте нижче запити, для детального ознайомлення з цим можете натиснути відповідну кнопку",
        reply_markup=back_button)
    context.user_data["admin_requests"] = queue
    context.user_data["admin_request_index"] = 0
    await show_admin_request(update, context)


async def show_admin_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    index = context.user_data["admin_request_index"]
    queue = context.user_data["admin_requests"]
    request = queue[index]
    total = len(queue)

    if request['role'] == 'Учень':
        user = school_db.get_pupil(request["user_id"])
        user_name = user["pupil_name"]
        user_surname = user["pupil_surname"]
    else:
        user = school_db.get_teacher(request["user_id"])
        user_name = user["teacher_name"]
        user_surname = user["teacher_surname"]

    dt = datetime.fromisoformat(request["timestamp"])
    ts = dt.strftime("%d.%m.%Y %H:%M")

    text = (
        f"Запит {index + 1}/{total} 📨\n"
        f"{request['role']}: {user_name} {user_surname} \n\n"
        f"{request['text']}\n\n"
        f"Дата запиту: {ts}"
    )

    buttons = [
        [
            InlineKeyboardButton("◀️ Назад", callback_data="admin_req_prev"),
            InlineKeyboardButton("Далі ▶️", callback_data="admin_req_next")
        ],
        [
            InlineKeyboardButton("Переглянути повністю запит", callback_data="admin_req_check")
        ]
    ]
    markup = InlineKeyboardMarkup(buttons)

    if update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=markup)
    else:
        await update.message.reply_text(text, reply_markup=markup)


async def handle_admin_req_nav(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    action = query.data.split("_")[2]

    index = context.user_data["admin_request_index"]
    total = len(context.user_data["admin_requests"])
    index = (index - 1) % total if action == "prev" else (index + 1) % total
    context.user_data["admin_request_index"] = index

    await show_admin_request(update, context)


async def handle_admin_req_check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    index = context.user_data["admin_request_index"]
    request = context.user_data["admin_requests"][index]

    await context.bot.copy_message(
        chat_id=query.message.chat.id,
        from_chat_id=request["user_id"],
        message_id=request["message_id"]
    )


async def handle_admin_reply_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_admin(user_id):
        return
    if "admin_requests" not in context.user_data:
        return

    index = context.user_data["admin_request_index"]
    request = context.user_data["admin_requests"][index]

    await context.bot.send_message(
        chat_id=request["user_id"],
        text="<b>Вітаємо, нижче відповідь на ваш запит ✅</b>",
        parse_mode="HTML"
    )
    await context.bot.copy_message(
        from_chat_id=update.message.chat.id,
        chat_id=request["user_id"],
        message_id=update.message.message_id
    )

    if request["role"] == "Учень":
        school_db.clear_pupil_requests(request["user_id"])
    else:
        school_db.clear_teacher_requests(request["user_id"])

    context.user_data.pop("admin_requests", None)
    context.user_data.pop("admin_request_index", None)

    await update.message.reply_text("Відповідь відправлено ✅", reply_markup=admin_keyboard)


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
    
    application.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            handle_admin_reply_text
        ),
        group=0
    )

    application.add_handler(CommandHandler("admin", show_admin_panel), group=1)
    application.add_handler(MessageHandler(filters.Text("Заявки учнів 📜"), handle_pupil_requests), group=1)
    application.add_handler(MessageHandler(filters.Text("Заявки викладачів 📜"), handle_teacher_requests), group=1)
    application.add_handler(
        MessageHandler(filters.Text("Керувати призначеннями ⚙️"), open_assignment_manager),
        group=1
    )
    application.add_handler(
        MessageHandler(filters.Text("Знайти чат 🔎"), start_chat_search),
        group=1
    )
    application.add_handler(MessageHandler(filters.Text("Запити 📜"), handle_admin_requests), group=1)

    application.add_handler(
        CallbackQueryHandler(handle_admin_req_nav, pattern=r"^admin_req_(prev|next)$"),
        group=1
    )
    application.add_handler(
        CallbackQueryHandler(handle_admin_req_check, pattern=r"^admin_req_check$"),
        group=1
    )

    application.add_handler(
        CallbackQueryHandler(handle_pupil_request_navigation, pattern=r"^request_(prev|next)$"),
        group=1
    )
    application.add_handler(
        CallbackQueryHandler(handle_pupil_request_action, pattern=r"^request_(decline|assign)_\d+$"),
        group=1
    )
    application.add_handler(
        CallbackQueryHandler(handle_teacher_navigation, pattern=r"^teacher_(prev|next)$"),
        group=1
    )
    application.add_handler(
        CallbackQueryHandler(handle_teacher_action, pattern=r"^teacher_(decline|confirm)_\d+$"),
        group=1
    )
    application.add_handler(
        CallbackQueryHandler(handle_assign_teacher, pattern=r"^assign_\d+(_\d+)?$"),
        group=1
    )

    application.add_handler(
        CallbackQueryHandler(handle_open_chat, pattern=r"^open_chat_(teacher|pupil)_\d+$"),
        group=1
    )

    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_chat_search_input),
        group=1
    )

    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_assign_text),
        group=2
    )

    # … other filters.Text(…) handlers …


    # NOW the catch-all reply-text handler, in a later group:
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_admin_reply_text),
        group=2
    )
    application.add_handler(
        CallbackQueryHandler(handle_clear_assignment, pattern=r"^clear_\d+_\d+$"),
        group=2
    )


    application.bot_data["notify_all_admins"] = notify_all_admins
