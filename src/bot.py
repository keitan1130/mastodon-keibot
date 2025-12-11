"""Mastodonボットのメインロジック"""
import logging
from mastodon import Mastodon, StreamListener

from .config import API_BASE_URL, ACCESS_TOKEN
from .utils import strip_html, snowflake_gen
from .fetcher import get_full_thread
from .processor import get_processor
from .llm_interface import get_gemini
from .poster import MastodonPoster
from .storage import get_storage


class MentionBot(StreamListener):
    """メンションを処理するボット"""

    def __init__(self, client: Mastodon):
        super().__init__()
        self.client = client
        self.poster = MastodonPoster(client)
        self.processor = get_processor()
        self.gemini = get_gemini()
        self.storage = get_storage()

    def on_notification(self, notification):
        """通知を処理"""
        if notification.type != 'mention':
            return

        status = notification.status
        author_acct = status.account.acct
        text = strip_html(status.content)
        logging.info(f"Mention from @{author_acct}: {text}")

        try:
            self._handle_mention(status, author_acct, text)
        except Exception as e:
            logging.error(f"Error handling mention: {e}", exc_info=True)

    def _handle_mention(self, status, author_acct: str, text: str):
        """メンションを処理"""
        # スレッド全体を取得
        convo = get_full_thread(self.client, status)

        # 既存の会話IDを検索、なければ新規作成
        conversation_id = self.storage.find_existing_conversation(convo)
        if conversation_id:
            logging.info(f"Found existing conversation ID: {conversation_id}")
        else:
            conversation_id = snowflake_gen.generate()
            logging.info(f"Generated new conversation ID: {conversation_id}")

        # アクティブなプロンプトを決定
        active_prompt, new_custom_prompt = self.processor.determine_active_prompt(
            text, conversation_id
        )

        # システムプロンプトを更新
        system_prompt = self.processor.build_system_prompt(active_prompt)
        self.gemini.update_system_prompt(system_prompt)

        # メンション投稿にお気に入りをつける
        self.poster.favourite_status(status.id)

        # 会話プロンプトを構築
        gemini_prompt = self.processor.build_conversation_prompt(
            convo,
            conversation_id,
            new_custom_prompt
        )

        # AIレスポンスを生成
        response = self.gemini.generate(gemini_prompt)
        logging.info(f"AI response: {response[:50]}...")

        # Markdownを除去してクリーンな応答を取得
        from .utils import remove_markdown
        clean_response = remove_markdown(response)

        # 返信を投稿
        posted_replies = self.poster.post_reply(
            clean_response,
            original_acct=author_acct,
            reply_to_id=status.id
        )

        # 投稿後のデータを更新
        current_gemini_content = self.gemini.read_system_prompt() or active_prompt

        # ボットの返信IDを記録
        bot_reply_ids = {str(s['id']) for s in posted_replies} if posted_replies else set()

        # 会話データを保存
        updated_convo = convo + posted_replies if posted_replies else convo

        # 既存データのカスタムプロンプトを取得
        existing_data = self.storage.load_conversation(conversation_id)
        existing_custom_prompt = existing_data.get("custom_prompt") if existing_data else None

        self.storage.save_conversation(
            conversation_id=conversation_id,
            mention_status=status,
            thread_data=updated_convo,
            ai_prompt=current_gemini_content,
            ai_response=response,
            custom_prompt=new_custom_prompt if new_custom_prompt else existing_custom_prompt,
            bot_reply_ids=bot_reply_ids
        )

    def on_stream_error(self, error):
        """ストリームエラーを処理"""
        logging.error(f'Stream error: {error}')
        return True  # ストリームを維持


def create_client() -> Mastodon:
    """Mastodonクライアントを作成"""
    client = Mastodon(
        access_token=ACCESS_TOKEN,
        api_base_url=API_BASE_URL,
        request_timeout=60,
        ratelimit_method='throw',
    )
    client.session.verify = False  # Disable SSL verification if needed
    return client
