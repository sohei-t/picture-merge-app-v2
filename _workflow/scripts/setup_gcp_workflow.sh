#!/bin/bash
# GCPワークフロー専用プロジェクトのセットアップスクリプト
# 使用方法: ./setup_gcp_workflow.sh

set -e

# カラー定義
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}================================${NC}"
echo -e "${BLUE}🚀 GCPワークフロー環境セットアップ${NC}"
echo -e "${BLUE}================================${NC}"
echo ""

PROJECT_ID="ai-agent-workflow-2024"
SERVICE_ACCOUNT_NAME="ai-agent-workflow-sa"
CREDENTIALS_DIR="$HOME/Desktop/git-worktree-agent/_workflow/credentials"
KEY_FILE="$CREDENTIALS_DIR/gcp-workflow-key.json"

# Step 1: プロジェクト確認
echo -e "${YELLOW}Step 1: プロジェクト確認...${NC}"
gcloud config set project $PROJECT_ID
echo -e "${GREEN}✅ プロジェクト: $PROJECT_ID${NC}"
echo ""

# Step 2: 請求先アカウント確認
echo -e "${YELLOW}Step 2: 請求先アカウント確認...${NC}"
BILLING_ACCOUNT=$(gcloud billing projects describe $PROJECT_ID --format="value(billingAccountName)" 2>/dev/null || echo "")

if [ -z "$BILLING_ACCOUNT" ]; then
    echo -e "${RED}❌ 請求先アカウントがリンクされていません${NC}"
    echo ""
    echo -e "${YELLOW}以下のURLで請求先アカウントをリンクしてください:${NC}"
    echo "https://console.cloud.google.com/billing/linkedaccount?project=$PROJECT_ID"
    echo ""
    echo "リンク後、このスクリプトを再実行してください。"
    exit 1
else
    echo -e "${GREEN}✅ 請求先アカウント: $BILLING_ACCOUNT${NC}"
fi
echo ""

# Step 3: 必要なAPIを有効化
echo -e "${YELLOW}Step 3: 必要なAPIを有効化中...${NC}"
echo "これには数分かかる場合があります..."

# 課金不要のAPIのみ先に有効化
gcloud services enable \
  cloudresourcemanager.googleapis.com \
  serviceusage.googleapis.com \
  iam.googleapis.com \
  --project=$PROJECT_ID

# 課金が必要なAPIを有効化（請求先アカウントがある場合のみ成功）
if gcloud services enable \
  aiplatform.googleapis.com \
  texttospeech.googleapis.com \
  storage.googleapis.com \
  --project=$PROJECT_ID 2>/dev/null; then
    echo -e "${GREEN}✅ すべてのAPIを有効化しました${NC}"
else
    echo -e "${RED}❌ 一部のAPIの有効化に失敗しました（請求先アカウント未設定の可能性）${NC}"
    echo -e "${YELLOW}以下のURLで請求先アカウントをリンクしてください:${NC}"
    echo "https://console.cloud.google.com/billing/linkedaccount?project=$PROJECT_ID"
    echo ""
    echo "リンク後、以下のコマンドでAPIを有効化してください:"
    echo "gcloud services enable aiplatform.googleapis.com texttospeech.googleapis.com storage.googleapis.com --project=$PROJECT_ID"
fi
echo ""

# Step 4: サービスアカウント作成
echo -e "${YELLOW}Step 4: サービスアカウント作成...${NC}"

# 既存確認
EXISTING_SA=$(gcloud iam service-accounts list \
  --filter="email:$SERVICE_ACCOUNT_NAME@$PROJECT_ID.iam.gserviceaccount.com" \
  --format="value(email)" 2>/dev/null || echo "")

if [ -z "$EXISTING_SA" ]; then
    gcloud iam service-accounts create $SERVICE_ACCOUNT_NAME \
      --display-name="AI Agent Workflow Service Account" \
      --description="ワークフロー実行用のサービスアカウント（画像生成・音声生成）"
    echo -e "${GREEN}✅ サービスアカウント作成完了${NC}"
else
    echo -e "${GREEN}✅ サービスアカウント既存: $EXISTING_SA${NC}"
fi

SA_EMAIL="$SERVICE_ACCOUNT_NAME@$PROJECT_ID.iam.gserviceaccount.com"
echo ""

# Step 5: 必要な権限を付与
echo -e "${YELLOW}Step 5: 権限付与中...${NC}"

# Vertex AI（Imagen）用
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:$SA_EMAIL" \
  --role="roles/aiplatform.user" \
  --condition=None

# Text-to-Speech用
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:$SA_EMAIL" \
  --role="roles/cloudtts.admin" \
  --condition=None

# Storage用（画像/音声の保存）
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:$SA_EMAIL" \
  --role="roles/storage.objectAdmin" \
  --condition=None

echo -e "${GREEN}✅ 権限付与完了${NC}"
echo ""

# Step 6: 認証キー作成
echo -e "${YELLOW}Step 6: 認証キー作成...${NC}"

# credentialsディレクトリ作成
mkdir -p "$CREDENTIALS_DIR"

# 既存キー削除（再作成）
if [ -f "$KEY_FILE" ]; then
    echo -e "${YELLOW}⚠️  既存のキーを削除します${NC}"
    rm "$KEY_FILE"
fi

# 新しいキー作成
gcloud iam service-accounts keys create "$KEY_FILE" \
  --iam-account="$SA_EMAIL"

# 権限設定（自分だけ読み書き可能）
chmod 600 "$KEY_FILE"

echo -e "${GREEN}✅ 認証キー作成完了: $KEY_FILE${NC}"
echo ""

# Step 7: .envファイル更新
echo -e "${YELLOW}Step 7: .env設定...${NC}"

ENV_FILE="$HOME/Desktop/git-worktree-agent/_workflow/.env"
ENV_TEMPLATE="$HOME/Desktop/git-worktree-agent/_workflow/.env.template"

# .env.templateをコピー（存在しない場合）
if [ ! -f "$ENV_FILE" ] && [ -f "$ENV_TEMPLATE" ]; then
    cp "$ENV_TEMPLATE" "$ENV_FILE"
    echo -e "${GREEN}✅ .envファイル作成${NC}"
fi

# 設定を更新
if [ -f "$ENV_FILE" ]; then
    # GCPプロジェクトID
    if grep -q "^GCP_PROJECT_ID=" "$ENV_FILE"; then
        sed -i '' "s|^GCP_PROJECT_ID=.*|GCP_PROJECT_ID=$PROJECT_ID|g" "$ENV_FILE"
    else
        echo "GCP_PROJECT_ID=$PROJECT_ID" >> "$ENV_FILE"
    fi

    # 認証キーパス
    if grep -q "^GOOGLE_APPLICATION_CREDENTIALS=" "$ENV_FILE"; then
        sed -i '' "s|^GOOGLE_APPLICATION_CREDENTIALS=.*|GOOGLE_APPLICATION_CREDENTIALS=$KEY_FILE|g" "$ENV_FILE"
    else
        echo "GOOGLE_APPLICATION_CREDENTIALS=$KEY_FILE" >> "$ENV_FILE"
    fi

    echo -e "${GREEN}✅ .env設定更新完了${NC}"
else
    echo -e "${YELLOW}⚠️  .envファイルが見つかりません${NC}"
fi
echo ""

# Step 8: 動作確認
echo -e "${YELLOW}Step 8: 動作確認...${NC}"

# 環境変数設定
export GOOGLE_APPLICATION_CREDENTIALS="$KEY_FILE"

# APIが有効化されているか確認
echo "有効化されているAPIを確認中..."
gcloud services list --enabled | grep -E "aiplatform|texttospeech"

echo ""
echo -e "${BLUE}================================${NC}"
echo -e "${GREEN}✅ セットアップ完了！${NC}"
echo -e "${BLUE}================================${NC}"
echo ""
echo -e "${GREEN}プロジェクト: $PROJECT_ID${NC}"
echo -e "${GREEN}サービスアカウント: $SA_EMAIL${NC}"
echo -e "${GREEN}認証キー: $KEY_FILE${NC}"
echo ""
echo -e "${YELLOW}次のステップ:${NC}"
echo "1. ワークフローを実行してください"
echo "2. 画像生成・音声生成が自動的に動作します"
echo ""
echo -e "${BLUE}コスト目安:${NC}"
echo "  - 画像生成（Imagen）: $0.02/枚"
echo "  - 音声生成（TTS）: $4/100万文字"
echo "  - 100枚の画像 + 音声: 約$2-3/アプリ"
echo ""
