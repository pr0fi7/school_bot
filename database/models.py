import os
import psycopg2
import psycopg2.extras
from dotenv import load_dotenv
from uuid import uuid4
from datetime import datetime
from config.settings import db_params

load_dotenv()

class Database:
    def __init__(self, conn_params):
        self.conn = psycopg2.connect(**conn_params)
        self._create_tables()

    def _create_tables(self):
        with self.conn.cursor() as cursor:
            self.conn.autocommit = True
            try:
                cursor.execute('''DO $$ 
                BEGIN 
                    IF NOT EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'pgcrypto') THEN
                        CREATE EXTENSION pgcrypto;
                    END IF;
                END $$;''')

                cursor.execute('''CREATE TABLE IF NOT EXISTS public.teachers (
                    teacher_id SERIAL PRIMARY KEY,
                    teach_name VARCHAR(100) NOT NULL,
                    teacher_surname VARCHAR(100) NOT NULL
                );''')

                cursor.execute('''CREATE TABLE IF NOT EXISTS public.pupils (
                    pupil_id SERIAL PRIMARY KEY,
                    pupil_name VARCHAR(100) NOT NULL,
                    pupil_surname VARCHAR(100) NOT NULL,
                    languages_learning VARCHAR(255)
                );''')

                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS public.conversations (
                    group_id UUID PRIMARY KEY,
                    branch_id UUID,
                    teacher_id INT REFERENCES public.teachers(teacher_id) ON DELETE CASCADE,
                    pupil_id INT REFERENCES public.pupils(pupil_id) ON DELETE CASCADE,
                    conversation JSONB,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );''')

                cursor.execute('''CREATE TABLE IF NOT EXISTS public.admins (
                    admin_id SERIAL PRIMARY KEY,
                    admin_name VARCHAR(100) NOT NULL,
                    admin_surname VARCHAR(100) NOT NULL,
                    admin_username VARCHAR(100) NOT NULL UNIQUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );''')
            except Exception as e:
                print("Error creating tables:", e)
            finally:
                self.conn.autocommit = False

    def get_all_conversations(self):
        with self.conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
            cursor.execute("SELECT * FROM public.conversations")
            rows = cursor.fetchall()
            return [dict(row) for row in rows]  # Convert to JSON format

    def get_conversation(self, branch_id):
        with self.conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
            cursor.execute("SELECT * FROM public.conversations WHERE branch_id = %s", (branch_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def insert_teacher(self, teach_name, teacher_surname):
        with self.conn.cursor() as cursor:
            cursor.execute('''INSERT INTO public.teachers (teach_name, teacher_surname)
                              VALUES (%s, %s) RETURNING teacher_id;''', (teach_name, teacher_surname))
            teacher_id = cursor.fetchone()[0]
            self.conn.commit()
            return teacher_id

    def insert_pupil(self, pupil_name, pupil_surname, languages_learning):
        with self.conn.cursor() as cursor:
            cursor.execute('''INSERT INTO public.pupils (pupil_name, pupil_surname, languages_learning)
                              VALUES (%s, %s, %s) RETURNING pupil_id;''', (pupil_name, pupil_surname, languages_learning))
            pupil_id = cursor.fetchone()[0]
            self.conn.commit()
            return pupil_id

    def insert_conversation(self, teacher_id, pupil_id, conversation_data):
        with self.conn.cursor() as cursor:
            cursor.execute('''INSERT INTO public.conversations (teacher_id, pupil_id, conversation)
                              VALUES (%s, %s, %s) RETURNING conversation_id;''', 
                           (teacher_id, pupil_id, psycopg2.extras.Json(conversation_data)))
            conversation_id = cursor.fetchone()[0]
            self.conn.commit()
            return conversation_id

    def update_conversation(self, conversation_id, conversation_data):
        with self.conn.cursor() as cursor:
            cursor.execute('''UPDATE public.conversations
                              SET conversation = %s
                              WHERE conversation_id = %s;''', 
                           (psycopg2.extras.Json(conversation_data), conversation_id))
            self.conn.commit()

    def delete_conversation(self, conversation_id):
        with self.conn.cursor() as cursor:
            cursor.execute('''DELETE FROM public.conversations WHERE conversation_id = %s;''', (conversation_id,))
            self.conn.commit()
    
    def get_all_teachers(self):
        with self.conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
            cursor.execute("SELECT * FROM public.teachers")
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    
    def get_all_pupils(self):
        with self.conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
            cursor.execute("SELECT * FROM public.pupils")
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    



print(db_params)

school_db = Database(db_params)
