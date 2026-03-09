# GitHub Portfolio Publisher - Detailed Reference

## 完全なワークフロー仕様

### 1. プロジェクト構造

```
~/Desktop/AI-Apps/{app-name}-agent/       # 開発環境
├── worktrees/
│   └── mission-v1/                       # 作業ディレクトリ
│       ├── src/                          # ソースコード
│       ├── tests/                        # テストコード
│       └── DELIVERY/                     # 公開対象（これだけ）
│           ├── index.html                # 必須
│           ├── README.md                 # 必須
│           ├── about.html                # 必須
│           ├── src/                      # 実行用最小コード
│           └── assets/                   # 画像・スタイル
├── src/
│   ├── delivery_organizer.py             # DELIVERY作成
│   ├── simplified_github_publisher.py    # GitHub公開
│   └── documenter_agent_v2.py            # ドキュメント生成
└── update_and_publish.sh                 # 自動化スクリプト
```

### 2. GitHub リポジトリ構造

```
https://github.com/sohei-t/ai-agent-portfolio/
├── index.html                             # ポートフォリオトップ
├── calculator/                            # アプリ1
│   ├── index.html
│   ├── README.md
│   └── about.html
├── todo-app/                             # アプリ2
│   └── ...
└── {app-name}/                           # 新しいアプリ（DELIVERYの内容を配置）
```

## スクリプト詳細仕様

### simplified_github_publisher.py

**主要機能:**
1. DELIVERYフォルダの検証
2. 不要ファイルの除去
3. {app-name}/ へのコピー（apps/ サブディレクトリは使わない）
4. ポートフォリオindex.html更新
5. Git操作（add, commit, push）

**除外されるファイル:**
- `.git`, `.gitignore`
- `.env`, `.env.*`
- `__pycache__`, `*.pyc`
- `node_modules/`, `venv/`
- `test_*`, `*_test.py`
- `*.log`, `*.tmp`, `*.bak`

**slugルール:**
- 日付プレフィックス除去（20241212- など）
- -agent サフィックス除去
- 小文字変換
- 特殊文字をハイフンに変換

### update_and_publish.sh

**処理フロー:**
1. worktreeディレクトリ確認
2. テスト実行（npm test または pytest）
3. delivery_organizer.py 実行
4. 新規/更新の選択
5. simplified_github_publisher.py 実行

**エラーハンドリング:**
- テスト失敗時は中断
- DELIVERY作成失敗時は中断
- Git push失敗時はrebase後に再試行

## コマンドリファレンス

### 基本コマンド

```bash
# 初回公開
cd worktrees/mission-v1
python3 ../../src/delivery_organizer.py
python3 ../../src/simplified_github_publisher.py .

# 更新公開
cd worktrees/mission-v1
python3 ../../src/delivery_organizer.py
python3 ../../src/simplified_github_publisher.py .

# 自動化
cd worktrees/mission-v1
../../update_and_publish.sh
```

### トラブルシューティング

```bash
# DELIVERYフォルダ再作成
rm -rf DELIVERY
python3 ../../src/delivery_organizer.py

# Git競合解決
cd ~/Desktop/GitHub/ai-agent-portfolio
git pull origin main --rebase
git push origin main

# 強制上書き（注意）
python3 ../../src/simplified_github_publisher.py .
```

## セキュリティチェックリスト

### 公開前確認事項

1. **ソースコード分離**
   - [ ] worktrees/ は含まれていない
   - [ ] 開発用設定ファイルは除外
   - [ ] テストコードは除外

2. **機密情報**
   - [ ] .env ファイルは除外
   - [ ] APIキーは含まれていない
   - [ ] 個人情報は削除済み

3. **必須ファイル**
   - [ ] index.html が存在
   - [ ] README.md が存在
   - [ ] about.html が存在
   - [ ] 実行に必要な最小コードのみ

4. **リポジトリ確認**
   - [ ] URLは sohei-t/ai-agent-portfolio
   - [ ] リポジトリ直下に {app-name}/ を配置
   - [ ] 既存アプリを上書きしない（異なる名前）

## GitHub Pages URL構成

### アクセスURL

- **ポートフォリオトップ**: https://sohei-t.github.io/ai-agent-portfolio/
- **アプリ一覧**: https://sohei-t.github.io/ai-agent-portfolio/index.html
- **個別アプリ**: https://sohei-t.github.io/ai-agent-portfolio/{app-name}/
- **アプリ説明**: https://sohei-t.github.io/ai-agent-portfolio/{app-name}/about.html

### README.md 自動追加リンク

```markdown
## 🌐 Live Demo & Documentation

### [🎮 Live Demo](https://sohei-t.github.io/ai-agent-portfolio/{app-name}/)
### [📱 Visual Presentation](https://sohei-t.github.io/ai-agent-portfolio/{app-name}/about.html)
### [🎵 Audio Explanation](https://sohei-t.github.io/ai-agent-portfolio/{app-name}/explanation.mp3)
```

## ベストプラクティス

1. **開発フロー**
   - 常にworktreeで作業
   - テストを必ず実行
   - DELIVERYフォルダ経由で公開

2. **バージョン管理**
   - 大きな変更は新ブランチ
   - 小さな修正は既存ブランチ
   - コミットメッセージは明確に

3. **品質保証**
   - テスト全パス確認
   - ローカル動作確認
   - GitHub Pages動作確認

4. **定期メンテナンス**
   - 不要ファイル削除
   - リンク切れチェック
   - パフォーマンス最適化
