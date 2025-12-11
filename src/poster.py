"""Mastodonへの投稿処理"""
import logging
from mastodon import Mastodon
from typing import Optional

from .utils import split_into_segments


class MastodonPoster:
    """Mastodonへの投稿を担当"""

    def __init__(self, client: Mastodon):
        self.client = client

    def post_status(
        self,
        text: str,
        visibility: str = 'public',
        in_reply_to_id: Optional[int] = None
    ):
        """単一のステータスを投稿"""
        try:
            status = self.client.status_post(
                status=text,
                in_reply_to_id=in_reply_to_id,
                visibility=visibility
            )
            logging.info(f"Posted status (ID: {status['id']})")
            return status
        except Exception as e:
            logging.error(f'Failed to post status: {e}')
            return None

    def post_thread(
        self,
        segments: list[str],
        original_acct: str,
        reply_to_id: int
    ) -> list:
        """
        スレッドとして複数の返信を投稿

        Args:
            segments: 投稿するセグメントのリスト
            original_acct: 最初の返信でメンションするアカウント
            reply_to_id: 返信先のステータスID

        Returns:
            投稿したstatusオブジェクトのリスト
        """
        prev_id = reply_to_id
        posted_statuses = []

        for idx, seg in enumerate(segments):
            text = seg
            if idx == 0:
                text = f"@{original_acct} {seg}"
            visibility = 'public' if idx == 0 else 'unlisted'

            # Log the content being posted for easy copying
            logging.info(f"Reply {idx+1}/{len(segments)}: {text[:60]}...")

            try:
                status = self.client.status_post(
                    status=text,
                    in_reply_to_id=prev_id,
                    visibility=visibility
                )
                posted_statuses.append(status)
                prev_id = status['id']
                logging.info(f"Posted reply {idx+1} (ID: {status['id']})")
            except Exception as e:
                logging.error(f'Failed to post segment {idx+1}: {e}')
                break

        return posted_statuses

    def post_reply(
        self,
        text: str,
        original_acct: str,
        reply_to_id: int,
        max_len: int = 400
    ) -> list:
        """
        テキストを適切に分割してスレッドとして返信

        Args:
            text: 返信するテキスト
            original_acct: メンションするアカウント
            reply_to_id: 返信先のステータスID
            max_len: セグメントの最大長

        Returns:
            投稿したstatusオブジェクトのリスト
        """
        segments = split_into_segments(text, max_len)
        logging.info(f"Posting {len(segments)} segments")
        return self.post_thread(segments, original_acct, reply_to_id)

    def favourite_status(self, status_id: int) -> bool:
        """ステータスをお気に入りに追加"""
        try:
            self.client.status_favourite(status_id)
            logging.info(f"Favourited status (ID: {status_id})")
            return True
        except Exception as e:
            logging.error(f"Failed to favourite status: {e}")
            return False

    def boost_status(self, status_id: int) -> bool:
        """ステータスをブースト"""
        try:
            self.client.status_reblog(status_id)
            logging.info(f"Boosted status (ID: {status_id})")
            return True
        except Exception as e:
            logging.error(f"Failed to boost status: {e}")
            return False
