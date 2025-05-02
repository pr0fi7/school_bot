from database.models import school_db


def is_pupil(user_id: int) -> bool:
    with school_db.conn.cursor() as cursor:
        cursor.execute("SELECT 1 FROM public.pupils WHERE pupil_id = %s", (user_id,))
        return cursor.fetchone() is not None


def is_admin(admin_id: int) -> bool:
    with school_db.conn.cursor() as cursor:
        cursor.execute("SELECT 1 FROM public.admins WHERE admin_id = %s", (admin_id,))
        return cursor.fetchone() is not None


def is_teacher(teacher_id: int) -> bool:
    with school_db.conn.cursor() as cursor:
        cursor.execute("SELECT 1 FROM public.teachers WHERE teacher_id = %s", (teacher_id,))
        return cursor.fetchone() is not None
