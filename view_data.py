#!/usr/bin/env python3
"""会話データを確認するためのユーティリティスクリプト"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.storage import get_storage
from datetime import datetime


def list_conversations():
    """全会話の一覧を表示"""
    storage = get_storage()
    conversations = storage.get_all_conversations()

    if not conversations:
        print("会話データがありません。")
        return

    print(f"\n{'='*80}")
    print(f"会話データ一覧 ({len(conversations)} 件)")
    print(f"{'='*80}\n")

    for conv in conversations:
        print(f"会話ID: {conv['id']}")
        print(f"メッセージ数: {conv['message_count']}")
        if conv['custom_prompt']:
            print(f"カスタムプロンプト: {conv['custom_prompt'][:50]}...")
        print(f"作成: {conv['created_at']}")
        print(f"更新: {conv['updated_at']}")
        print("-" * 80)


def show_conversation(conversation_id: int):
    """特定の会話の詳細を表示"""
    storage = get_storage()
    conv = storage.load_conversation(conversation_id)

    if not conv:
        print(f"会話ID {conversation_id} が見つかりません。")
        return

    print(f"\n{'='*80}")
    print(f"会話ID: {conv['conversation_id']}")
    print(f"{'='*80}")
    print(f"作成: {conv['created_at']}")
    print(f"更新: {conv['updated_at']}")

    if conv['custom_prompt']:
        print(f"\nカスタムプロンプト:")
        print(f"  {conv['custom_prompt']}")

    if conv['ai_prompt']:
        print(f"\nAIプロンプト (最初の200文字):")
        print(f"  {conv['ai_prompt'][:200]}...")

    print(f"\n最新のAI応答:")
    print(f"  {conv['latest_ai_response'][:200]}...")

    print(f"\n{'='*80}")
    print(f"メッセージ ({len(conv['thread_data'])} 件)")
    print(f"{'='*80}\n")

    for i, msg in enumerate(conv['thread_data'], 1):
        bot_flag = " [BOT]" if msg.get('is_bot_reply') else ""
        print(f"{i}. {msg['account']}{bot_flag}")
        print(f"   {msg['content'][:100]}{'...' if len(msg['content']) > 100 else ''}")
        print(f"   {msg['created_at']}")
        print()


def main():
    if len(sys.argv) < 2:
        print("使用方法:")
        print("  python view_data.py list              - 全会話の一覧")
        print("  python view_data.py show <会話ID>    - 特定の会話の詳細")
        print("  python view_data.py latest            - 最新の会話の詳細")
        sys.exit(1)

    command = sys.argv[1]

    if command == "list":
        list_conversations()
    elif command == "show":
        if len(sys.argv) < 3:
            print("エラー: 会話IDを指定してください")
            sys.exit(1)
        conversation_id = int(sys.argv[2])
        show_conversation(conversation_id)
    elif command == "latest":
        storage = get_storage()
        conversations = storage.get_all_conversations(limit=1)
        if conversations:
            show_conversation(conversations[0]['id'])
        else:
            print("会話データがありません。")
    else:
        print(f"不明なコマンド: {command}")
        sys.exit(1)


if __name__ == '__main__':
    main()
