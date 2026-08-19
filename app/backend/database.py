import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Dict, Generator, List, Optional


class DatabaseManager:
    """Manages SQLite database storage in the user's Documents directory."""

    def __init__(self, db_path: Optional[Path] = None):
        if db_path is None:
            docs_dir = Path.home() / "Documents" / "PandaPilot"
            docs_dir.mkdir(parents=True, exist_ok=True)
            self.db_path = docs_dir / "pandapilot.db"
        else:
            self.db_path = Path(db_path)
            self.db_path.parent.mkdir(parents=True, exist_ok=True)

        self._init_db()

    @contextmanager
    def _get_connection(self) -> Generator[sqlite3.Connection, None, None]:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def _init_db(self) -> None:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS profiles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    host TEXT NOT NULL,
                    port INTEGER DEFAULT 22,
                    ssh_user TEXT NOT NULL,
                    ssh_auth_type TEXT DEFAULT 'password',
                    ssh_password TEXT,
                    ssh_key_path TEXT,
                    sasl_user TEXT NOT NULL,
                    sasl_password TEXT NOT NULL,
                    sasl_mechanism TEXT DEFAULT 'SCRAM-SHA-256',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS activity_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    profile_id INTEGER,
                    command TEXT NOT NULL,
                    action_type TEXT,
                    status TEXT,
                    output TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(profile_id) REFERENCES profiles(id) ON DELETE CASCADE
                );
            """)
            conn.commit()

    def get_profiles(self) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM profiles ORDER BY name ASC")
            return [dict(row) for row in cursor.fetchall()]

    def get_profile(self, profile_id: int) -> Optional[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM profiles WHERE id = ?", (profile_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def add_profile(self, data: Dict[str, Any]) -> int:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO profiles (
                    name, host, port, ssh_user, ssh_auth_type,
                    ssh_password, ssh_key_path, sasl_user, sasl_password, sasl_mechanism
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                data.get("name", "Untitled Cluster"),
                data.get("host", "127.0.0.1"),
                int(data.get("port", 22)),
                data.get("ssh_user", "root"),
                data.get("ssh_auth_type", "password"),
                data.get("ssh_password", ""),
                data.get("ssh_key_path", ""),
                data.get("sasl_user", ""),
                data.get("sasl_password", ""),
                data.get("sasl_mechanism", "SCRAM-SHA-256"),
            ))
            conn.commit()
            return cursor.lastrowid

    def update_profile(self, profile_id: int, data: Dict[str, Any]) -> bool:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE profiles
                SET name = ?, host = ?, port = ?, ssh_user = ?, ssh_auth_type = ?,
                    ssh_password = ?, ssh_key_path = ?, sasl_user = ?,
                    sasl_password = ?, sasl_mechanism = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (
                data.get("name", "Untitled Cluster"),
                data.get("host", "127.0.0.1"),
                int(data.get("port", 22)),
                data.get("ssh_user", "root"),
                data.get("ssh_auth_type", "password"),
                data.get("ssh_password", ""),
                data.get("ssh_key_path", ""),
                data.get("sasl_user", ""),
                data.get("sasl_password", ""),
                data.get("sasl_mechanism", "SCRAM-SHA-256"),
                profile_id
            ))
            conn.commit()
            return cursor.rowcount > 0

    def delete_profile(self, profile_id: int) -> bool:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM profiles WHERE id = ?", (profile_id,))
            conn.commit()
            return cursor.rowcount > 0

    def log_activity(
        self,
        profile_id: Optional[int],
        command: str,
        action_type: str,
        status: str,
        output: str
    ) -> int:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO activity_logs (profile_id, command, action_type, status, output)
                VALUES (?, ?, ?, ?, ?)
            """, (profile_id, command, action_type, status, output))
            conn.commit()
            return cursor.lastrowid

    def get_activity_logs(self, limit: int = 50) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT l.*, p.name as profile_name
                FROM activity_logs l
                LEFT JOIN profiles p ON l.profile_id = p.id
                ORDER BY l.created_at DESC
                LIMIT ?
            """, (limit,))
            return [dict(row) for row in cursor.fetchall()]
