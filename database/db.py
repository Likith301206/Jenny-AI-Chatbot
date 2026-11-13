import os
import psycopg

from psycopg.rows import dict_row
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")


def get_db_connection():

    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL is missing from .env")

    connection = psycopg.connect(
        DATABASE_URL,
        row_factory=dict_row
    )

    return connection


def create_tables():

    connection = get_db_connection()

    try:
        with connection.cursor() as cursor:

            # USERS TABLE
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id BIGSERIAL PRIMARY KEY,
                    name VARCHAR(100) NOT NULL,
                    email VARCHAR(254) UNIQUE NOT NULL,
                    password TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # CHATS TABLE
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS chats (
                    id BIGSERIAL PRIMARY KEY,
                    conversation_id TEXT,
                    user_message TEXT NOT NULL,
                    ai_response TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    user_id BIGINT REFERENCES users(id) ON DELETE CASCADE
                )
            """)

            # Ensure required columns exist
            cursor.execute("""
                ALTER TABLE chats
                ADD COLUMN IF NOT EXISTS conversation_id TEXT
            """)

            cursor.execute("""
                ALTER TABLE chats
                ADD COLUMN IF NOT EXISTS user_id BIGINT
                REFERENCES users(id) ON DELETE CASCADE
            """)

            # INDEXES
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_chats_user
                ON chats(user_id)
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_chats_conversation
                ON chats(conversation_id)
            """)

        connection.commit()

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()