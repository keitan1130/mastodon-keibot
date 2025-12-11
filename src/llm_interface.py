"""LLM（Ollama）との通信インターフェース"""
import logging
from typing import Optional

try:
    import ollama
except ImportError:
    ollama = None

from .config import OLLAMA_MODEL
from .utils import remove_markdown


class OllamaInterface:
    """Ollamaとの通信を担当"""

    def __init__(self, model: str = None):
        self.model = model or OLLAMA_MODEL
        self._system_prompt: Optional[str] = None

        if ollama is None:
            logging.error("ollama package not installed. Run: pip install ollama")

    def update_system_prompt(self, system_prompt: str) -> bool:
        """システムプロンプトを設定"""
        self._system_prompt = system_prompt
        logging.info(f'Updated system prompt ({len(system_prompt)} chars)')
        return True

    def read_system_prompt(self) -> Optional[str]:
        """現在のシステムプロンプトを取得"""
        return self._system_prompt

    def generate(self, user_prompt: str) -> str:
        """Ollamaでテキストを生成"""
        if ollama is None:
            return 'Error: ollama package not installed.'

        try:
            # メッセージを構築
            messages = []

            # システムプロンプトがあれば追加
            if self._system_prompt:
                messages.append({
                    "role": "system",
                    "content": self._system_prompt
                })

            # ユーザーメッセージを追加
            messages.append({
                "role": "user",
                "content": user_prompt
            })

            logging.info(f"Sending to Ollama ({self.model}): {len(messages)} messages")

            # Ollamaでチャット
            response = ollama.chat(
                model=self.model,
                messages=messages
            )

            # レスポンスからテキストを取得
            content = response['message']['content']
            logging.info(f"Ollama response received ({len(content)} chars)")
            return content

        except ollama.ResponseError as e:
            logging.error(f'Ollama response error: {e}')
            return 'Error: Ollama response error.'
        except Exception as e:
            logging.error(f'Unexpected error calling Ollama: {e}')
            return f'Error: {str(e)}'

    def generate_clean(self, user_prompt: str) -> str:
        """Ollamaでテキストを生成し、Markdownを除去"""
        response = self.generate(user_prompt)
        return remove_markdown(response)


# シングルトンインスタンス
_llm: Optional[OllamaInterface] = None


def get_llm() -> OllamaInterface:
    """LLMインターフェースのシングルトンインスタンスを取得"""
    global _llm
    if _llm is None:
        _llm = OllamaInterface()
    return _llm
