from datetime import datetime

from telegram import Update
from telegram.ext import MessageHandler, filters, ContextTypes

from bot.admin import handle_admin_back
from bot.permissions import is_pupil, is_teacher, is_admin
from bot.keyboards import pupil_keyboard, back_button
from database.models import school_db

CHAT_WITH = 'chat_with'


# Connecting all buttons

async def show_pupil_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    if is_pupil(user.id):
        await update.message.reply_text(
            "Оберіть опцію нижче, з ким ви хочете зв'язатися",
            reply_markup=pupil_keyboard
        )


# Teacher and pupil chatting

async def start_pupil_teacher_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_pupil(update.effective_user.id):
        return

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
        await context.bot.copy_message(
            from_chat_id=msg.chat.id,
            chat_id=conv['group_id'],
            message_thread_id=conv['branch_id'],
            message_id=msg.message_id
        )


async def handle_teacher_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_teacher(update.effective_user.id):
        return

    msg = update.message

    conv = school_db.get_conversation(msg.chat_id, msg.message_thread_id)
    if not conv:
        return await update.message.reply_text("Не знайдено розмову для цього потоку.")

    pupil = school_db.get_pupil(conv['pupil_id'])

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


# Admin and pupil chatting

# TODO: admin chat, keep it for future
# async def start_pupil_admin_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     if not is_pupil(update.effective_user.id):
#         return
#
#     context.user_data[CHAT_WITH] = 'admin'
#
#     await update.message.reply_text("💬 Ви в режимі чату з адміністрацією. Ваші вхідні повідомлення:")
#     queue = context.user_data.get(ADMIN_QUEUE, [])
#
#     for text, ts in queue:
#         await update.message.reply_text(f"{text}\n[{ts}]")
#
#     context.user_data[ADMIN_QUEUE] = []
#     await update.message.reply_text("Щоб вийти з чату, натисніть:", reply_markup=back_button)


# TODO: admin chat, keep it for future
# async def handle_admin_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     if not is_admin(update.effective_user.id):
#         return
#
#     text = update.message.text
#     now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M')
#     pupil_id = context.user_data.get('current_pupil_id')
#     if not pupil_id:
#         await update.message.reply_text("Спочатку виберіть учня для чату.")
#         return
#
#     if context.user_data.get(CHAT_WITH) != 'admin':
#         queue = context.user_data.setdefault(ADMIN_QUEUE, [])
#         queue.append((text, now))
#         await update.message.reply_text("Ваше повідомлення буде доставлено, коли учень увійде в режим чату.")
#     else:
#         await context.bot.send_message(
#             chat_id=pupil_id,
#             text=f"Адміністратор: {text}\n[{now}]"
#         )


# Additional handlers

async def exit_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.pop(CHAT_WITH, None)
    if is_pupil(update.effective_user.id):
        await update.message.reply_text("Ви вийшли з чату.", reply_markup=pupil_keyboard)
        school_db.update_pupil_online(False, update.effective_user.id)
    if is_admin(update.effective_user.id):
        await handle_admin_back(update, context)


def register_conversation(application):
    application.add_handler(MessageHandler(filters.Text("Викладач 👨‍🏫"), start_pupil_teacher_chat))
    application.add_handler(MessageHandler(filters.Text("◀️ Назад"), exit_chat))

    teacher_ids = [t["teacher_id"] for t in school_db.get_all_teachers()]
    application.add_handler(
        MessageHandler(filters.ALL & filters.User(teacher_ids), handle_teacher_message)
    )

    pupil_ids = [p["pupil_id"] for p in school_db.get_all_pupils()]
    application.add_handler(
        MessageHandler(
            filters.ALL & ~filters.COMMAND & filters.User(pupil_ids),
            handle_pupil_to_teacher_message
        )
    )

    # TODO: admin chat, keep it for future
    # application.add_handler(MessageHandler(filters.Text("Адміністратор 👩‍💼"), start_pupil_admin_chat))
    # admin_ids = [a["admin_id"] for a in school_db.get_all_admins()]
    # application.add_handler(
    #     MessageHandler(filters.TEXT & filters.User(admin_ids), handle_admin_message)
    # )
