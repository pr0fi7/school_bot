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


def declined_request(pupil_name: str, pupil_surname: str) -> str:
    return f"""Шановний(а) {pupil_name} {pupil_surname},

На жаль, вашу заявку на навчання в онлайн-школі UKnow було відхилено. 
Якщо у вас є запитання або ви хочете спробувати ще раз — будь ласка, зв’яжіться з адміністрацією.

Бажаємо успіхів і сподіваємося побачити вас у наших майбутніх курсах! 🚀"""


def teacher_new_pupil_notification(pupil_name: str, pupil_surname: str) -> str:
    """
    SMS, яке надсилається викладачеві, коли йому призначають нового учня.
    """
    return f"""👋 Привіт!

У вас новий учень для занять:

👤 {pupil_name} {pupil_surname}

Зв’яжіться з ним для узгодження часу та деталей уроку. Успіхів! 🚀"""


def student_assigned_teacher_notification(teacher_name: str, teacher_surname: str) -> str:
    """
    SMS, яке надсилається учневі, коли йому призначають викладача.
    """
    return f"""🎉 Вітаємо!

Вам призначено викладача:

👨‍🏫 {teacher_name} {teacher_surname}

Він незабаром зв’яжеться з вами для уточнення розкладу. Гарного навчання! 📚"""
