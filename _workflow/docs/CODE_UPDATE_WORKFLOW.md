# 📝 コード修正・更新ワークフロー

## 🔄 ワークフローパターン

### パターンA: 軽微な修正（バグ修正、テキスト修正など）
```bash
# 1. 既存worktreeで修正
cd worktrees/mission-v1
# 修正作業...

# 2. テスト確認
npm test  # または適切なテスト

# 3. DELIVERYフォルダ更新
python3 ../../src/delivery_organizer.py

# 4. GitHub更新（--updateフラグ付き）
python3 ../../src/github_publisher_v8.py --update
```

### パターンB: 機能追加・大幅修正
```bash
# 1. 新しいブランチ作成
git worktree add -b feat/v2 ./worktrees/mission-v2 main

# 2. 修正作業
cd worktrees/mission-v2
# 開発作業...

# 3. テスト確認
npm test

# 4. DELIVERYフォルダ作成
python3 ../../src/delivery_organizer.py

# 5. GitHub更新
python3 ../../src/github_publisher_v8.py --update
```

## 🎯 重要ルール

### 1. DELIVERYフォルダのみ公開
- ソースコード全体は公開しない
- `worktrees/` の内容は公開しない
- テストコードは公開しない
- 開発用設定ファイルは公開しない

### 2. 公開先リポジトリ
- **固定URL**: `https://github.com/sohei-t/ai-agent-portfolio`
- **フォルダ構造**: `/apps/{アプリ名}/`
- **更新時**: 既存フォルダを上書き

### 3. 必須ファイル
DELIVERYフォルダに以下が含まれることを確認：
- `index.html` - アプリのエントリポイント
- `README.md` - アプリの説明
- `about.html` - ビジュアル説明ページ
- `src/` - 実行に必要な最小限のコード
- `assets/` - 画像やスタイル

## 🔨 実装方法

### 方法1: ローカルスキルとして実装（推奨）

**メリット:**
- Claudeが直接実行できる
- 手順が明確で確実
- エラーハンドリングが容易

**実装:**
```bash
# ~/.claude/skills/update-portfolio/skill.py として保存
```

### 方法2: ワークフローエージェントとして実装

**メリット:**
- 複雑な処理を自動化
- 並列処理可能
- 進捗が見える

**デメリット:**
- セットアップが複雑
- デバッグが困難

## 📋 チェックリスト

### 修正前
- [ ] 修正内容の明確化
- [ ] 影響範囲の確認
- [ ] バックアップの作成

### 修正中
- [ ] 適切なブランチで作業
- [ ] テストコードの更新
- [ ] ドキュメントの更新

### 修正後
- [ ] テスト全パス確認
- [ ] DELIVERYフォルダ生成
- [ ] 不要ファイル除外確認
- [ ] GitHub公開（--updateフラグ）

## 🚀 自動化スクリプト

### update_and_publish.sh
```bash
#!/bin/bash
# コード修正後の自動公開スクリプト

set -e

echo "🔄 コード更新・公開プロセス開始"

# 1. 現在のworktreeパス取得
WORKTREE_PATH=$(pwd)
PROJECT_ROOT=$(dirname $(dirname $WORKTREE_PATH))

# 2. テスト実行
echo "🧪 テスト実行中..."
npm test || pytest

# 3. DELIVERY作成
echo "📦 DELIVERYフォルダ作成中..."
python3 $PROJECT_ROOT/_workflow/src/delivery_organizer.py

# 4. GitHub公開
echo "📤 GitHubに公開中..."
python3 $PROJECT_ROOT/_workflow/src/github_publisher_v8.py --update

echo "✅ 更新完了！"
```

## 💡 推奨事項

1. **常にDELIVERYフォルダを経由**
   - 直接GitHubにpushしない
   - delivery_organizer.pyを必ず実行

2. **テスト必須**
   - 公開前に必ずテスト実行
   - エラーがある場合は公開しない

3. **バージョン管理**
   - 大きな変更は新しいブランチで
   - 小さな修正は既存ブランチで

4. **定期的な確認**
   - GitHub Pages の動作確認
   - リンク切れチェック
   - パフォーマンステスト