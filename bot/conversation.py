from datetime import datetime

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import MessageHandler, filters, ContextTypes, ConversationHandler

from bot.admin import handle_admin_back
from bot.messages import admin_notification_sms
from bot.permissions import is_pupil, is_teacher, is_admin
from bot.keyboards import pupil_keyboard, back_button, teacher_keyboard, admin_keyboard
from bot.trigger_words import trigger_words

from database.models import school_db

CHAT_WITH = 'chat_with'
ADMIN_CHAT = 0


# Connecting all buttons

async def show_teacher_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    if is_teacher(user.id):
        await update.message.reply_text(
            "Оберіть опцію нижче для початку дії:",
            reply_markup=teacher_keyboard
        )


async def show_pupil_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    if is_pupil(user.id):
        await update.message.reply_text(
            "Оберіть опцію нижче, з ким ви хочете зв'язатися:",
            reply_markup=pupil_keyboard
        )


# Teacher and pupil chatting

async def start_pupil_teacher_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if not is_pupil(user_id):
        return

    conv = school_db.get_conversation_by_pupil(user_id)
    if not conv or not conv.get('teacher_id'):
        return await update.message.reply_text(
            "Вам ще не призначено викладача ❗️"
            "Будь ласка, зачекайте, доки ми не підберемо для вас викладача 📚"
        )

    context.user_data[CHAT_WITH] = 'teacher'
    school_db.update_pupil_online(True, update.effective_user.id)

    conv = school_db.get_conversation_by_pupil(update.effective_user.id)
    if conv and conv.get('conversation_id'):
        entries = school_db.get_conversation_messages(conv['conversation_id'])
        for entry in entries:
            dt = datetime.fromisoformat(entry.get('timestamp', ''))
            ts = dt.strftime('%d.%m.%Y %H:%M')
            if entry.get('type') == 'text':
                await update.message.reply_text(f"{entry['content']}\n[{ts}]")
            else:
                await context.bot.copy_message(
                    chat_id=update.effective_user.id,
                    from_chat_id=conv['group_id'],
                    message_id=entry.get('message_id')
                )
                await update.message.reply_text(f"[{ts}]")
        school_db.clear_conversation_messages(conv['conversation_id'])

    await update.message.reply_text("💬 Ви в режимі чату з викладачем. Ваші вхідні повідомлення:")

    await update.message.reply_text("Щоб вийти з чату, натисніть:", reply_markup=back_button)


async def handle_pupil_to_teacher_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_pupil(user_id):
        return

    msg = update.message
    conv = school_db.get_conversation_by_pupil(user_id)

    if context.user_data.get(CHAT_WITH) == 'teacher':
        await check_message(update, context, msg, conv, "pupil")

        await context.bot.copy_message(
            from_chat_id=msg.chat.id,
            chat_id=conv['group_id'],
            message_thread_id=conv['branch_id'],
            message_id=msg.message_id
        )


async def handle_teacher_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_teacher(update.effective_user.id) or update.effective_chat.type == 'private':
        return

    msg = update.message

    conv = school_db.get_conversation(msg.chat_id, msg.message_thread_id)

    pupil = school_db.get_pupil(conv['pupil_id'])

    await check_message(update, context, msg, conv, "teacher")

    if pupil['is_online']:
        await context.bot.copy_message(
            from_chat_id=update.effective_chat.id,
            chat_id=pupil['pupil_id'],
            message_id=msg.message_id
        )
    else:
        if msg.text:
            msg_type, content = 'text', msg.text
        else:
            msg_type, content = 'message', msg.text

        school_db.append_conversation_message(
            conversation_id=conv['conversation_id'],
            sender='teacher',
            msg_type=msg_type,
            content=content,
            message_id=msg.message_id
        )


# Requesting to admin

async def start_admin_chat(update, context):
    if is_pupil(update.message.from_user.id):
        existing = school_db.get_pupil_requests(update.message.from_user.id)
    elif is_teacher(update.message.from_user.id):
        existing = school_db.get_teacher_requests(update.message.from_user.id)

    if existing:
        await update.message.reply_text(
            "Ви вже надіслали запит, будь ласка, зачекайте, поки ми обробимо попередній ⚠️"
        )
        return
    context.user_data[CHAT_WITH] = 'admin'
    await update.message.reply_text(
        "Будь ласка, надішліть свій запит, щоб адміністрація його розглянула. Запит можна надсилати один раз, далі буде необхідно чекати відповідь 💬",
        reply_markup=back_button
    )


async def handle_message_to_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get(CHAT_WITH) != 'admin':
        return

    msg = update.message
    user_id = msg.from_user.id
    raw_text = msg.text or msg.caption or ""
    sent_at = datetime.utcnow().isoformat()

    if is_pupil(user_id):
        add_request = school_db.add_pupil_request
        role = "Учень"
        keyboard = pupil_keyboard
    elif is_teacher(user_id):
        add_request = school_db.add_teacher_request
        role = "Викладач"
        keyboard = teacher_keyboard
    else:
        context.user_data.pop(CHAT_WITH, None)
        return await msg.reply_text(
            "Вибачте, надсилати запити можуть лише зареєстровані користувачі ❗️"
        )

    entry = {
        "sender_id": user_id,
        "role": role,
        "message_id": msg.message_id,
        "text": raw_text,
        "timestamp": sent_at
    }
    add_request(user_id, entry)

    admins = school_db.get_all_admins()
    for admin in admins:
        await context.bot.send_message(
            chat_id=admin["admin_id"],
            text="Отримано новий запит. Будь ласка, надайте відповідь у певне визначеному меню 🔔",
            reply_markup=admin_keyboard
        )

    context.user_data.pop(CHAT_WITH, None)
    await msg.reply_text(
        "Ваш запит надіслано адміністраторам ✅",
        reply_markup=keyboard
    )


# Mass notifying

async def teacher_notyfing(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    user_id = msg.from_user.id
    text = msg.text or ""

    if not is_teacher(user_id):
        return

    if text == "Повідомити усіх учнів 🔔":
        context.user_data["broadcast_teacher"] = True
        return await msg.reply_text(
            "Введіть повідомлення для всіх ваших учнів: ✉️",
            reply_markup=back_button
        )

    if not context.user_data.get("broadcast_teacher"):
        return

    raw_text = msg.text or msg.caption or ""
    sent_at = datetime.utcnow().isoformat()

    result = await trigger_words(raw_text)
    if result["status"]:
        teacher = school_db.get_teacher(user_id)
        admins = school_db.get_all_admins()
        for adm in admins:
            await context.bot.send_message(
                chat_id=adm["admin_id"],
                text=f"⚠️ Викладач {teacher['teacher_name']} {teacher['teacher_surname']} намагався розіслати з тригер-словом:\n{raw_text}\n\n{sent_at}"
            )
        context.user_data.pop("broadcast_teacher", None)
        return

    convs = [c for c in school_db.get_all_conversations() if c["teacher_id"] == user_id]

    for conv in convs:
        group_id = conv["group_id"]
        branch_id = conv["branch_id"]

        await context.bot.copy_message(
            chat_id=group_id,
            message_thread_id=branch_id,
            from_chat_id=msg.chat.id,
            message_id=msg.message_id
        )

    await msg.reply_text("✅ Ваше повідомлення надіслано всім учням.", reply_markup=teacher_keyboard)
    context.user_data.pop("broadcast_teacher", None)


async def admin_notyfing(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    user_id = msg.from_user.id
    text = msg.text or ""

    if not is_admin(user_id):
        return

    if text == "Видалити сповіщення вчителям 🗑️":
        return await delete_teacher_notifications(update, context)

    if text == "Повідомити усіх вчителів 🔔":
        context.user_data["broadcast_admin"] = True
        return await msg.reply_text(
            "✉️ Введіть повідомлення, яке потрібно розіслати всім вчителям: ✉️",
            reply_markup=back_button,
        )

    if not context.user_data.get("broadcast_admin"):
        return

    school_db.clear_teacher_notifications(user_id)

    teachers = school_db.get_all_teachers()
    for t in teachers:
        tid = t["teacher_id"]

        header_msg = await context.bot.send_message(
            chat_id=tid,
            text="Повідомлення від адміністрації 📢",
        )
        body_msg = await context.bot.copy_message(
            chat_id=tid,
            from_chat_id=msg.chat.id,
            message_id=msg.message_id,
        )

        school_db.set_teacher_notification(
            admin_id=user_id,
            teacher_id=tid,
            header_id=header_msg.message_id,
            body_id=body_msg.message_id,
        )

    await msg.reply_text(
        "✅ Ваше повідомлення надіслано всім вчителям.",
        reply_markup=admin_keyboard,
    )
    context.user_data.pop("broadcast_admin", None)

async def delete_teacher_notifications(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    admin_id = msg.from_user.id
    if not is_admin(admin_id):
        return

    data = school_db.get_teacher_notifications(admin_id)
    if not data:
        return await msg.reply_text("Немає сповіщень для видалення.")

    for tid, (header_id, body_id) in data.items():
        for mid in (header_id, body_id):
            await context.bot.delete_message(chat_id=int(tid), message_id=mid)

    school_db.clear_teacher_notifications(admin_id)
    await msg.reply_text("✅ Сповіщення вчителям видалено.")

async def admin_pupil_notyfing(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    user_id = msg.from_user.id
    text = msg.text or ""

    if not is_admin(user_id):
        return

    if text == "Видалити сповіщення учням 🗑️":
        return await delete_pupil_notifications(update, context)

    if text == "Повідомити усіх учнів 🔔":
        context.user_data["broadcast_admin_pupil"] = True
        return await msg.reply_text(
            "✉️ Введіть повідомлення, яке потрібно розіслати всім учням: ✉️",
            reply_markup=back_button,
        )

    if not context.user_data.get("broadcast_admin_pupil"):
        return

    school_db.clear_pupil_notifications(user_id)

    pupils = school_db.get_all_pupils()
    for p in pupils:
        pid = p["pupil_id"]

        header_msg = await context.bot.send_message(
            chat_id=pid,
            text="Повідомлення від адміністрації 📢",
        )
        body_msg = await context.bot.copy_message(
            chat_id=pid,
            from_chat_id=msg.chat.id,
            message_id=msg.message_id,
        )

        school_db.set_pupil_notification(
            admin_id=user_id,
            pupil_id=pid,
            header_id=header_msg.message_id,
            body_id=body_msg.message_id,
        )

    await msg.reply_text(
        "✅ Ваше повідомлення надіслано всім учням.",
        reply_markup=admin_keyboard,
    )
    context.user_data.pop("broadcast_admin_pupil", None)

async def delete_pupil_notifications(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    admin_id = msg.from_user.id
    if not is_admin(admin_id):
        return

    data = school_db.get_pupil_notifications(admin_id)
    if not data:
        return await msg.reply_text("Немає сповіщень для видалення.")

    for pid, (header_id, body_id) in data.items():
        for mid in (header_id, body_id):
            await context.bot.delete_message(chat_id=int(pid), message_id=mid)

    school_db.clear_pupil_notifications(admin_id)
    await msg.reply_text("✅ Сповіщення учням видалено.")


# Additional handlers

async def check_message(update: Update, context: ContextTypes.DEFAULT_TYPE, msg, conv, sender):
    raw_text = msg.text or msg.caption or ""
    result = await trigger_words(raw_text)
    if result['status']:
        admins = school_db.get_all_admins()
        pupil = school_db.get_pupil(conv['pupil_id'])
        teacher = school_db.get_teacher(conv['teacher_id'])

        chat_link = teacher['telegram_invite']

        button = InlineKeyboardButton(text="🔗 Відкрити чат", url=chat_link)
        markup = InlineKeyboardMarkup([[button]])

        for admin in admins:
            tg_id = admin.get("admin_id")
            text = admin_notification_sms(
                sender=sender,
                student_name=pupil['pupil_name'],
                student_surname=pupil['pupil_surname'],
                teacher_name=teacher['teacher_name'],
                teacher_surname=teacher['teacher_surname'],
                message_text=raw_text,
                sent_at=datetime.now()
            )
            await context.bot.send_message(
                chat_id=tg_id,
                text=text,
                reply_markup=markup
            )


async def exit_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()

    if is_pupil(update.effective_user.id):
        await update.message.reply_text("Ви вийшли з чату.", reply_markup=pupil_keyboard)
        school_db.update_pupil_online(False, update.effective_user.id)

    if is_admin(update.effective_user.id):
        await handle_admin_back(update, context)


def register_conversation(application):
    application.add_handler(
        MessageHandler(filters.Text("Написати адміністратору 👩‍💼"),
                       start_admin_chat),
        group=2
    )

    application.add_handler(
        MessageHandler(
            filters.ALL & ~filters.COMMAND,
            teacher_notyfing
        ),
        group=3
    )

    application.add_handler(
        MessageHandler(
            filters.ALL & ~filters.COMMAND,
            admin_notyfing
        ),
        group=2
    )

    application.add_handler(
        MessageHandler(
            filters.ALL & ~filters.COMMAND,
            admin_pupil_notyfing
        ),
        group=2
    )

    application.add_handler(
        MessageHandler(filters.Text("Написати викладачеві 👨‍🏫"),
                       start_pupil_teacher_chat),
        group=0
    )
    application.add_handler(
        MessageHandler(filters.Text("◀️ Назад"),
                       exit_chat),
        group=0
    )

    teacher_ids = [t["teacher_id"] for t in school_db.get_all_teachers()]
    pupil_ids = [p["pupil_id"] for p in school_db.get_all_pupils()]

    application.add_handler(
        MessageHandler(
            filters.ALL & ~filters.COMMAND & filters.User(teacher_ids),
            handle_teacher_message
        ),
        group=1
    )

    application.add_handler(
        MessageHandler(
            filters.ALL & ~filters.COMMAND & filters.User(pupil_ids) & (
                    filters.ChatType.GROUP | filters.ChatType.SUPERGROUP),
            handle_pupil_to_teacher_message
        ),
        group=1
    )

    application.add_handler(
        MessageHandler(
            filters.ALL & ~filters.COMMAND & filters.User(teacher_ids + pupil_ids),
            handle_message_to_admin
        ),
        group=0
    )
