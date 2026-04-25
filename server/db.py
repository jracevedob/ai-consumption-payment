from __future__ import annotations

import os
import sqlite3
from pathlib import Path
from typing import Optional, Tuple


def db_path() -> Path:
    return Path(os.getenv("ACP_DB_PATH", "acp.sqlite")).resolve()


def connect() -> sqlite3.Connection:
    con = sqlite3.connect(str(db_path()), check_same_thread=False)
    con.row_factory = sqlite3.Row
    return con


def migrate(con: sqlite3.Connection) -> None:
    cur = con.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          email TEXT NOT NULL UNIQUE,
          password_hash TEXT NOT NULL,
          salt TEXT NOT NULL,
          created_at TEXT NOT NULL
        );
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS sessions (
          id TEXT PRIMARY KEY,
          user_id INTEGER NOT NULL,
          expires_at TEXT NOT NULL,
          created_at TEXT NOT NULL,
          FOREIGN KEY (user_id) REFERENCES users(id)
        );
        """
    )
    con.commit()


def get_user_by_email(con: sqlite3.Connection, email: str) -> Optional[sqlite3.Row]:
    return con.execute("SELECT * FROM users WHERE email = ?", (email.lower().strip(),)).fetchone()


def get_user_by_id(con: sqlite3.Connection, user_id: int) -> Optional[sqlite3.Row]:
    return con.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()


def create_user(con: sqlite3.Connection, email: str, password_hash: str, salt: str, created_at: str) -> int:
    cur = con.cursor()
    cur.execute(
        "INSERT INTO users(email, password_hash, salt, created_at) VALUES(?,?,?,?)",
        (email.lower().strip(), password_hash, salt, created_at),
    )
    con.commit()
    return int(cur.lastrowid)


def create_session(con: sqlite3.Connection, session_id: str, user_id: int, expires_at: str, created_at: str) -> None:
    con.execute(
        "INSERT INTO sessions(id, user_id, expires_at, created_at) VALUES(?,?,?,?)",
        (session_id, user_id, expires_at, created_at),
    )
    con.commit()


def delete_session(con: sqlite3.Connection, session_id: str) -> None:
    con.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
    con.commit()


def get_session(con: sqlite3.Connection, session_id: str) -> Optional[sqlite3.Row]:
    return con.execute("SELECT * FROM sessions WHERE id = ?", (session_id,)).fetchone()

