"""会話データの保存（SQLiteベース）"""
import os
import sqlite3
import json
import logging
from datetime import datetime
from typing import Optional
from contextlib import contextmanager

from .config import DATA_DIR
from .utils import strip_html


class ConversationStorage:
    """SQLiteを使用した会話データストレージ"""

    def __init__(self, db_path: str = None):
        if db_path is None:
            os.makedirs(DATA_DIR, exist_ok=True)
            db_path = os.path.join(DATA_DIR, 'conversations.db')
        self.db_path = db_path
        self._init_db()

    @contextmanager
    def _get_connection(self):
        """データベース接続のコンテキストマネージャー"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def _init_db(self):
        """データベースとテーブルを初期化"""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # 会話テーブル
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS conversations (
                    id INTEGER PRIMARY KEY,
                    custom_prompt TEXT,
                    ai_prompt TEXT,
                    latest_ai_response TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            ''')

            # メッセージテーブル
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    conversation_id INTEGER NOT NULL,
                    status_id TEXT NOT NULL UNIQUE,
                    account TEXT NOT NULL,
                    content TEXT NOT NULL,
                    url TEXT,
                    is_bot_reply INTEGER DEFAULT 0,
                    created_at TEXT,
                    FOREIGN KEY (conversation_id) REFERENCES conversations(id)
                )
            ''')

            # インデックス作成
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_messages_conversation
                ON messages(conversation_id)
            ''')
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_messages_status
                ON messages(status_id)
            ''')

    def save_conversation(
        self,
        conversation_id: int,
        mention_status,
        thread_data: list,
        ai_prompt: str,
        ai_response: str,
        custom_prompt: str = None,
        bot_reply_ids: set = None
    ):
        """会話データを保存（更新）"""
        now = datetime.now().isoformat()
        bot_reply_ids = bot_reply_ids or set()

        with self._get_connection() as conn:
            cursor = conn.cursor()

            # 会話が存在するか確認
            cursor.execute('SELECT id FROM conversations WHERE id = ?', (conversation_id,))
            exists = cursor.fetchone() is not None

            if exists:
                # 更新
                if custom_prompt:
                    cursor.execute('''
                        UPDATE conversations
                        SET custom_prompt = ?, ai_prompt = ?, latest_ai_response = ?, updated_at = ?
                        WHERE id = ?
                    ''', (custom_prompt, ai_prompt, ai_response, now, conversation_id))
                else:
                    cursor.execute('''
                        UPDATE conversations
                        SET latest_ai_response = ?, updated_at = ?
                        WHERE id = ?
                    ''', (ai_response, now, conversation_id))
            else:
                # 新規作成
                cursor.execute('''
                    INSERT INTO conversations (id, custom_prompt, ai_prompt, latest_ai_response, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (conversation_id, custom_prompt, ai_prompt, ai_response, now, now))

            # メッセージを保存
            for status in thread_data:
                status_id = str(status.id)
                is_bot_reply = 1 if status_id in bot_reply_ids else 0

                try:
                    cursor.execute('''
                        INSERT OR IGNORE INTO messages
                        (conversation_id, status_id, account, content, url, is_bot_reply, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        conversation_id,
                        status_id,
                        status.account.acct,
                        strip_html(status.content),
                        status.url,
                        is_bot_reply,
                        status.created_at.isoformat() if status.created_at else None
                    ))
                except Exception as e:
                    logging.error(f"Failed to save message {status_id}: {e}")

        logging.info(f"Saved/Updated conversation {conversation_id}")

    def find_conversation_by_status(self, status_id: str) -> Optional[int]:
        """ステータスIDから会話IDを検索"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT conversation_id FROM messages WHERE status_id = ?
            ''', (status_id,))
            row = cursor.fetchone()
            return row['conversation_id'] if row else None

    def find_existing_conversation(self, thread_data: list) -> Optional[int]:
        """スレッド内の投稿から既存の会話IDを検索"""
        status_ids = [str(status.id) for status in thread_data]

        if not status_ids:
            return None

        with self._get_connection() as conn:
            cursor = conn.cursor()
            placeholders = ','.join(['?' for _ in status_ids])
            cursor.execute(f'''
                SELECT DISTINCT conversation_id FROM messages
                WHERE status_id IN ({placeholders})
                LIMIT 1
            ''', status_ids)
            row = cursor.fetchone()
            return row['conversation_id'] if row else None

    def load_conversation(self, conversation_id: int) -> Optional[dict]:
        """会話データを読み込み"""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # 会話情報を取得
            cursor.execute('SELECT * FROM conversations WHERE id = ?', (conversation_id,))
            conv_row = cursor.fetchone()

            if not conv_row:
                return None

            # メッセージを取得
            cursor.execute('''
                SELECT * FROM messages
                WHERE conversation_id = ?
                ORDER BY created_at ASC
            ''', (conversation_id,))
            messages = cursor.fetchall()

            return {
                'conversation_id': conv_row['id'],
                'custom_prompt': conv_row['custom_prompt'],
                'ai_prompt': conv_row['ai_prompt'],
                'latest_ai_response': conv_row['latest_ai_response'],
                'created_at': conv_row['created_at'],
                'updated_at': conv_row['updated_at'],
                'thread_data': [
                    {
                        'id': msg['status_id'],
                        'account': msg['account'],
                        'content': msg['content'],
                        'url': msg['url'],
                        'is_bot_reply': bool(msg['is_bot_reply']),
                        'created_at': msg['created_at']
                    }
                    for msg in messages
                ]
            }

    def update_custom_prompt(self, conversation_id: int, custom_prompt: str) -> bool:
        """カスタムプロンプトを更新"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE conversations
                SET custom_prompt = ?, updated_at = ?
                WHERE id = ?
            ''', (custom_prompt, datetime.now().isoformat(), conversation_id))

            if cursor.rowcount > 0:
                logging.info(f"Updated custom prompt for conversation {conversation_id}")
                return True
            return False

    def get_conversation_messages(self, conversation_id: int) -> list[dict]:
        """会話のメッセージ一覧を取得"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM messages
                WHERE conversation_id = ?
                ORDER BY created_at ASC
            ''', (conversation_id,))

            return [
                {
                    'id': row['status_id'],
                    'account': row['account'],
                    'content': row['content'],
                    'is_bot_reply': bool(row['is_bot_reply']),
                    'created_at': row['created_at']
                }
                for row in cursor.fetchall()
            ]

    def get_all_conversations(self, limit: int = 100) -> list[dict]:
        """全会話の一覧を取得"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, custom_prompt, created_at, updated_at,
                       (SELECT COUNT(*) FROM messages WHERE conversation_id = conversations.id) as message_count
                FROM conversations
                ORDER BY updated_at DESC
                LIMIT ?
            ''', (limit,))

            return [
                {
                    'id': row['id'],
                    'custom_prompt': row['custom_prompt'],
                    'message_count': row['message_count'],
                    'created_at': row['created_at'],
                    'updated_at': row['updated_at']
                }
                for row in cursor.fetchall()
            ]


# グローバルインスタンス
_storage: Optional[ConversationStorage] = None


def get_storage() -> ConversationStorage:
    """ストレージのシングルトンインスタンスを取得"""
    global _storage
    if _storage is None:
        _storage = ConversationStorage()
    return _storage
