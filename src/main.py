"""Keibotエントリーポイント"""
import logging
import sys

from .config import validate_config
from .bot import create_client, MentionBot


def main():
    """ボットを起動"""
    # 設定を検証
    if not validate_config():
        sys.exit(1)

    # クライアントを作成
    client = create_client()

    # 起動メッセージを投稿
    try:
        startup_status = client.status_post(status="起動(開発中)")
        logging.info(f"Posted startup message: 起動 (ID: {startup_status['id']})")
    except Exception as e:
        logging.error(f"Failed to post startup message: {e}")

    # ボットを作成して開始
    bot = MentionBot(client)
    logging.info('Starting Mastodon mention stream...')

    try:
        client.stream_user(bot)
    except KeyboardInterrupt:
        logging.info('Shutting down bot.')
    except Exception as e:
        logging.error(f'Stream error: {e}')
        raise


if __name__ == '__main__':
    main()
