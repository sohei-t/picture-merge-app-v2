#!/bin/bash

# GCP Text-to-Speech セットアップスクリプト
# 音声生成機能を有効にするための設定

set -e

# カラー定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${BLUE}================================${NC}"
echo -e "${BLUE}🔊 GCP Text-to-Speech セットアップ${NC}"
echo -e "${BLUE}================================${NC}"

CURRENT_DIR=$(pwd)
CREDENTIALS_DIR="${CURRENT_DIR}/credentials"
KEY_FILE="${CREDENTIALS_DIR}/gcp-workflow-key.json"

# credentialsディレクトリを作成
mkdir -p "$CREDENTIALS_DIR"

# ======================
# 1. gcloud CLI の確認
# ======================
echo -e "\n${CYAN}1. gcloud CLI の確認${NC}"

if command -v gcloud &> /dev/null; then
    echo -e "${GREEN}✅ gcloud CLI がインストールされています${NC}"

    # 認証状態を確認
    if gcloud auth list --format="value(account)" | grep -q '@'; then
        ACCOUNT=$(gcloud auth list --filter=status:ACTIVE --format="value(account)")
        echo -e "${GREEN}✅ ログイン済み: $ACCOUNT${NC}"
    else
        echo -e "${YELLOW}⚠️  ログインが必要です${NC}"
        echo -e "${YELLOW}実行: gcloud auth login${NC}"
        exit 1
    fi

    # プロジェクトIDを確認
    PROJECT_ID=$(gcloud config get-value project 2>/dev/null)
    if [ -z "$PROJECT_ID" ]; then
        echo -e "${RED}❌ プロジェクトが設定されていません${NC}"
        echo "利用可能なプロジェクト:"
        gcloud projects list --format="table(projectId,name)"
        echo ""
        echo -e "${YELLOW}プロジェクトIDを入力してください:${NC}"
        read -p "> " PROJECT_ID
        gcloud config set project "$PROJECT_ID"
    fi
    echo -e "${GREEN}✅ プロジェクト: $PROJECT_ID${NC}"
else
    echo -e "${RED}❌ gcloud CLI がインストールされていません${NC}"
    echo ""
    echo "インストール方法:"
    echo "1. https://cloud.google.com/sdk/docs/install を開く"
    echo "2. お使いのOSに合わせてインストール"
    echo "3. gcloud init を実行"
    exit 1
fi

# ======================
# 2. Text-to-Speech API の有効化
# ======================
echo -e "\n${CYAN}2. Text-to-Speech API の有効化${NC}"

# APIが有効か確認
if gcloud services list --enabled --filter="name:texttospeech.googleapis.com" --format="value(name)" | grep -q "texttospeech"; then
    echo -e "${GREEN}✅ Text-to-Speech API は有効です${NC}"
else
    echo -e "${YELLOW}Text-to-Speech API を有効化しています...${NC}"
    gcloud services enable texttospeech.googleapis.com
    echo -e "${GREEN}✅ Text-to-Speech API を有効化しました${NC}"
fi

# ======================
# 3. サービスアカウントの作成
# ======================
echo -e "\n${CYAN}3. サービスアカウントの設定${NC}"

SERVICE_ACCOUNT_NAME="tts-service-account"
SERVICE_ACCOUNT_EMAIL="${SERVICE_ACCOUNT_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"

# サービスアカウントの存在確認
if gcloud iam service-accounts describe "$SERVICE_ACCOUNT_EMAIL" &>/dev/null; then
    echo -e "${GREEN}✅ サービスアカウントは既に存在します${NC}"
else
    echo -e "${YELLOW}サービスアカウントを作成しています...${NC}"
    gcloud iam service-accounts create "$SERVICE_ACCOUNT_NAME" \
        --display-name="Text-to-Speech Service Account" \
        --description="Service account for TTS API access"
    echo -e "${GREEN}✅ サービスアカウントを作成しました${NC}"
fi

# ======================
# 4. 権限の付与
# ======================
echo -e "\n${CYAN}4. 権限の付与${NC}"

# Text-to-Speech の権限を付与
echo -e "${YELLOW}Text-to-Speech の権限を付与しています...${NC}"

gcloud projects add-iam-policy-binding "$PROJECT_ID" \
    --member="serviceAccount:${SERVICE_ACCOUNT_EMAIL}" \
    --role="roles/cloudtts.viewer" &>/dev/null || true

echo -e "${GREEN}✅ 権限を付与しました${NC}"

# ======================
# 5. 認証キーの生成
# ======================
echo -e "\n${CYAN}5. 認証キーの生成${NC}"

if [ -f "$KEY_FILE" ]; then
    echo -e "${YELLOW}⚠️  認証キーファイルが既に存在します: $KEY_FILE${NC}"
    echo -e "${YELLOW}新しいキーを生成しますか？ (y/n)${NC}"
    read -p "> " REGENERATE

    if [ "$REGENERATE" != "y" ] && [ "$REGENERATE" != "Y" ]; then
        echo -e "${GREEN}既存のキーを使用します${NC}"
    else
        # バックアップを作成
        mv "$KEY_FILE" "${KEY_FILE}.backup.$(date +%Y%m%d_%H%M%S)"
        echo -e "${YELLOW}既存のキーをバックアップしました${NC}"

        # 新しいキーを生成
        gcloud iam service-accounts keys create "$KEY_FILE" \
            --iam-account="$SERVICE_ACCOUNT_EMAIL"
        echo -e "${GREEN}✅ 新しい認証キーを生成しました${NC}"
    fi
else
    echo -e "${YELLOW}認証キーを生成しています...${NC}"
    gcloud iam service-accounts keys create "$KEY_FILE" \
        --iam-account="$SERVICE_ACCOUNT_EMAIL"
    echo -e "${GREEN}✅ 認証キーを生成しました: $KEY_FILE${NC}"
fi

# ======================
# 6. 環境変数の設定
# ======================
echo -e "\n${CYAN}6. 環境変数の設定${NC}"

# .env ファイルに追加
if [ -f ".env" ]; then
    if grep -q "GOOGLE_APPLICATION_CREDENTIALS" .env; then
        echo -e "${YELLOW}環境変数は既に設定されています${NC}"
    else
        echo "GOOGLE_APPLICATION_CREDENTIALS=\"$KEY_FILE\"" >> .env
        echo -e "${GREEN}✅ .env ファイルに環境変数を追加しました${NC}"
    fi
else
    cat > .env << EOF
# Google Cloud Platform
GOOGLE_APPLICATION_CREDENTIALS="$KEY_FILE"
PROJECT_ID="$PROJECT_ID"
EOF
    echo -e "${GREEN}✅ .env ファイルを作成しました${NC}"
fi

# ======================
# 7. Node.js パッケージのインストール
# ======================
echo -e "\n${CYAN}7. Node.js パッケージの確認${NC}"

if [ -f "package.json" ]; then
    if grep -q "@google-cloud/text-to-speech" package.json; then
        echo -e "${GREEN}✅ @google-cloud/text-to-speech は既に package.json に含まれています${NC}"
    else
        echo -e "${YELLOW}package.json に依存関係を追加しています...${NC}"
        npm install --save @google-cloud/text-to-speech
        echo -e "${GREEN}✅ 依存関係を追加しました${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  package.json が見つかりません${NC}"
    echo "プロジェクトで npm install @google-cloud/text-to-speech を実行してください"
fi

# ======================
# 8. テスト音声の生成
# ======================
echo -e "\n${CYAN}8. テスト音声の生成${NC}"

# テスト用スクリプトを作成
cat > test_tts.js << 'EOF'
const textToSpeech = require('@google-cloud/text-to-speech');
const fs = require('fs');
const util = require('util');

async function testTTS() {
    const client = new textToSpeech.TextToSpeechClient();

    const text = 'こんにちは。Google Cloud Text-to-Speech のテストです。正常に動作しています。';

    const request = {
        input: {text: text},
        voice: {
            languageCode: 'ja-JP',
            name: 'ja-JP-Neural2-D',
            ssmlGender: 'NEUTRAL'
        },
        audioConfig: {
            audioEncoding: 'MP3'
        },
    };

    try {
        const [response] = await client.synthesizeSpeech(request);
        const writeFile = util.promisify(fs.writeFile);
        await writeFile('test_audio.mp3', response.audioContent, 'binary');
        console.log('✅ テスト音声を生成しました: test_audio.mp3');
        console.log('🔊 音声ファイルを再生して確認してください');
    } catch (error) {
        console.error('❌ エラー:', error.message);
    }
}

testTTS();
EOF

echo -e "${YELLOW}テスト音声を生成しますか？ (y/n)${NC}"
read -p "> " TEST_AUDIO

if [ "$TEST_AUDIO" = "y" ] || [ "$TEST_AUDIO" = "Y" ]; then
    if command -v node &> /dev/null; then
        export GOOGLE_APPLICATION_CREDENTIALS="$KEY_FILE"
        node test_tts.js

        if [ -f "test_audio.mp3" ]; then
            echo -e "${GREEN}✅ テスト音声の生成に成功しました！${NC}"

            # macOSの場合は自動再生
            if [ "$(uname)" = "Darwin" ]; then
                echo -e "${YELLOW}音声を再生しています...${NC}"
                afplay test_audio.mp3 2>/dev/null || true
            fi
        fi
    else
        echo -e "${YELLOW}Node.js がインストールされていないため、テストをスキップします${NC}"
    fi
fi

# ======================
# 完了メッセージ
# ======================
echo -e "\n${BLUE}================================${NC}"
echo -e "${GREEN}✅ セットアップ完了！${NC}"
echo -e "${BLUE}================================${NC}"

echo -e "\n${GREEN}設定内容:${NC}"
echo -e "  プロジェクトID: ${PROJECT_ID}"
echo -e "  サービスアカウント: ${SERVICE_ACCOUNT_EMAIL}"
echo -e "  認証キー: ${KEY_FILE}"

echo -e "\n${GREEN}使い方:${NC}"
echo -e "  1. プロジェクトで: npm install @google-cloud/text-to-speech"
echo -e "  2. スクリプト実行: node generate_audio_gcp.js"
echo -e "  または"
echo -e "  3. npm run generate-audio:gcp"

echo -e "\n${YELLOW}⚠️  重要な注意事項:${NC}"
echo -e "  - 認証キーファイル（${KEY_FILE}）は機密情報です"
echo -e "  - .gitignore に credentials/ を追加してください"
echo -e "  - キーを他人と共有しないでください"

# .gitignore に追加
if [ -f ".gitignore" ]; then
    if ! grep -q "credentials/" .gitignore; then
        echo -e "\n# GCP credentials" >> .gitignore
        echo "credentials/" >> .gitignore
        echo "*.json" >> .gitignore
        echo "test_audio.mp3" >> .gitignore
        echo -e "${GREEN}✅ .gitignore に credentials/ を追加しました${NC}"
    fi
else
    cat > .gitignore << EOF
# GCP credentials
credentials/
*.json

# Audio files
test_audio.mp3
explanation.mp3

# Node
node_modules/
npm-debug.log*

# Environment
.env
.env.local

# OS
.DS_Store
Thumbs.db
EOF
    echo -e "${GREEN}✅ .gitignore を作成しました${NC}"
fi

echo -e "\n${GREEN}準備が整いました！音声生成機能が利用可能です。${NC}"