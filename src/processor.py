"""プロンプト処理とメッセージ構築"""
import re
import logging
from typing import Optional

from .utils import strip_html, extract_custom_prompt
from .config import DEFAULT_CHARACTER_PROMPT, SYSTEM_PROMPT_TEMPLATE
from .storage import get_storage


class PromptProcessor:
    """プロンプトの処理と構築を担当"""

    def __init__(self):
        self.storage = get_storage()

    def determine_active_prompt(
        self,
        text: str,
        conversation_id: Optional[int] = None
    ) -> tuple[str, Optional[str]]:
        """
        アクティブなプロンプトを決定

        Returns:
            tuple: (active_prompt, custom_prompt_if_new)
        """
        # テキストからカスタムプロンプトを抽出
        custom_prompt = extract_custom_prompt(text)

        # 既存の会話データを取得
        existing_data = None
        if conversation_id:
            existing_data = self.storage.load_conversation(conversation_id)

        if custom_prompt:
            # 新しいカスタムプロンプトが見つかった
            logging.info(f"Custom prompt detected: {custom_prompt}")
            return custom_prompt, custom_prompt
        elif existing_data and existing_data.get("custom_prompt"):
            # 既存の会話にカスタムプロンプトがある
            active_prompt = existing_data["custom_prompt"]
            logging.info(f"Using existing custom prompt: {active_prompt}")
            return active_prompt, None
        elif existing_data and existing_data.get("ai_prompt"):
            # 既存の会話の保存されたプロンプトを使用
            logging.info("Using existing saved prompt")
            return existing_data["ai_prompt"], None
        else:
            # デフォルトのキャラクター設定
            logging.info("Using default character prompt")
            return DEFAULT_CHARACTER_PROMPT, None

    def build_system_prompt(self, character_prompt: str) -> str:
        """システムプロンプトを構築"""
        return SYSTEM_PROMPT_TEMPLATE + character_prompt

    def build_conversation_prompt(
        self,
        thread_data: list,
        conversation_id: Optional[int] = None,
        custom_prompt: Optional[str] = None
    ) -> str:
        """
        Gemini用の会話プロンプトを構築

        Args:
            thread_data: 現在のスレッドデータ
            conversation_id: 既存の会話ID（あれば）
            custom_prompt: 除去するカスタムプロンプト（あれば）

        Returns:
            構築されたプロンプト
        """
        conversation_parts = []
        existing_ids = set()

        # 既存の会話データがあれば取得
        if conversation_id:
            existing_data = self.storage.load_conversation(conversation_id)
            if existing_data and existing_data.get("thread_data"):
                existing_ids = {status["id"] for status in existing_data["thread_data"]}

                # 既存の会話履歴から会話を構築
                for thread_status in existing_data["thread_data"]:
                    acct = thread_status["account"]
                    content = thread_status["content"]
                    # カスタムプロンプト部分を除去
                    content = re.sub(r'/\*[^*]+\*/', '', content).strip()
                    if content:
                        conversation_parts.append(f"{acct}: {content}")

        # 現在のスレッドから新しい投稿を追加
        for status in thread_data:
            if str(status.id) not in existing_ids:
                acct = status['account']['acct'] if isinstance(status, dict) else status.account.acct
                content = strip_html(status.get('content', '') if isinstance(status, dict) else status.content)

                # カスタムプロンプト部分を除去
                if custom_prompt and custom_prompt in content:
                    content = re.sub(r'/\*[^*]+\*/', '', content).strip()
                if content:
                    conversation_parts.append(f"{acct}: {content}")

        # 会話プロンプトを構築
        if not conversation_parts:
            # 会話内容が空の場合
            logging.info("Empty conversation - sending greeting prompt")
            return "【重要】新しい会話が始まりました。キャラクターとして自然に挨拶してください。"

        conversation_text = '\n'.join(conversation_parts)
        logging.info(f"Built conversation prompt with {len(conversation_parts)} messages")

        return f"""【会話ログ】
{conversation_text}

【重要】上記の会話に対して、最後の投稿に返信してください。キャラクターとして自然に応答してください。"""


# シングルトンインスタンス
_processor: Optional[PromptProcessor] = None


def get_processor() -> PromptProcessor:
    """プロセッサのシングルトンインスタンスを取得"""
    global _processor
    if _processor is None:
        _processor = PromptProcessor()
    return _processor
