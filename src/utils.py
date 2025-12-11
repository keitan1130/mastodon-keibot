"""ユーティリティ関数"""
import re
import time
from datetime import datetime


def strip_html(html: str) -> str:
    """HTMLタグを除去"""
    return re.sub(r'<[^>]+>', '', html)


def extract_custom_prompt(text: str) -> str | None:
    """
    テキストから /*ここにプロンプト*/ 形式のカスタムプロンプトを抽出

    複数行にも対応:
    /*
    あ
    あ
    */
    """
    # re.DOTALL で . が改行にもマッチ、.*? で最短マッチ
    match = re.search(r'/\*(.*?)\*/', text, re.DOTALL)
    if match:
        return match.group(1).strip()
    return None


def remove_markdown(text: str) -> str:
    """Markdownフォーマットを除去"""
    plain_text = text

    # 0. WebFetchToolの出力やAPIレスポンスを削除
    plain_text = re.sub(r'\[WebFetchTool\].*?(?=\n[^\[\s]|\Z)', '', plain_text, flags=re.DOTALL)

    # 0.5. Google CLI credentials メッセージを削除
    plain_text = re.sub(r'Loaded cached credentials\..*?\n?', '', plain_text, flags=re.MULTILINE)

    # 1. JSONブロックを削除 (より厳密に)
    plain_text = re.sub(r'\{.*?\}', '', plain_text, flags=re.DOTALL)

    # 2. JSON残りカスを削除
    plain_text = re.sub(r'^[}\]\s]*$', '', plain_text, flags=re.MULTILINE)
    plain_text = re.sub(r'^\s*[":,\[\]{}]\s*$', '', plain_text, flags=re.MULTILINE)

    # 3. コロンで始まる行を削除 (JSONの残りカス)
    plain_text = re.sub(r'^\s*":\s*', '', plain_text, flags=re.MULTILINE)

    # 4. コードブロックを削除 (```で囲まれた部分)
    plain_text = re.sub(r'```.*?```', '', plain_text, flags=re.DOTALL)

    # 5. 見出しを削除 (#)
    plain_text = re.sub(r'^#+\s*(.*)$', r'\1', plain_text, flags=re.MULTILINE)

    # 6. 太字と斜体を削除 (内容のみ残す)
    plain_text = re.sub(r'\*\*([^\*]+)\*\*', r'\1', plain_text)  # **太字**
    plain_text = re.sub(r'__([^_]+)__', r'\1', plain_text)  # __太字__
    plain_text = re.sub(r'\*([^\*]+)\*', r'\1', plain_text)  # *斜体*
    plain_text = re.sub(r'_([^_]+)_', r'\1', plain_text)  # _斜体_

    # 7. リンクを削除 (リンクテキストのみ残す)
    plain_text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', plain_text)

    # 8. 引用符を削除 (>)
    plain_text = re.sub(r'^>\s*', '', plain_text, flags=re.MULTILINE)

    # 9. インラインコードを削除 (`)
    plain_text = re.sub(r'`([^`]+)`', r'\1', plain_text)

    # 10. 水平線 (---, ***, ___) を削除
    plain_text = re.sub(r'^[-\*_]{3,}\s*$', '', plain_text, flags=re.MULTILINE)

    # 11. 余分な空行を整理
    plain_text = re.sub(r'\n\n+', '\n\n', plain_text).strip()

    return plain_text


def split_into_segments(text: str, max_len: int = 400) -> list[str]:
    """テキストを文で区切り、max_lenに収まるセグメントに分割"""
    # Split into sentences (supports Japanese and English punctuation)
    sentences = re.split(r'(?<=[。.！？!?])\s*', text)
    segments = []
    current = ''
    limit = max_len - 100  # より余裕をもたせる

    for sentence in sentences:
        if not sentence:
            continue
        prospect = f"{current}{sentence}" if current else sentence
        if len(prospect) > limit and current:
            segments.append(current)
            current = sentence
        else:
            current = prospect

    # If current is still longer than limit, force split by character limit
    if current and len(current) > limit:
        while len(current) > limit:
            segments.append(current[:limit])
            current = current[limit:]

    if current:
        segments.append(current)

    total = len(segments)
    # Prefix with count
    return [f"{i+1}/{total}: {seg.strip()}" for i, seg in enumerate(segments)]


class SnowflakeGenerator:
    """Snowflake ID generator (Twitter-style 64bit)"""

    def __init__(self, machine_id: int = 1, datacenter_id: int = 1):
        self.machine_id = machine_id & 0x1F  # 5 bits
        self.datacenter_id = datacenter_id & 0x1F  # 5 bits
        self.sequence = 0
        self.last_timestamp = -1
        # Custom epoch (2025-01-01 00:00:00 UTC in milliseconds)
        self.epoch = int(datetime(2025, 1, 1).timestamp() * 1000)

    def generate(self) -> int:
        timestamp = int(time.time() * 1000)

        if timestamp < self.last_timestamp:
            raise Exception("Clock moved backwards")

        if timestamp == self.last_timestamp:
            self.sequence = (self.sequence + 1) & 0xFFF  # 12 bits
            if self.sequence == 0:
                # Wait for next millisecond
                while timestamp <= self.last_timestamp:
                    timestamp = int(time.time() * 1000)
        else:
            self.sequence = 0

        self.last_timestamp = timestamp

        # Generate Snowflake ID
        # 1 bit (unused) + 41 bits timestamp + 5 bits datacenter + 5 bits machine + 12 bits sequence
        snowflake = ((timestamp - self.epoch) << 22) | (self.datacenter_id << 17) | (self.machine_id << 12) | self.sequence
        return snowflake


# Global Snowflake generator instance
snowflake_gen = SnowflakeGenerator(machine_id=1, datacenter_id=1)
