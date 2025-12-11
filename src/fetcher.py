"""Mastodon APIからのデータ取得"""
import logging
from mastodon import Mastodon


def get_thread_context(client: Mastodon, status_id: int) -> dict:
    """スレッドのコンテキスト（祖先と子孫）を取得"""
    try:
        ctx = client.status_context(status_id)
        return {
            'ancestors': ctx.get('ancestors', []),
            'descendants': ctx.get('descendants', [])
        }
    except Exception as e:
        logging.error(f"Failed to get thread context: {e}")
        return {'ancestors': [], 'descendants': []}


def get_full_thread(client: Mastodon, status) -> list:
    """ステータスを含む完全なスレッドを取得"""
    ctx = get_thread_context(client, status.id)
    return ctx['ancestors'] + [status] + ctx['descendants']


def get_status(client: Mastodon, status_id: int):
    """ステータスを取得"""
    try:
        return client.status(status_id)
    except Exception as e:
        logging.error(f"Failed to get status {status_id}: {e}")
        return None


def get_account_info(client: Mastodon):
    """認証済みアカウントの情報を取得"""
    try:
        return client.me()
    except Exception as e:
        logging.error(f"Failed to get account info: {e}")
        return None
