from telegram import Update


async def welcome(update: Update, context):
    if update.message.new_chat_members:
        for user in update.message.new_chat_members:
            await update.message.reply_text(
                f"""Привіт {user.first_name} 👋
                    Вітаємо Вас в чаті онлайн школи UKnow 🎓

                    Наші адміністратори готові Вам допомогти щодня з 7:00 до 22:30⏰

                    Також, тут Ви можете написати викладачеві стосовно навчання та матеріалів 📚

                    Готові розпочати? 😊
                    Тисніть кнопки нижче для зв'язку з викладачем ⬇️""",
                parse_mode="HTML"
            )

            await update.message.reply_image(
                photo="public/images/image.jpg",
                caption="Вітаємо в UKnow!",
            )
