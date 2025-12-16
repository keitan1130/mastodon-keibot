# Keibot - Mastodon AI Bot

Mastodonのメンションに自動返信するAIボットです。

**GitHub**: https://github.com/keitan1130/mastodon-keibot

## プロジェクト構造

```
mastodon-keibot/
├── .env.example        # 環境変数サンプル
├── view_data.py        # 会話データ確認ユーティリティ
├── data/               # 会話データ（SQLite DB）
└── src/
    ├── __init__.py     # パッケージ初期化
    ├── config.py       # 設定と環境変数
    ├── utils.py        # ユーティリティ関数（HTML除去、Markdown除去、Snowflake ID生成）
    ├── storage.py      # 会話データの保存（SQLite）
    ├── fetcher.py      # スレッドコンテキストの取得
    ├── processor.py    # プロンプト構築と処理
    ├── llm_interface.py # LLM（Ollama）との通信
    ├── poster.py       # Mastodonへの投稿処理
    ├── bot.py          # StreamListenerとメインボットロジック
    └── main.py         # メインエントリーポイント
```

## モジュール説明

### config.py
- `.env` ファイルからの環境変数読み込み
- API設定（Mastodon URL、アクセストークン）
- Ollamaモデル設定（デフォルト: `gemma3:27b`）
- 返信の公開設定（`KEIBOT_VISIBILITY`）
- データディレクトリパス
- デフォルトキャラクタープロンプト

### utils.py
- `strip_html()`: HTMLタグを除去
- `remove_markdown()`: Markdownフォーマットを除去（JSON、コードブロック、太字等）
- `split_into_segments()`: テキストを投稿用に分割（400文字制限）
- `extract_custom_prompt()`: `/*プロンプト*/` 形式のカスタムプロンプトを抽出
- `SnowflakeGenerator`: Snowflake IDの生成

### storage.py
- `ConversationStorage`: SQLiteベースの会話データ管理
  - 会話の保存・読み込み
  - ステータスIDからの会話検索
  - メッセージ履歴の管理
  - 全会話一覧の取得

### fetcher.py
- `get_thread_context()`: スレッドの祖先・子孫を取得
- `get_full_thread()`: 完全なスレッドを取得
- `get_status()`: 単一ステータスを取得
- `get_account_info()`: 認証済みアカウント情報を取得

### processor.py
- `PromptProcessor`: プロンプト処理
  - アクティブプロンプトの決定（カスタム→既存→デフォルト）
  - システムプロンプトの構築
  - 会話プロンプトの構築
- `clean_content_for_log()`: @mention や番号プレフィックスを除去

### llm_interface.py
- `OllamaInterface`: LLM（Ollama）との通信
  - システムプロンプトの設定・取得
  - テキスト生成
  - Markdown除去済み応答の取得（`generate_clean()`）
- シングルトンインスタンス（`get_llm()`）

### poster.py
- `MastodonPoster`: 投稿処理
  - 単一ステータスの投稿
  - スレッド返信の投稿（自動分割、番号付け）
  - お気に入り・ブースト

### bot.py
- `MentionBot`: メンション処理ボット
  - メンション通知の処理
  - スレッドコンテキストの取得
  - 会話ID管理（新規生成/既存検索）
  - 公開設定の決定（`follow`オプション対応）
- `create_client()`: Mastodonクライアント作成

### main.py
- 設定の検証
- 起動メッセージの投稿
- ボットの起動とストリーム監視

## 環境構築

### 必要な環境

- Python 3.9以上
- Ollama（ローカルLLM）
- Mastodonアカウントとアクセストークン

### 手順1: リポジトリのクローン

```bash
git clone https://github.com/keitan1130/mastodon-keibot.git
cd mastodon-keibot
```

### 手順2: Python仮想環境の作成

```bash
# 仮想環境を作成
python3 -m venv .venv

# 仮想環境を有効化
# Linux/Mac の場合:
source .venv/bin/activate

# Windows の場合:
# .venv\Scripts\activate
```

### 手順3: Pythonパッケージのインストール

仮想環境が有効化されている状態で実行：

```bash
pip install Mastodon.py ollama
```

### 手順4: Ollamaのインストール

Ollamaをインストールしていない場合は、[公式サイト](https://ollama.ai/)からインストールしてください。

**Linuxの場合:**
```bash
curl -fsSL https://ollama.ai/install.sh | sh
```

**Macの場合:**
- https://ollama.ai/download からダウンロードしてインストール

**Windowsの場合:**
- https://ollama.ai/download からダウンロードしてインストール

### 手順5: Ollamaの起動

**Mac/Windowsの場合**: GUIインストーラーを使用すると自動的にバックグラウンドで起動します。この手順はスキップできます。

**Linuxの場合**: インストール後、まず自動起動を無効化してから手動で起動します。

```bash
# 自動起動をオフにする
sudo systemctl disable ollama
sudo systemctl stop ollama

# 手動でOllamaサーバーを起動（別ターミナル推奨）
ollama serve
```

※ `ollama serve` は実行したままにしておく必要があります

Ollamaが起動しているか確認：
```bash
ollama list
```
エラーが出なければ起動しています。

**（参考）自動起動したい場合:**
```bash
# systemdサービスとして有効化・起動
sudo systemctl enable ollama
sudo systemctl start ollama

# 状態確認
sudo systemctl status ollama
```

### 手順6: AIモデルのダウンロード

Ollamaが起動している状態で、別のターミナルで実行：

```bash
ollama pull gemma3:27b
```

他のモデルを使用する場合は、環境変数 `OLLAMA_MODEL` で指定できます。

利用可能なモデル例：
- `gemma3:27b`（デフォルト）
- `llama3.2`
- `mistral`
- `qwen2.5`
- `gemma3:270m`

### 手順7: Mastodonアクセストークンの取得

1. Mastodonインスタンスにログイン
2. 設定 → 開発 → 新しいアプリケーション
3. アプリケーション名を入力（例: Keibot）
4. 必要な権限を選択：
   - `read`
   - `profile`
   - `write:favourites`
   - `write:statuses`
   - `write:media`
5. 「送信」をクリック
6. 作成されたアプリケーションをクリックして詳細を開く
7. 「アクセストークン」をコピー

### 手順8: ディレクトリ作成

```bash
mkdir -p data
```

### 手順9: 環境変数の設定

`.env.example` をコピーして `.env` を作成：

```bash
cp .env.example .env
```

`.env` ファイルを編集：

```dotenv
# 必須
MASTODON_API_BASE_URL=https://your-mastodon-instance.com
MASTODON_ACCESS_TOKEN=your-access-token-here

# オプション
OLLAMA_MODEL=gemma3:27b
KEIBOT_DATA_DIR=/path/to/data
KEIBOT_VISIBILITY=follow  # public, unlisted, private, direct, follow
```

### 手順10: ボットの起動

仮想環境が有効化されていることを確認してから実行：

```bash
python3 -m src.main
```

ボットが正常に起動すると、Mastodonに起動メッセージが投稿されます。

## 日常的な使用方法

### ボットの起動手順

1. 仮想環境を有効化：
```bash
source .venv/bin/activate  # Linux/Mac
# または .venv\Scripts\activate  # Windows
```

2. **Linuxの場合**: 別ターミナルでOllamaを起動：
```bash
ollama serve
```
※ Mac/Windowsで自動起動している場合はスキップ

3. ボットを起動：
```bash
python3 -m src.main
```

### ボットの停止

Ctrl+C でボットを停止できます。

### 会話データ確認

```bash
# 全会話一覧
python3 view_data.py

# 特定の会話詳細
python3 view_data.py <conversation_id>

# 最新の会話詳細
python3 view_data.py latest
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
複数行にも対応しています。

例：
```
@keibot こんにちは！ /*クールな口調で話して*/
```

```
@keibot /*
関西弁で話してください。
明るい性格で！
*/ 調子どう？
```

## 返信の公開設定

環境変数 `KEIBOT_VISIBILITY` で返信の公開設定を制御できます：

- `public`: 公開
- `unlisted`: 未収載
- `private`: フォロワー限定
- `direct`: ダイレクトメッセージ
- `follow`: 相手の投稿の公開設定に合わせる（デフォルト）

## 依存関係

- `Mastodon.py`: Mastodon APIクライアント
- `ollama`: Ollama Python クライアント（LLMとの通信）
