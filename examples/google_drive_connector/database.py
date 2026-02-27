"""
SQLite storage for Google Drive connected accounts, installs, and sync history.
"""

import json
import os
import sqlite3
from typing import Optional, List, Dict

DATABASE_PATH = os.environ.get("DATABASE_PATH", "./connector.db")


def get_db() -> sqlite3.Connection:
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS installs (
            install_id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            tenant_id TEXT NOT NULL,
            scopes_granted TEXT,
            status TEXT DEFAULT 'active',
            installed_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS google_accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            install_id TEXT NOT NULL,
            email TEXT NOT NULL,
            display_name TEXT,
            google_user_id TEXT,
            access_token TEXT NOT NULL,
            refresh_token TEXT,
            token_expires_at TEXT,
            status TEXT DEFAULT 'active',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (install_id) REFERENCES installs(install_id),
            UNIQUE(install_id, email)
        );

        CREATE TABLE IF NOT EXISTS sync_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            install_id TEXT NOT NULL,
            google_account_id INTEGER NOT NULL,
            google_file_id TEXT NOT NULL,
            file_name TEXT NOT NULL,
            askdiana_document_id TEXT,
            status TEXT DEFAULT 'pending',
            error_message TEXT,
            synced_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (install_id) REFERENCES installs(install_id),
            FOREIGN KEY (google_account_id) REFERENCES google_accounts(id)
        );
    """)
    conn.commit()
    conn.close()


# ------------------------------------------------------------------ #
# Installs                                                            #
# ------------------------------------------------------------------ #

def save_install(install_id: str, user_id: str, tenant_id: str, scopes_granted: list):
    conn = get_db()
    conn.execute(
        "INSERT OR REPLACE INTO installs (install_id, user_id, tenant_id, scopes_granted) VALUES (?, ?, ?, ?)",
        (install_id, user_id, tenant_id, json.dumps(scopes_granted)),
    )
    conn.commit()
    conn.close()


def remove_install(install_id: str):
    conn = get_db()
    conn.execute("DELETE FROM sync_history WHERE install_id = ?", (install_id,))
    conn.execute("DELETE FROM google_accounts WHERE install_id = ?", (install_id,))
    conn.execute("DELETE FROM installs WHERE install_id = ?", (install_id,))
    conn.commit()
    conn.close()


def get_install(install_id: str) -> Optional[Dict]:
    conn = get_db()
    row = conn.execute("SELECT * FROM installs WHERE install_id = ?", (install_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


# ------------------------------------------------------------------ #
# Google Accounts                                                      #
# ------------------------------------------------------------------ #

def save_google_account(
    install_id: str,
    email: str,
    display_name: str,
    google_user_id: str,
    access_token: str,
    refresh_token: Optional[str],
    token_expires_at: Optional[str],
) -> int:
    conn = get_db()
    cursor = conn.execute(
        """INSERT INTO google_accounts
           (install_id, email, display_name, google_user_id, access_token, refresh_token, token_expires_at)
           VALUES (?, ?, ?, ?, ?, ?, ?)
           ON CONFLICT(install_id, email) DO UPDATE SET
             access_token = excluded.access_token,
             refresh_token = COALESCE(excluded.refresh_token, google_accounts.refresh_token),
             token_expires_at = excluded.token_expires_at,
             display_name = excluded.display_name,
             status = 'active'""",
        (install_id, email, display_name, google_user_id, access_token, refresh_token, token_expires_at),
    )
    account_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return account_id


def get_google_accounts(install_id: str) -> List[Dict]:
    conn = get_db()
    rows = conn.execute(
        "SELECT id, install_id, email, display_name, status, created_at FROM google_accounts WHERE install_id = ? AND status = 'active'",
        (install_id,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_google_account(account_id: int) -> Optional[Dict]:
    conn = get_db()
    row = conn.execute("SELECT * FROM google_accounts WHERE id = ?", (account_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def update_tokens(account_id: int, access_token: str, refresh_token: Optional[str], expires_at: Optional[str]):
    conn = get_db()
    conn.execute(
        "UPDATE google_accounts SET access_token = ?, refresh_token = COALESCE(?, refresh_token), token_expires_at = ? WHERE id = ?",
        (access_token, refresh_token, expires_at, account_id),
    )
    conn.commit()
    conn.close()


# ------------------------------------------------------------------ #
# Sync History                                                         #
# ------------------------------------------------------------------ #

def record_sync(
    install_id: str,
    google_account_id: int,
    google_file_id: str,
    file_name: str,
    askdiana_document_id: Optional[str] = None,
    status: str = "success",
    error_message: Optional[str] = None,
):
    conn = get_db()
    conn.execute(
        """INSERT INTO sync_history
           (install_id, google_account_id, google_file_id, file_name, askdiana_document_id, status, error_message)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (install_id, google_account_id, google_file_id, file_name, askdiana_document_id, status, error_message),
    )
    conn.commit()
    conn.close()


def get_sync_history(install_id: str, limit: int = 50) -> List[Dict]:
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM sync_history WHERE install_id = ? ORDER BY synced_at DESC LIMIT ?",
        (install_id, limit),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]
