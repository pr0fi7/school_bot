from datetime import datetime


def welcome_message(user_first_name: str) -> str:
    return f"""Привіт, {user_first_name} 👋🏻
Вітаємо Вас в чаті онлайн школи UKnow 🎓

Наші адміністратори готові Вам допомогти щодня з 7:00 до 22:30 ⏰

Також, тут Ви можете написати викладачеві стосовно навчання та матеріалів 📚

Готові розпочати? 😊
Тисніть кнопки нижче для зв'язку з викладачем ⬇️"""


def new_student_notification(name: str, surname: str, language: str) -> str:
    return f"""🆕 Новий учень подав заявку на навчання!

👤 Ім’я: {name} {surname}
🌐 Мова навчання: {language}

🎯 Виберіть для нього викладача у відповідному меню."""


def new_teacher_notification(name: str, surname: str, language: str) -> str:
    return f"""🆕 Новий викладач подав заявку на навчання!

👤 Ім’я: {name} {surname}
🌐 Мова викладання: {language}

🎯 Підтвердіть нового вчителя у відповідному меню!"""


def declined_request(pupil_name: str, pupil_surname: str) -> str:
    return f"""Шановний(а) {pupil_name} {pupil_surname},

На жаль, вашу заявку в онлайн-школу UKnow було відхилено. 
Якщо у вас є запитання або ви хочете спробувати ще раз — будь ласка, зв’яжіться з адміністрацією."""


def teacher_new_pupil_notification(pupil_name: str, pupil_surname: str) -> str:
    return f"""👋 Привіт!

У вас новий учень для занять:

👤 {pupil_name} {pupil_surname}

Зв’яжіться з ним для узгодження часу та деталей уроку. Успіхів! 🚀"""


def student_assigned_teacher_notification(teacher_name: str, teacher_surname: str) -> str:
    return f"""🎉 Вітаємо!

Вам призначено викладача:

👨‍🏫 {teacher_name} {teacher_surname}

Він незабаром зв’яжеться з вами для уточнення розкладу. Гарного навчання! 📚"""


def admin_notification_sms(
        sender: str,
        student_name: str,
        student_surname: str,
        teacher_name: str,
        teacher_surname: str,
        message_text: str,
        sent_at: datetime
) -> str:
    date_str = sent_at.strftime("%d.%m.%Y %H:%M")

    if sender.lower() in ("pupil", "student"):
        sender_full = f"{student_name} {student_surname}"
    else:
        sender_full = f"{teacher_name} {teacher_surname}"


    return (
        f"⚠️ Увага!\n"
        f"Розмова: {student_name} {student_surname} ↔️ {teacher_name} {teacher_surname}\n"
        f"Відправник: {sender_full}\n"
        f"Повідомлення: {message_text}\n"
        f"Дата: {date_str}"
    )
