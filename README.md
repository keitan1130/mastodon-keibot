# Keibot - Mastodon AI Bot

Mastodonのメンションに自動返信するAIボットです。

## プロジェクト構造

```
mastodon-keibot/
├── keibot.py           # エントリーポイント（後方互換性のため維持）
├── data/               # 会話データ（SQLite DB）
└── src/
    ├── __init__.py     # パッケージ初期化
    ├── config.py       # 設定と環境変数
    ├── utils.py        # ユーティリティ関数（HTML除去、Markdown除去、Snowflake ID生成）
    ├── storage.py      # 会話データの保存（SQLite）
    ├── fetcher.py      # スレッドコンテキストの取得
    ├── processor.py    # プロンプト構築と処理
    ├── llm_interface.py # Gemini CLIとの通信
    ├── poster.py       # Mastodonへの投稿処理
    ├── bot.py          # StreamListenerとメインボットロジック
    └── main.py         # メインエントリーポイント
```

## モジュール説明

### config.py
- 環境変数の読み込み
- API設定（Mastodon URL、アクセストークン）
- データディレクトリパス
- デフォルトキャラクタープロンプト

### utils.py
- `strip_html()`: HTMLタグを除去
- `remove_markdown()`: Markdownフォーマットを除去
- `split_into_segments()`: テキストを投稿用に分割
- `extract_custom_prompt()`: カスタムプロンプトを抽出
- `SnowflakeGenerator`: Snowflake IDの生成

### storage.py
- `ConversationStorage`: SQLiteベースの会話データ管理
  - 会話の保存・読み込み
  - ステータスIDからの会話検索
  - メッセージ履歴の管理

### fetcher.py
- `get_thread_context()`: スレッドの祖先・子孫を取得
- `get_full_thread()`: 完全なスレッドを取得
- `get_status()`: 単一ステータスを取得

### processor.py
- `PromptProcessor`: プロンプト処理
  - アクティブプロンプトの決定
  - システムプロンプトの構築
  - 会話プロンプトの構築

### llm_interface.py
- `GeminiInterface`: Gemini CLIとの通信
  - システムプロンプトの更新（GEMINI.md）
  - テキスト生成
  - Markdown除去済み応答の取得

### poster.py
- `MastodonPoster`: 投稿処理
  - 単一ステータスの投稿
  - スレッド返信の投稿
  - お気に入り・ブースト

### bot.py
- `MentionBot`: メンション処理ボット
- `create_client()`: Mastodonクライアント作成

### main.py
- ボットの起動処理

## 使用方法

```bash
# 環境変数を設定
export MASTODON_API_BASE_URL="https://your-mastodon-instance.com"
export MASTODON_ACCESS_TOKEN="your-access-token"

# ボットを起動
python keibot.py
# または
python -m src.main
```

## 会話データ

会話データはSQLiteデータベース（`data/conversations.db`）に保存されます。

### テーブル構造

**conversations**
- `id`: 会話ID（Snowflake ID）
- `custom_prompt`: カスタムプロンプト
- `ai_prompt`: 使用されたAIプロンプト
- `latest_ai_response`: 最新のAI応答
- `created_at`: 作成日時
- `updated_at`: 更新日時

**messages**
- `id`: メッセージID
- `conversation_id`: 会話ID
- `status_id`: MastodonステータスID
- `account`: アカウント名
- `content`: 内容
- `url`: ステータスURL
- `is_bot_reply`: ボットの返信かどうか
- `created_at`: 作成日時

## カスタムプロンプト

投稿内に `/*ここにプロンプト*/` 形式でカスタムプロンプトを指定できます。

例：
```
@keibot こんにちは！ /*クールな口調で話して*/
```

## 依存関係

- `Mastodon.py`: Mastodon APIクライアント
- `gemini` CLI: Gemini AI（外部コマンド）
