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

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            conversation_id TEXT,
            user_message TEXT NOT NULL,
            ai_response TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Check whether conversation_id already exists
    cursor.execute("PRAGMA table_info(chats)")
    columns = [column["name"] for column in cursor.fetchall()]

    if "conversation_id" not in columns:
        cursor.execute(
            "ALTER TABLE chats ADD COLUMN conversation_id TEXT"
        )

    # Give existing messages individual conversation IDs
    cursor.execute("""
        UPDATE chats
        SET conversation_id = 'old-' || id
        WHERE conversation_id IS NULL
    """)

    connection.commit()
    connection.close()