#!/bin/bash

# ポートフォリオリポジトリのクリーンアップスクリプト

PORTFOLIO_DIR="$HOME/Desktop/GitHub/ai-agent-portfolio"

echo "🧹 ポートフォリオリポジトリのクリーンアップ"
echo "📁 対象: $PORTFOLIO_DIR"
echo ""

# ディレクトリ存在確認
if [ ! -d "$PORTFOLIO_DIR" ]; then
    echo "❌ ポートフォリオディレクトリが見つかりません"
    exit 1
fi

cd "$PORTFOLIO_DIR"

echo "📝 削除対象ファイル:"
echo "  - .slug_mapping.json"
echo "  - .processed_apps.json"
echo "  - processed_apps.json"
echo "  - slug_mapping.json"
echo "  - PORTFOLIO_INDEX.md"
echo ""

# 確認
read -p "これらのファイルを削除しますか？ (y/n): " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    # 管理ファイル削除
    rm -f .slug_mapping.json
    rm -f .processed_apps.json
    rm -f processed_apps.json
    rm -f slug_mapping.json
    rm -f PORTFOLIO_INDEX.md

    echo "✅ 管理ファイルを削除しました"

    # .gitignore作成/更新
    cat > .gitignore << 'EOF'
# 管理ファイル（公開不要）
.slug_mapping.json
.processed_apps.json
processed_apps.json
slug_mapping.json
*.mapping.json
PORTFOLIO_INDEX.md

# OS関連
.DS_Store
Thumbs.db

# IDE
.vscode/
.idea/

# 環境ファイル
.env
.env.local
*.env

# ビルドキャッシュ
__pycache__/
*.pyc
*.pyo
node_modules/

# バックアップ
*.backup
*.bak
*~

# 一時ファイル
*.tmp
*.temp
.cache/
EOF

    echo "✅ .gitignoreを更新しました"

    # Git操作
    git add .gitignore
    git rm --cached .slug_mapping.json 2>/dev/null || true
    git rm --cached .processed_apps.json 2>/dev/null || true
    git rm --cached processed_apps.json 2>/dev/null || true
    git rm --cached slug_mapping.json 2>/dev/null || true
    git rm --cached PORTFOLIO_INDEX.md 2>/dev/null || true

    git commit -m "chore: 不要な管理ファイルを削除し.gitignoreを追加" 2>/dev/null

    echo ""
    echo "✅ クリーンアップ完了！"
    echo ""
    echo "📝 次のステップ:"
    echo "  git push origin main"
    echo ""
else
    echo "❌ キャンセルしました"
fi