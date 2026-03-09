#!/bin/bash

# 完成物検証スクリプト
# フェーズ5の成果物が正しく生成されているか確認

set -e

# カラー定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${BLUE}================================${NC}"
echo -e "${BLUE}📋 完成物検証${NC}"
echo -e "${BLUE}================================${NC}"

# 引数チェック
if [ $# -eq 0 ]; then
    echo -e "${YELLOW}使用方法: $0 <worktree_path>${NC}"
    echo -e "${YELLOW}例: $0 ./worktrees/mission-todo-app${NC}"
    exit 1
fi

WORKTREE_PATH="$1"

if [ ! -d "$WORKTREE_PATH" ]; then
    echo -e "${RED}❌ ディレクトリが存在しません: $WORKTREE_PATH${NC}"
    exit 1
fi

cd "$WORKTREE_PATH"

echo -e "\n${CYAN}プロジェクトディレクトリ: $(pwd)${NC}"

# 検証結果を記録
PASS_COUNT=0
FAIL_COUNT=0
TOTAL_COUNT=0

# 検証関数
check_file() {
    local file="$1"
    local description="$2"
    local optional="$3"

    ((TOTAL_COUNT++))

    if [ -f "$file" ]; then
        echo -e "${GREEN}✅ $description${NC}"
        echo -e "   ファイル: $file"
        echo -e "   サイズ: $(ls -lh "$file" | awk '{print $5}')"
        ((PASS_COUNT++))
    else
        if [ "$optional" = "optional" ]; then
            echo -e "${YELLOW}⚠️  $description (オプション)${NC}"
            ((PASS_COUNT++))
        else
            echo -e "${RED}❌ $description${NC}"
            echo -e "   期待されるファイル: $file"
            ((FAIL_COUNT++))
        fi
    fi
}

# フェーズ1: 要件定義・計画
echo -e "\n${CYAN}=== フェーズ1: 要件定義・計画 ===${NC}"
check_file "REQUIREMENTS.md" "要件定義書"
check_file "WBS.json" "WBS（作業分解構造）"

# フェーズ2: テスト設計
echo -e "\n${CYAN}=== フェーズ2: テスト設計 ===${NC}"
if [ -d "tests" ]; then
    TEST_FILES=$(find tests -name "*.test.js" -o -name "*.test.ts" -o -name "*.py" 2>/dev/null | head -5)
    if [ -n "$TEST_FILES" ]; then
        echo -e "${GREEN}✅ テストファイル${NC}"
        echo "$TEST_FILES" | while read -r file; do
            echo -e "   - $file"
        done
        ((PASS_COUNT++))
    else
        echo -e "${RED}❌ テストファイルが見つかりません${NC}"
        ((FAIL_COUNT++))
    fi
    ((TOTAL_COUNT++))
else
    echo -e "${YELLOW}⚠️  tests ディレクトリが存在しません${NC}"
fi

# フェーズ3: 実装
echo -e "\n${CYAN}=== フェーズ3: 実装 ===${NC}"
check_file "package.json" "Node.js プロジェクト設定" "optional"
check_file "requirements.txt" "Python プロジェクト設定" "optional"

if [ -d "src" ] || [ -d "app" ] || [ -d "public" ]; then
    echo -e "${GREEN}✅ ソースコードディレクトリ${NC}"
    ((PASS_COUNT++))
else
    echo -e "${RED}❌ ソースコードディレクトリが見つかりません${NC}"
    ((FAIL_COUNT++))
fi
((TOTAL_COUNT++))

# フェーズ5: 完成処理（最重要）
echo -e "\n${CYAN}=== フェーズ5: 完成処理（最重要）===${NC}"
check_file "README.md" "README"
check_file "about.html" "プロジェクト解説ページ"
check_file "audio_script.txt" "音声スクリプト"
check_file "generate_audio_gcp.js" "音声生成スクリプト"
check_file "explanation.mp3" "解説音声" "optional"
check_file "launch_app.command" "起動スクリプト"

# package.json に音声生成の依存関係があるかチェック
if [ -f "package.json" ]; then
    if grep -q "@google-cloud/text-to-speech" package.json; then
        echo -e "${GREEN}✅ 音声生成依存関係${NC}"
        ((PASS_COUNT++))
    else
        echo -e "${YELLOW}⚠️  @google-cloud/text-to-speech が package.json にありません${NC}"
    fi
    ((TOTAL_COUNT++))
fi

# launch_app.command の実行権限チェック
if [ -f "launch_app.command" ]; then
    if [ -x "launch_app.command" ]; then
        echo -e "${GREEN}✅ launch_app.command 実行権限${NC}"
        ((PASS_COUNT++))
    else
        echo -e "${YELLOW}⚠️  launch_app.command に実行権限がありません${NC}"
        echo -e "   修正: chmod +x launch_app.command"
    fi
    ((TOTAL_COUNT++))
fi

# 結果サマリー
echo -e "\n${BLUE}================================${NC}"
echo -e "${BLUE}📊 検証結果サマリー${NC}"
echo -e "${BLUE}================================${NC}"

echo -e "\n検証項目: ${TOTAL_COUNT}個"
echo -e "${GREEN}成功: ${PASS_COUNT}個${NC}"
echo -e "${RED}失敗: ${FAIL_COUNT}個${NC}"

if [ $FAIL_COUNT -eq 0 ]; then
    echo -e "\n${GREEN}🎉 すべての検証に合格しました！${NC}"
else
    echo -e "\n${YELLOW}⚠️  未生成のファイルがあります${NC}"
    echo -e "\n${CYAN}修正方法:${NC}"

    if [ ! -f "about.html" ] || [ ! -f "audio_script.txt" ] || [ ! -f "generate_audio_gcp.js" ]; then
        echo -e "1. Documenterエージェントを実行:"
        echo -e "   ${YELLOW}python3 ~/Desktop/git-worktree-agent/_workflow/src/documenter_agent.py${NC}"
    fi

    if [ ! -f "explanation.mp3" ] && [ -f "generate_audio_gcp.js" ]; then
        echo -e "\n2. 音声を生成:"
        echo -e "   ${YELLOW}export GOOGLE_APPLICATION_CREDENTIALS=\"\$HOME/Desktop/git-worktree-agent/_workflow/credentials/gcp-workflow-key.json\"${NC}"
        echo -e "   ${YELLOW}npm install @google-cloud/text-to-speech${NC}"
        echo -e "   ${YELLOW}node generate_audio_gcp.js${NC}"
    fi

    if [ ! -f "launch_app.command" ]; then
        echo -e "\n3. 起動スクリプトを生成:"
        echo -e "   ${YELLOW}python3 ~/Desktop/git-worktree-agent/_workflow/src/launcher_generator.py${NC}"
    fi
fi

echo -e "\n${GREEN}検証完了${NC}"