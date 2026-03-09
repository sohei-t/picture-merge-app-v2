#!/bin/bash
# GitHub CLI ARM64版セットアップスクリプト (M4 Mac対応)
# このスクリプトはM4チップのMacでGitHub CLIをセットアップし、自動プッシュを可能にします

set -e

echo "🚀 GitHub CLI ARM64版セットアップを開始します..."

# 1. 既存のghコマンドを確認
echo "📋 既存のGitHub CLI設定を確認中..."
if command -v gh &> /dev/null; then
    echo "⚠️ 既存のghコマンドが見つかりました: $(which gh)"
    gh_version=$(gh --version 2>/dev/null || echo "バージョン取得失敗")
    echo "   バージョン: $gh_version"
fi

# 2. ~/bin ディレクトリを作成
echo "📁 ~/bin ディレクトリをセットアップ中..."
mkdir -p ~/bin

# 3. ARM64版のGitHub CLIをダウンロード
GH_VERSION="2.63.2"
echo "📦 GitHub CLI v$GH_VERSION (ARM64版) をダウンロード中..."

# 既存ファイルをクリーンアップ
rm -f /tmp/gh_arm64.zip
rm -rf /tmp/gh_${GH_VERSION}_macOS_arm64

# ダウンロード
curl -L "https://github.com/cli/cli/releases/download/v${GH_VERSION}/gh_${GH_VERSION}_macOS_arm64.zip" \
    -o /tmp/gh_arm64.zip \
    --progress-bar

# 4. 展開とインストール
echo "📂 展開中..."
cd /tmp
unzip -q gh_arm64.zip

echo "🔧 インストール中..."
cp /tmp/gh_${GH_VERSION}_macOS_arm64/bin/gh ~/bin/gh
chmod +x ~/bin/gh

# 5. バージョン確認
echo "✅ インストール完了！"
echo "   インストール先: ~/bin/gh"
echo "   バージョン: $(~/bin/gh --version)"

# 6. PATHの設定を確認
if [[ ":$PATH:" != *":$HOME/bin:"* ]]; then
    echo ""
    echo "⚠️ ~/bin がPATHに含まれていません"
    echo "以下のいずれかの方法でPATHに追加してください:"
    echo ""
    echo "# bashの場合 (~/.bash_profile に追加):"
    echo 'export PATH="$HOME/bin:$PATH"'
    echo ""
    echo "# zshの場合 (~/.zshrc に追加):"
    echo 'export PATH="$HOME/bin:$PATH"'
fi

# 7. 認証状態を確認
echo ""
echo "📋 GitHub認証状態を確認中..."
if ~/bin/gh auth status &> /dev/null; then
    echo "✅ GitHub認証済み"
    ~/bin/gh auth status
else
    echo "⚠️ GitHub認証が必要です"
    echo ""
    echo "以下のコマンドで認証を設定してください:"
    echo "~/bin/gh auth login"
    echo ""
    echo "推奨設定:"
    echo "  - Where do you use GitHub? → GitHub.com"
    echo "  - Protocol → SSH"
    echo "  - SSH key → 既存のキーを選択 (id_ed25519推奨)"
    echo "  - Title → デフォルト (GitHub CLI) またはカスタム名"
    echo "  - Authenticate → Login with a web browser"
fi

# 8. Git設定の更新
echo ""
echo "🔧 Git認証ヘルパーを設定中..."

# credential helperスクリプトを作成
cat > ~/bin/gh-credential-helper.sh << 'EOF'
#!/bin/bash
# GitHub CLI credential helper for M4 Mac
exec ~/bin/gh auth git-credential "$@"
EOF

chmod +x ~/bin/gh-credential-helper.sh

# グローバルGit設定を更新
echo "   Gitグローバル設定を更新中..."
/usr/bin/git config --global --replace-all credential.https://github.com.helper "!~/bin/gh-credential-helper.sh"

echo "✅ Git認証ヘルパー設定完了"

# 9. クリーンアップ
echo ""
echo "🧹 一時ファイルをクリーンアップ中..."
rm -f /tmp/gh_arm64.zip
rm -rf /tmp/gh_${GH_VERSION}_macOS_arm64

echo ""
echo "========================================="
echo "✅ セットアップ完了！"
echo "========================================="
echo ""
echo "📝 次のステップ:"

if ! ~/bin/gh auth status &> /dev/null; then
    echo "1. GitHub認証を設定:"
    echo "   ~/bin/gh auth login"
else
    echo "1. ✅ GitHub認証済み"
fi

echo ""
echo "2. 自動プッシュをテスト:"
echo "   cd {your-repo}"
echo "   /usr/bin/git push origin main"
echo ""
echo "========================================="