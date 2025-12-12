"""設定と環境変数の管理"""
import os
import logging
from pathlib import Path

# .envファイルを読み込み
def load_dotenv():
    """プロジェクトルートの.envファイルから環境変数を読み込み"""
    env_path = Path(__file__).parent.parent / '.env'
    if env_path.exists():
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, _, value = line.partition('=')
                    os.environ.setdefault(key.strip(), value.strip())

# 起動時に.envを読み込み
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

# Environment variables
API_BASE_URL = os.environ.get('MASTODON_API_BASE_URL', '')
ACCESS_TOKEN = os.environ.get('MASTODON_ACCESS_TOKEN', '')

# Data storage paths
DATA_DIR = os.environ.get(
    'KEIBOT_DATA_DIR',
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')
)

# Ollama設定
OLLAMA_MODEL = os.environ.get('OLLAMA_MODEL', 'gemma3:12b')

# 返信の公開設定
# public: 公開, unlisted: 未収載, private: フォロワー限定, direct: ダイレクト
# follow: 相手の投稿の公開設定に合わせる
DEFAULT_VISIBILITY = os.environ.get('KEIBOT_VISIBILITY', 'follow')

# Default character prompt
DEFAULT_CHARACTER_PROMPT = """自分のことをグリフィンドールだと思っている一般人"""

# System prompt template
SYSTEM_PROMPT_TEMPLATE = """あなたは指定されたキャラクターとして振る舞うAIアシスタントです。
以下のキャラクター設定に完全に従って、そのキャラクターになりきって会話してください。
キャラクターとしての自然な会話を心がけてください。

【キャラクター設定】
"""

def validate_config():
    """設定を検証"""
    if not ACCESS_TOKEN:
        logging.error('ACCESS_TOKEN not set. Please export MASTODON_ACCESS_TOKEN.')
        return False
    return True
