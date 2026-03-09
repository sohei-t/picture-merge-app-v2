#!/bin/bash

# 顧客納品物パッケージング スクリプト
# Client deliverables packaging script

set -e

# カラー定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}================================${NC}"
echo -e "${BLUE}📦 納品物パッケージング開始${NC}"
echo -e "${BLUE}================================${NC}"

# プロジェクト情報を取得
PROJECT_NAME=""
CLIENT_NAME=""
if [ -f "PROJECT_INFO.yaml" ]; then
    PROJECT_NAME=$(grep "name:" PROJECT_INFO.yaml | head -1 | sed 's/.*name: *//')
    CLIENT_NAME=$(grep "client_name:" PROJECT_INFO.yaml | head -1 | sed 's/.*client_name: *//')
fi

if [ -z "$PROJECT_NAME" ]; then
    PROJECT_NAME="project"
fi

if [ -z "$CLIENT_NAME" ]; then
    CLIENT_NAME="client"
fi

TIMESTAMP=$(date +%Y%m%d_%H%M%S)

echo -e "${YELLOW}プロジェクト: ${PROJECT_NAME}${NC}"
echo -e "${YELLOW}クライアント: ${CLIENT_NAME}${NC}"

# ディレクトリ構成を作成
echo -e "\n${GREEN}📁 納品物ディレクトリを作成中...${NC}"

mkdir -p deliverables/01_documents
mkdir -p deliverables/02_source
mkdir -p deliverables/03_executable
mkdir -p deliverables/04_presentation

# ドキュメント生成
echo -e "\n${GREEN}📄 ドキュメントを生成中...${NC}"

# 強化版ドキュメント生成スクリプトを実行
if [ -f "src/enhanced_client_document_generator.py" ]; then
    python3 src/enhanced_client_document_generator.py
elif [ -f "src/client_document_generator.py" ]; then
    python3 src/client_document_generator.py
else
    echo -e "${YELLOW}⚠️  ドキュメント生成スクリプトが見つかりません${NC}"
fi

# PDF変換の準備
PDF_CONVERTER_AVAILABLE=false

# Node.jsベースのPDF変換を優先的に使用
if [ -f "src/pdf_converter.js" ] && [ -f "package.json" ]; then
    # node_modulesがなければインストール
    if [ ! -d "node_modules/puppeteer" ] || [ ! -d "node_modules/marked" ]; then
        echo -e "${YELLOW}📦 PDF変換モジュールをインストール中...${NC}"
        echo -e "${YELLOW}   (初回のみ。puppeteerのダウンロードに数分かかります)${NC}"
        npm install --silent 2>/dev/null || {
            echo -e "${RED}⚠️  npm install 失敗。PDF変換をスキップします${NC}"
        }
    fi

    # PDF変換実行
    if [ -d "node_modules/puppeteer" ] && [ -d "node_modules/marked" ]; then
        echo -e "\n${GREEN}📄 PDFに変換中...${NC}"
        node src/pdf_converter.js deliverables/01_documents/ 2>/dev/null || {
            echo -e "${YELLOW}⚠️  PDF変換中にエラーが発生しました${NC}"
        }
        PDF_CONVERTER_AVAILABLE=true
    fi
fi

# 代替手段: markdown-pdfがインストールされている場合
if [ "$PDF_CONVERTER_AVAILABLE" = false ] && command -v markdown-pdf &> /dev/null; then
    echo -e "\n${GREEN}📄 PDFに変換中（markdown-pdf使用）...${NC}"
    for md_file in deliverables/01_documents/*.md; do
        if [ -f "$md_file" ]; then
            pdf_file="${md_file%.md}.pdf"
            markdown-pdf "$md_file" -o "$pdf_file"
            echo -e "  ✅ $(basename "$pdf_file")"
        fi
    done
    PDF_CONVERTER_AVAILABLE=true
fi

# PDF変換できなかった場合
if [ "$PDF_CONVERTER_AVAILABLE" = false ]; then
    echo -e "${YELLOW}⚠️  PDF変換モジュールが利用できません。Markdown形式のまま納品します。${NC}"
    echo -e "${YELLOW}   PDF変換を有効にするには: npm install${NC}"
fi

# ソースコードをパッケージング
echo -e "\n${GREEN}📦 ソースコードをパッケージング中...${NC}"

# 除外するファイル/ディレクトリのリスト
EXCLUDE_PATTERNS=(
    "node_modules"
    ".git"
    ".gitignore"
    "*.log"
    ".env"
    ".env.local"
    ".env.production"
    "dist"
    "build"
    "coverage"
    "__pycache__"
    "*.pyc"
    ".DS_Store"
    "Thumbs.db"
)

# tar除外オプションを構築
EXCLUDE_OPTIONS=""
for pattern in "${EXCLUDE_PATTERNS[@]}"; do
    EXCLUDE_OPTIONS="$EXCLUDE_OPTIONS --exclude=$pattern"
done

# ソースコードをアーカイブ
tar -czf deliverables/02_source/source_code.tar.gz $EXCLUDE_OPTIONS .

# README.mdをコピー
if [ -f "README.md" ]; then
    cp README.md deliverables/02_source/
fi

# ライセンスファイルを作成
cat > deliverables/02_source/LICENSE.md << 'EOFMARKER'
# ライセンス情報

本ソフトウェアは、特定のクライアント向けに開発されたものです。

## 著作権
Copyright (c) 2024 [開発者名/会社名]

## 使用許諾
本ソフトウェアの使用は、契約書に記載された条件に従います。

## 制限事項
- 本ソフトウェアの無断複製・配布を禁止します
- リバースエンジニアリングを禁止します
- 第三者への譲渡・貸与を禁止します

## 保証
本ソフトウェアは現状のまま提供され、明示的または暗黙的な保証はありません。
EOFMARKER

# 実行可能ファイルをコピー
echo -e "\n${GREEN}🚀 実行可能ファイルを準備中...${NC}"

# launch_app.commandをコピー
if [ -f "launch_app.command" ]; then
    cp launch_app.command deliverables/03_executable/
    chmod +x deliverables/03_executable/launch_app.command
fi

# package.jsonをコピー（依存関係確認用）
if [ -f "package.json" ]; then
    cp package.json deliverables/03_executable/
fi

# インストール手順を作成
cat > deliverables/03_executable/INSTALL.md << 'EOFMARKER'
# インストール手順

## 前提条件
- Node.js 18.0.0以降がインストールされていること
- npmまたはyarnがインストールされていること

## インストール手順

1. ソースコードを展開
```bash
cd 展開したいディレクトリ
tar -xzf ../02_source/source_code.tar.gz
```

2. 依存関係をインストール
```bash
npm install
```

3. 環境設定（必要に応じて）
```bash
cp .env.example .env
# .envファイルを編集
```

4. アプリケーション起動
```bash
# 方法1: launch_app.commandをダブルクリック
# 方法2: コマンドラインから
npm start
```

## トラブルシューティング
問題が発生した場合は、操作マニュアルのトラブルシューティングセクションを参照してください。
EOFMARKER

# プレゼンテーション資料をコピー
echo -e "\n${GREEN}🎨 プレゼンテーション資料を準備中...${NC}"

# about.htmlがあればコピー
if [ -f "about.html" ]; then
    cp about.html deliverables/04_presentation/system_overview.html
fi

# 音声ファイルがあればコピー
if [ -f "explanation.mp3" ]; then
    cp explanation.mp3 deliverables/04_presentation/
fi

# 納品物一覧を作成
echo -e "\n${GREEN}📋 納品物一覧を作成中...${NC}"

cat > deliverables/納品物一覧.md << EOFMARKER
# 納品物一覧

## プロジェクト: ${PROJECT_NAME}
## クライアント: ${CLIENT_NAME}
## 納品日: $(date +%Y年%m月%d日)

## 納品物構成

### 📁 01_documents/ - ドキュメント類
- 要件定義書（PDF/Markdown）
- 基本設計書（PDF/Markdown）
- テスト結果報告書（PDF/Markdown）
- 操作マニュアル（PDF/Markdown）
- 納品チェックリスト

### 📁 02_source/ - ソースコード
- source_code.tar.gz - ソースコード一式
- README.md - 開発者向けドキュメント
- LICENSE.md - ライセンス情報

### 📁 03_executable/ - 実行可能形式
- launch_app.command - ワンクリック起動スクリプト
- package.json - 依存関係定義
- INSTALL.md - インストール手順

### 📁 04_presentation/ - プレゼンテーション資料
- system_overview.html - システム概要説明
- explanation.mp3 - 音声解説（ある場合）

## 使用方法

1. **ドキュメントの確認**
   01_documents/フォルダ内の各ドキュメントをご確認ください。

2. **システムのインストール**
   03_executable/INSTALL.mdの手順に従ってインストールしてください。

3. **システムの起動**
   launch_app.commandをダブルクリックするか、npm startを実行してください。

## サポート
ご不明な点がございましたら、以下までお問い合わせください：
- メール: support@example.com
- 電話: 03-XXXX-XXXX

---
© 2024 All Rights Reserved.
EOFMARKER

# 最終パッケージを作成
echo -e "\n${GREEN}📦 最終パッケージを作成中...${NC}"

PACKAGE_NAME="${CLIENT_NAME}_${PROJECT_NAME}_deliverables_${TIMESTAMP}.zip"

cd deliverables
zip -r "../${PACKAGE_NAME}" . -x "*.DS_Store" "*__MACOSX*"
cd ..

# 完了メッセージ
echo -e "\n${GREEN}================================${NC}"
echo -e "${GREEN}✅ 納品物パッケージング完了！${NC}"
echo -e "${GREEN}================================${NC}"

echo -e "\n${BLUE}📦 納品物の場所:${NC}"
echo -e "  ディレクトリ: ./deliverables/"
echo -e "  パッケージ: ./${PACKAGE_NAME}"

echo -e "\n${BLUE}📋 納品物の内容:${NC}"
echo -e "  1. ドキュメント一式（01_documents/）"
echo -e "  2. ソースコード（02_source/）"
echo -e "  3. 実行可能ファイル（03_executable/）"
echo -e "  4. プレゼンテーション資料（04_presentation/）"

echo -e "\n${YELLOW}⚠️  納品前に以下を確認してください:${NC}"
echo -e "  - 機密情報が含まれていないか"
echo -e "  - ライセンス条項が正しいか"
echo -e "  - クライアント情報が正確か"
echo -e "  - すべてのドキュメントが最新か"

echo -e "\n${GREEN}納品準備が整いました！${NC}"