import sqlite3
import os

DATABASE_PATH = os.path.join(
    os.path.dirname(__file__),
    "jenny.db"
)


def get_db_connection():
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def create_tables():
    connection = get_db_connection()
    cursor = connection.cursor()

    # USERS TABLE
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # CHATS TABLE
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            conversation_id TEXT,
            user_message TEXT NOT NULL,
            ai_response TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Check existing chat columns
    cursor.execute("PRAGMA table_info(chats)")
    columns = [column["name"] for column in cursor.fetchall()]

    # Migration: conversation_id
    if "conversation_id" not in columns:
        cursor.execute(
            "ALTER TABLE chats ADD COLUMN conversation_id TEXT"
        )

    # Migration: user_id
    if "user_id" not in columns:
        cursor.execute(
            "ALTER TABLE chats ADD COLUMN user_id INTEGER"
        )

    # Handle old conversations
    cursor.execute("""
        UPDATE chats
        SET conversation_id = 'old-' || id
        WHERE conversation_id IS NULL
    """)

    # Indexes
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_chats_user
        ON chats(user_id)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_chats_conversation
        ON chats(conversation_id)
    """)

    connection.commit()
    connection.close()