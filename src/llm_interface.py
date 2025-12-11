"""LLM（Gemini）との通信インターフェース"""
import os
import subprocess
import logging
from typing import Optional

from .config import GEMINI_MD_PATH
from .utils import remove_markdown


class GeminiInterface:
    """Gemini CLIとの通信を担当"""

    def __init__(self, model: str = "gemini-2.5-flash"):
        self.model = model
        self.gemini_md_path = GEMINI_MD_PATH

    def update_system_prompt(self, system_prompt: str) -> bool:
        """GEMINI.mdを更新してシステムプロンプトを設定"""
        try:
            # ディレクトリが存在しない場合は作成
            os.makedirs(os.path.dirname(self.gemini_md_path), exist_ok=True)

            with open(self.gemini_md_path, 'w', encoding='utf-8') as f:
                f.write(system_prompt)
            logging.info(f'Updated GEMINI.md ({len(system_prompt)} chars)')
            return True
        except Exception as e:
            logging.error(f'Failed to update GEMINI.md: {e}')
            return False

    def read_system_prompt(self) -> Optional[str]:
        """現在のGEMINI.mdの内容を読み込み"""
        try:
            with open(self.gemini_md_path, 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            return None
        except Exception as e:
            logging.error(f'Failed to read GEMINI.md: {e}')
            return None

    def generate(self, prompt: str) -> str:
        """Geminiでテキストを生成"""
        try:
            result = subprocess.run(
                ['gemini', '-m', self.model, '-p', prompt],
                capture_output=True,
                text=True,
                check=True,
                timeout=120  # 2分のタイムアウト
            )
            response = result.stdout.strip()
            logging.info(f"Gemini response received ({len(response)} chars)")
            return response
        except subprocess.TimeoutExpired:
            logging.error('Gemini call timed out')
            return 'Error: response generation timed out.'
        except subprocess.CalledProcessError as e:
            logging.error(f'Gemini call failed: {e.stderr}')
            return 'Error: failed to generate response.'
        except FileNotFoundError:
            logging.error('Gemini CLI not found. Please ensure gemini is installed.')
            return 'Error: gemini CLI not found.'
        except Exception as e:
            logging.error(f'Unexpected error calling Gemini: {e}')
            return 'Error: unexpected error occurred.'

    def generate_clean(self, prompt: str) -> str:
        """Geminiでテキストを生成し、Markdownを除去"""
        response = self.generate(prompt)
        return remove_markdown(response)


# シングルトンインスタンス
_gemini: Optional[GeminiInterface] = None


def get_gemini() -> GeminiInterface:
    """Geminiインターフェースのシングルトンインスタンスを取得"""
    global _gemini
    if _gemini is None:
        _gemini = GeminiInterface()
    return _gemini
