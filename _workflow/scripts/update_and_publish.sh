#!/bin/bash
# コード修正後の自動公開スクリプト
# DELIVERYフォルダのみをGitHubに公開

set -e

# カラー定義
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}================================${NC}"
echo -e "${BLUE}🔄 コード更新・公開プロセス${NC}"
echo -e "${BLUE}================================${NC}"
echo ""

# 現在のディレクトリチェック
CURRENT_DIR=$(pwd)
if [[ ! "$CURRENT_DIR" == *"worktrees/mission"* ]]; then
    echo -e "${YELLOW}⚠️  worktreeディレクトリで実行してください${NC}"
    echo -e "   例: cd worktrees/mission-v1"
    exit 1
fi

# プロジェクトルート取得
PROJECT_ROOT=$(dirname $(dirname $CURRENT_DIR))

echo -e "${GREEN}📍 作業ディレクトリ: $CURRENT_DIR${NC}"
echo -e "${GREEN}📍 プロジェクトルート: $PROJECT_ROOT${NC}"
echo ""

# 1. テスト実行
echo -e "${YELLOW}1. テスト実行中...${NC}"
if [ -f "package.json" ]; then
    if npm test; then
        echo -e "${GREEN}✅ テスト成功${NC}"
    else
        echo -e "${RED}❌ テスト失敗。修正してください${NC}"
        exit 1
    fi
elif [ -f "test_app.py" ] || [ -f "tests.py" ]; then
    if python3 -m pytest; then
        echo -e "${GREEN}✅ テスト成功${NC}"
    else
        echo -e "${RED}❌ テスト失敗。修正してください${NC}"
        exit 1
    fi
else
    echo -e "${YELLOW}⚠️  テストファイルが見つかりません。スキップします${NC}"
fi
echo ""

# 2. DELIVERY作成
echo -e "${YELLOW}2. DELIVERYフォルダ作成中...${NC}"
if python3 $PROJECT_ROOT/_workflow/src/delivery_organizer.py; then
    echo -e "${GREEN}✅ DELIVERY作成成功${NC}"
else
    echo -e "${RED}❌ DELIVERY作成失敗${NC}"
    exit 1
fi
echo ""

# 3. 公開タイプ選択
echo -e "${YELLOW}3. 公開タイプを選択してください:${NC}"
echo "  [1] 新規公開（初回）"
echo "  [2] 更新公開（2回目以降）"
read -p "選択 (1/2): " PUBLISH_TYPE

if [ "$PUBLISH_TYPE" = "2" ]; then
    UPDATE_FLAG="--update"
    echo -e "${GREEN}✓ 更新として公開します${NC}"
else
    UPDATE_FLAG=""
    echo -e "${GREEN}✓ 新規として公開します${NC}"
fi
echo ""

# 4. GitHub公開
echo -e "${YELLOW}4. GitHubに公開中...${NC}"
echo -e "${BLUE}対象: https://github.com/sohei-t/ai-agent-portfolio${NC}"

if python3 $PROJECT_ROOT/_workflow/src/github_publisher_v8.py $UPDATE_FLAG; then
    echo -e "${GREEN}✅ GitHub公開成功${NC}"
else
    echo -e "${RED}❌ GitHub公開失敗${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}================================${NC}"
echo -e "${GREEN}✅ 更新・公開完了！${NC}"
echo -e "${GREEN}================================${NC}"
echo ""
echo -e "${BLUE}次のステップ:${NC}"
echo "1. GitHub Pagesで動作確認"
echo "2. READMEのリンク確認"
echo "3. about.htmlの表示確認"
echo ""