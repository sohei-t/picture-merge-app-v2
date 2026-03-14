#!/bin/bash

# Portfolio プロジェクトにプロフェッショナル文書を追加するスクリプト
# 既存の Portfolio プロジェクトを強化

set -e

# カラー定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${BLUE}================================${NC}"
echo -e "${BLUE}📚 Portfolio プロジェクト強化${NC}"
echo -e "${BLUE}================================${NC}"

# 現在のディレクトリがPortfolioプロジェクトか確認
if [ ! -f "PROJECT_INFO.yaml" ]; then
    echo -e "${RED}❌ PROJECT_INFO.yaml が見つかりません${NC}"
    echo "Portfolio プロジェクトのディレクトリで実行してください"
    exit 1
fi

# プロジェクトタイプを確認
PROJECT_TYPE=$(grep "type:" PROJECT_INFO.yaml | awk '{print $2}')
if [ "$PROJECT_TYPE" != "portfolio" ]; then
    echo -e "${YELLOW}⚠️  これは Portfolio プロジェクトではありません (type: $PROJECT_TYPE)${NC}"
    echo "Portfolio プロジェクトでのみ実行可能です"
    exit 1
fi

PROJECT_NAME=$(grep "name:" PROJECT_INFO.yaml | head -1 | awk '{print $2}')
echo -e "${GREEN}プロジェクト: ${PROJECT_NAME}${NC}"

# portfolio_doc_generator.py をコピー
GENERATOR_SCRIPT="${WORKFLOW_DIR:-.}/_workflow/src/portfolio_doc_generator.py"
if [ ! -f "$GENERATOR_SCRIPT" ]; then
    echo -e "${RED}❌ portfolio_doc_generator.py が見つかりません${NC}"
    exit 1
fi

# enhanced_client_document_generator.py も必要
ENHANCED_GENERATOR="${WORKFLOW_DIR:-.}/_workflow/src/enhanced_client_document_generator.py"
if [ ! -f "$ENHANCED_GENERATOR" ]; then
    echo -e "${RED}❌ enhanced_client_document_generator.py が見つかりません${NC}"
    exit 1
fi

# src ディレクトリを作成
mkdir -p src

# 必要なスクリプトをコピー
echo -e "${YELLOW}📋 文書生成スクリプトをコピー中...${NC}"
cp "$GENERATOR_SCRIPT" src/
cp "$ENHANCED_GENERATOR" src/

# PDF変換スクリプトもコピー（存在する場合）
PDF_CONVERTER="${WORKFLOW_DIR:-.}/_workflow/src/pdf_converter.js"
if [ -f "$PDF_CONVERTER" ]; then
    cp "$PDF_CONVERTER" src/
    echo -e "${GREEN}✅ PDF変換スクリプトもコピーしました${NC}"
fi

# 最新のworktreeまたはreleaseディレクトリから実行
if [ -d "release" ]; then
    echo -e "${YELLOW}📂 release/ ディレクトリで文書生成を実行...${NC}"
    cd release/*/ 2>/dev/null || cd release
elif [ -d "worktrees" ]; then
    LATEST_WORKTREE=$(ls -td worktrees/mission-* 2>/dev/null | head -1)
    if [ -n "$LATEST_WORKTREE" ]; then
        echo -e "${YELLOW}📂 $LATEST_WORKTREE で文書生成を実行...${NC}"
        cd "$LATEST_WORKTREE"
    fi
fi

# Python の yaml モジュールをチェック
python3 -c "import yaml" 2>/dev/null || {
    echo -e "${YELLOW}📦 PyYAML をインストール中...${NC}"
    pip3 install pyyaml
}

# プロフェッショナル文書を生成
echo -e "\n${CYAN}📄 プロフェッショナル文書を生成中...${NC}"
python3 ../../src/portfolio_doc_generator.py || python3 src/portfolio_doc_generator.py

# 生成された文書を確認
if [ -d "professional-docs" ]; then
    echo -e "\n${GREEN}✅ プロフェッショナル文書が生成されました！${NC}"
    echo -e "${BLUE}📁 内容:${NC}"
    ls -la professional-docs/

    # PDF変換が必要か確認
    PDF_COUNT=$(find professional-docs -name "*.pdf" | wc -l)
    MD_COUNT=$(find professional-docs -name "*.md" | wc -l)

    if [ "$PDF_COUNT" -eq 0 ] && [ "$MD_COUNT" -gt 0 ]; then
        echo -e "\n${YELLOW}📄 PDF変換を実行しますか？ (y/n)${NC}"
        read -p "> " CONVERT_PDF

        if [ "$CONVERT_PDF" = "y" ] || [ "$CONVERT_PDF" = "Y" ]; then
            if [ -f "src/pdf_converter.js" ] && [ -d "node_modules/puppeteer" ]; then
                node src/pdf_converter.js professional-docs/
            else
                echo -e "${YELLOW}PDF変換にはnpm installが必要です:${NC}"
                echo "  npm install marked puppeteer"
            fi
        fi
    fi

    echo -e "\n${BLUE}================================${NC}"
    echo -e "${GREEN}✨ Portfolio プロジェクトが強化されました！${NC}"
    echo -e "${BLUE}================================${NC}"

    echo -e "\n次のステップ:"
    echo "1. リリース版を更新: ./release.sh"
    echo "2. GitHubに公開: ./publish_to_portfolio.sh"
    echo ""
    echo -e "${GREEN}これで以下がアピールできます:${NC}"
    echo "  ✅ コード開発能力"
    echo "  ✅ テスト作成能力"
    echo "  ✅ プロフェッショナルな文書作成能力"
    echo "  ✅ AIを活用した自動化能力"
else
    echo -e "${RED}❌ 文書生成に失敗しました${NC}"
fi