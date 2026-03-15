"""Database connection and initialization."""
import os
import sqlite3
import logging

logger = logging.getLogger(__name__)

BASE_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
DATABASE = os.path.join(BASE_DIR, "database.db")


def get_db():
    """Get database connection with row factory."""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    """Initialize database schema. Call at app startup."""
    conn = get_db()
    try:
        conn.executescript(_SCHEMA)
        conn.commit()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error("Database initialization failed: %s", e)
        raise
    finally:
        conn.close()


_SCHEMA = '''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS study_sessions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        subject TEXT NOT NULL,
        start_time TIMESTAMP NOT NULL,
        end_time TIMESTAMP,
        duration_minutes INTEGER DEFAULT 0,
        notes TEXT,
        distractions INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id)
    );

    CREATE TABLE IF NOT EXISTS user_subjects (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        subject_name TEXT NOT NULL,
        UNIQUE(user_id, subject_name),
        FOREIGN KEY (user_id) REFERENCES users(id)
    );

    CREATE INDEX IF NOT EXISTS idx_sessions_user_date ON study_sessions(user_id, start_time);
    CREATE INDEX IF NOT EXISTS idx_sessions_subject ON study_sessions(user_id, subject);
'''
