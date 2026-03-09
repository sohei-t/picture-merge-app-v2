# GitHub Portfolio Publisher Skill

DELIVERYフォルダのみを安全にGitHubポートフォリオに公開するためのローカルスキル。

## 📋 概要

このスキルは、開発したアプリケーションのDELIVERYフォルダのみを https://github.com/sohei-t/ai-agent-portfolio に公開・更新するための厳格なルールとワークフローを提供します。

## 🚀 主な機能

- DELIVERYフォルダのみを公開（ソースコード全体は公開しない）
- 固定リポジトリ（sohei-t/ai-agent-portfolio）への安全な公開
- 新規公開と更新公開の両方に対応
- 自動テスト実行とエラーハンドリング
- GitHub Pages対応のURL生成

## 📦 インストール方法

### グローバルスキルとして配置する場合（推奨）

全てのプロジェクトで使用可能になります：

```bash
# スキルをグローバルディレクトリにコピー
cp -r github-portfolio-publisher ~/.claude/skills/

# 確認
ls ~/.claude/skills/github-portfolio-publisher/
```

### ローカルスキルとして配置する場合

このプロジェクトのみで使用：

```bash
# プロジェクトルートで実行
mkdir -p .claude/skills
cp -r github-portfolio-publisher .claude/skills/

# 確認
ls .claude/skills/github-portfolio-publisher/
```

## 🔧 使い方

### 基本的な使用方法

1. **初回公開時**
   ```bash
   cd worktrees/mission-v1
   python3 ../../src/delivery_organizer.py
   python3 ../../src/github_publisher_v8.py
   ```

2. **コード修正後の更新**
   ```bash
   cd worktrees/mission-v1
   # 修正作業...
   ../../update_and_publish.sh
   # → 「2. 更新公開」を選択
   ```

### Claudeへの指示例

```
「コードを修正したので、GitHubポートフォリオを更新してください」
「DELIVERYフォルダをGitHubに公開してください」
「アプリを sohei-t/ai-agent-portfolio に公開してください」
```

## 📁 ファイル構成

```
github-portfolio-publisher/
├── SKILL.md        # メインスキル定義
├── template.py     # Pythonテンプレート
├── reference.md    # 詳細リファレンス
└── README.md       # このファイル
```

## ⚠️ 重要な注意事項

1. **必ず DELIVERYフォルダのみを公開**
   - worktrees/ の内容は公開しない
   - ソースコード全体は公開しない

2. **固定リポジトリを使用**
   - 必ず `sohei-t/ai-agent-portfolio` に公開
   - 他のリポジトリには公開しない

3. **テストを必ず実行**
   - 公開前にテストが全てパスすることを確認
   - エラーがある状態では公開しない

## 🔍 動作確認

インストール後、Claudeに以下を聞いて確認：

```
「github-portfolio-publisher スキルは使えますか？」
「DELIVERYフォルダをGitHubに公開する手順を教えてください」
```

## 📚 関連ファイル

プロジェクト内の関連ファイル：

- `src/delivery_organizer.py` - DELIVERY作成スクリプト
- `src/github_publisher_v8.py` - GitHub公開スクリプト（厳格版）
- `update_and_publish.sh` - 自動更新スクリプト
- `CODE_UPDATE_WORKFLOW.md` - ワークフロー詳細説明

## 🆘 トラブルシューティング

### スキルが認識されない場合
```bash
# グローバルスキルの確認
ls -la ~/.claude/skills/

# ローカルスキルの確認
ls -la .claude/skills/

# 権限の修正
chmod -R 755 ~/.claude/skills/github-portfolio-publisher
```

### DELIVERYフォルダが作成されない
```bash
python3 src/delivery_organizer.py
```

### GitHub pushが失敗する
```bash
cd ~/Desktop/GitHub/ai-agent-portfolio
git pull origin main --rebase
# 再度公開スクリプトを実行
```

## 📝 更新履歴

- v1.0 (2024-12-12): 初版作成
  - DELIVERYフォルダのみの公開機能
  - sohei-t/ai-agent-portfolio への固定
  - 自動更新スクリプト対応

## 📮 サポート

問題が発生した場合は、以下を確認してください：

1. `SKILL.md` が正しく配置されているか
2. Pythonスクリプトが実行可能か
3. GitHubへのアクセス権限があるか

---

作成日: 2024-12-12
作成者: Claude with sohei-t