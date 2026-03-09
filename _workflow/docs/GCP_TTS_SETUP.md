# 🔊 音声生成（TTS）設定ガイド

## 📌 概要

音声解説（explanation.mp3）を生成するための設定ガイドです。

**推奨**: Gemini 2.5 Flash Preview TTS（APIキーのみで利用可能）
**フォールバック**: Google Cloud Text-to-Speech（サービスアカウント必要）

## 🎯 推奨: Gemini TTS（3ステップで完了）

### なぜ Gemini TTS を推奨するのか

| 項目 | Gemini TTS | GCP TTS |
|------|-----------|---------|
| 認証方式 | APIキーのみ | サービスアカウント |
| セットアップ | 3ステップ | 10+ステップ |
| 音声品質 | 非常に高品質 | 高品質 |
| SSML | 不要（自然言語で間を認識） | 必要 |
| コスト | 無料枠あり | 従量課金 |

### 設定手順

#### ステップ1: APIキーを取得

1. [Google AI Studio](https://makersuite.google.com/app/apikey) にアクセス
2. Googleアカウントでログイン
3. **Create API Key** をクリック
4. APIキーをコピー

#### ステップ2: 環境変数に設定

```bash
# 方法A: 直接設定（現在のセッションのみ）
export GEMINI_API_KEY='AIzaSy...'

# 方法B: グローバル設定ファイルに追加（永続化・推奨）
echo "GEMINI_API_KEY=AIzaSy..." >> ~/.config/ai-agents/profiles/default.env
```

#### ステップ3: 依存関係をインストール

```bash
# Python パッケージ
pip install google-genai pydub

# ffmpeg（pydubがMP3変換に使用）
brew install ffmpeg  # macOS
```

### 動作確認

```bash
python3 << 'EOF'
import os
from dotenv import load_dotenv
from pathlib import Path

# 環境変数読み込み
global_env = Path.home() / ".config" / "ai-agents" / "profiles" / "default.env"
if global_env.exists():
    load_dotenv(global_env)

from google import genai

api_key = os.environ.get('GEMINI_API_KEY')
if api_key:
    client = genai.Client(api_key=api_key)
    print("✅ Gemini API 接続OK")
else:
    print("❌ GEMINI_API_KEY が設定されていません")
EOF
```

---

## 🔧 フォールバック: GCP Text-to-Speech

Gemini APIキーが設定されていない場合、自動的にGCP TTSにフォールバックします。

### 設定手順

#### 1. Google Cloud Console でプロジェクト作成

1. [Google Cloud Console](https://console.cloud.google.com) にアクセス
2. 新しいプロジェクトを作成（または既存のプロジェクトを使用）
3. プロジェクトIDをメモ

#### 2. Text-to-Speech API を有効化

```bash
# gcloud CLIを使用する場合
gcloud services enable texttospeech.googleapis.com

# または、Consoleから：
# 1. 「APIとサービス」→「ライブラリ」
# 2. 「Cloud Text-to-Speech API」を検索
# 3. 「有効にする」をクリック
```

#### 3. サービスアカウントキーの作成

##### Console から作成する方法：

1. 「IAMと管理」→「サービスアカウント」
2. 「サービスアカウントを作成」
3. 以下の情報を入力：
   - 名前: `tts-agent`
   - ID: `tts-agent`
   - 説明: `Text-to-Speech for AI Agent`
4. 「作成して続行」
5. ロール: `Cloud Text-to-Speech 管理者`
6. 「続行」→「完了」
7. 作成したサービスアカウントをクリック
8. 「キー」タブ→「鍵を追加」→「新しい鍵を作成」
9. 形式: JSON
10. ダウンロードされたファイルを保存

##### gcloud CLI から作成する方法：

```bash
# サービスアカウント作成
gcloud iam service-accounts create tts-agent \
  --display-name="Text-to-Speech Agent"

# 権限付与
gcloud projects add-iam-policy-binding [PROJECT_ID] \
  --member="serviceAccount:tts-agent@[PROJECT_ID].iam.gserviceaccount.com" \
  --role="roles/cloudtts.admin"

# キー作成
gcloud iam service-accounts keys create ~/Downloads/gcp-workflow-key.json \
  --iam-account=tts-agent@[PROJECT_ID].iam.gserviceaccount.com
```

#### 4. 認証ファイルの配置

```bash
# ディレクトリ作成
mkdir -p ~/.config/ai-agents/credentials/gcp/

# ダウンロードしたキーファイルを配置
mv ~/Downloads/[ダウンロードしたファイル名].json \
   ~/.config/ai-agents/credentials/gcp/default.json

# 権限設定
chmod 600 ~/.config/ai-agents/credentials/gcp/default.json
```

---

## 📊 料金について

### Gemini TTS
- 無料枠あり（詳細は[Google AI Studio](https://makersuite.google.com/)で確認）

### GCP TTS（フォールバック）
- **WaveNet音声**: 100万文字/月まで無料
- **Neural2音声**: 100万文字/月まで無料
- 通常のアプリ説明（500-1000文字）では月1000プロジェクトでも無料枠内

---

## 🔒 セキュリティ注意事項

1. **認証ファイルをGitHubにpushしない**
   ```bash
   # .gitignoreに追加
   echo "credentials/" >> .gitignore
   echo "*.json" >> .gitignore
   ```

2. **認証ファイルは安全に保管**
   - バックアップを取る
   - 他人と共有しない
   - 定期的にローテーション

---

## 🎯 音声なしでも問題ない理由

1. **about.html**: ビジュアルで内容を説明
2. **README.md**: 技術詳細を記載
3. **GitHub Pages**: ライブデモで実際に体験可能

音声はあくまで**追加の価値**であり、なくてもポートフォリオとしては十分機能します。

---

## 🆘 トラブルシューティング

### Gemini TTS エラー

```bash
# GEMINI_API_KEY確認
python3 -c "import os; print('GEMINI_API_KEY:', 'Set' if os.environ.get('GEMINI_API_KEY') else 'Not set')"

# 環境変数ファイル確認
cat ~/.config/ai-agents/profiles/default.env | grep GEMINI
```

### GCP TTS エラー

```bash
# 認証ファイルの存在確認
ls -la ~/.config/ai-agents/credentials/gcp/default.json

# ファイルの中身確認（JSONフォーマットか）
cat ~/.config/ai-agents/credentials/gcp/default.json | python -m json.tool
```

---

## 📝 まとめ

- **推奨**: Gemini TTS（APIキーのみで簡単設定）
- **フォールバック**: GCP TTS（サービスアカウント必要）
- **音声生成は必須ではありません**
- どちらも未設定の場合は自動的にスキップ
- ポートフォリオの価値は音声なしでも十分伝わります
