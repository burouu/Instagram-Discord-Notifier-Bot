# core/database_manager.py
import sqlite3
import logging
from typing import Optional, Dict, Any
import os

class DatabaseManager:
    def __init__(self, db_path: str):
        self.db_path = os.path.abspath(db_path)
        logging.info(f"Database manager initialized. Database file path: {self.db_path}")
        self._create_tables()
        self._migrate_tables()

    def _get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _create_tables(self):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tracked_accounts (
                username TEXT NOT NULL,
                channel_id INTEGER NOT NULL,
                role_id INTEGER,
                message_content TEXT,
                embed_title TEXT,
                embed_description TEXT,
                embed_author_text TEXT,
                embed_author_icon_url TEXT,
                embed_footer_text TEXT,
                embed_footer_icon_url TEXT,
                embed_color TEXT,
                PRIMARY KEY (username, channel_id)
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sent_media (
                media_id TEXT PRIMARY KEY NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()
        conn.close()
        logging.info("Database tables verified.")

    def _migrate_tables(self):
        """Add new columns if they don't exist."""
        conn = self._get_connection()
        cursor = conn.cursor()
        columns_to_add = [
            ("role_id", "INTEGER"),
            ("message_content", "TEXT"),
            ("embed_title", "TEXT"),
            ("embed_description", "TEXT"),
            ("embed_author_text", "TEXT"),
            ("embed_author_icon_url", "TEXT"),
            ("embed_footer_text", "TEXT"),
            ("embed_footer_icon_url", "TEXT"),
            ("embed_color", "TEXT")
        ]
    
        cursor.execute("PRAGMA table_info(tracked_accounts)")
        existing_columns = [row["name"] for row in cursor.fetchall()]

        for col_name, col_type in columns_to_add:
            if col_name not in existing_columns:
                try:
                    cursor.execute(f"ALTER TABLE tracked_accounts ADD COLUMN {col_name} {col_type}")
                    logging.info(f"Migrated DB: Added column '{col_name}' to tracked_accounts.")
                except Exception as e:
                    logging.warning(f"Migration warning for {col_name}: {e}")
        
        conn.commit()
        conn.close()


    def add_account(self, username: str, channel_id: int, role_id: Optional[int] = None) -> bool:
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT INTO tracked_accounts (username, channel_id, role_id) VALUES (?, ?, ?)", 
                (username, channel_id, role_id)
            )
            conn.commit()
            logging.info(f"SUCCESSFULLY WROTE to DB: Account '{username}' to Channel {channel_id} (Role: {role_id}).")
            return True
        except sqlite3.IntegrityError:
            logging.warning(f"Mapping already exists for Account '{username}' in Channel ID {channel_id}.")
            return False
        finally:
            conn.close()

    def get_account_settings(self, username: str, channel_id: int) -> Optional[Dict[str, Any]]:
        """Return settings for a specific account in a specific channel."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM tracked_accounts WHERE username = ? AND channel_id = ?", (username, channel_id))
        result = cursor.fetchone()
        conn.close()
        return dict(result) if result else None

    def update_account_setting(self, username: str, channel_id: int, key: str, value: Optional[str]):
        conn = self._get_connection()
        cursor = conn.cursor()
        valid_keys = ["message_content", "embed_title", "embed_description", "embed_color", 
                      "embed_footer_text", "embed_author_text", "embed_author_icon_url", "embed_footer_icon_url"]
        if key not in valid_keys:
            return
            
        cursor.execute(f"UPDATE tracked_accounts SET {key} = ? WHERE username = ? AND channel_id = ?", (value, username, channel_id))
        conn.commit()
        conn.close()
        logging.info(f"Updated setting '{key}' for user {username} in channel {channel_id}.")


    def remove_account(self, username: str, channel_id: int) -> bool:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM tracked_accounts WHERE username = ? AND channel_id = ?", (username, channel_id))
        conn.commit()
        return cursor.rowcount > 0

    def get_accounts_for_channel(self, channel_id: int) -> list[str]:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT username FROM tracked_accounts WHERE channel_id = ?", (channel_id,))
        return [row[0] for row in cursor.fetchall()]

    def get_unique_tracked_usernames(self) -> list[str]:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT username FROM tracked_accounts")
        return [row[0] for row in cursor.fetchall()]
        
    def get_channels_for_username(self, username: str) -> list[int]:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT channel_id FROM tracked_accounts WHERE username = ?", (username,))
        return [row[0] for row in cursor.fetchall()]

    def is_media_sent(self, media_id: str) -> bool:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM sent_media WHERE media_id = ?", (media_id,))
        result = cursor.fetchone()
        conn.close()
        return result is not None

    def mark_media_as_sent(self, media_id: str) -> None:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT OR IGNORE INTO sent_media (media_id) VALUES (?)", (media_id,))
        conn.commit()
        conn.close()
    
    def get_guild_settings(self, guild_id: int):
        return {}