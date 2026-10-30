
import sqlite3
from pathlib import Path

DATABASE_PATH = (
    Path(__file__).resolve().parent.parent / "library.db"
)


def get_db_connection():
    connection = sqlite3.connect(DATABASE_PATH)

    connection.row_factory = sqlite3.Row

    # Enable foreign key checking.
    connection.execute("PRAGMA foreign_keys = ON")

    return connection


def initialize_db():
    connection = get_db_connection()

    # BOOKS TABLE
    connection.execute("""
        CREATE TABLE IF NOT EXISTS books (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            author TEXT NOT NULL,
            isbn TEXT UNIQUE,
            available INTEGER NOT NULL DEFAULT 1
        )
    """)

    # MEMBERS TABLE
    connection.execute("""
        CREATE TABLE IF NOT EXISTS members (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            phone TEXT
        )
    """)

    # LOANS TABLE
    connection.execute("""
        CREATE TABLE IF NOT EXISTS loans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            book_id INTEGER NOT NULL,
            member_id INTEGER NOT NULL,

            issue_date TEXT NOT NULL,
            due_date TEXT NOT NULL,
            return_date TEXT,

            FOREIGN KEY (book_id)
                REFERENCES books(id),

            FOREIGN KEY (member_id)
                REFERENCES members(id)
        )
    """)
    connection.execute("""
    CREATE TABLE IF NOT EXISTS librarians (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL UNIQUE,
        password_hash TEXT NOT NULL
    )
""")

    connection.commit()
    connection.close()
