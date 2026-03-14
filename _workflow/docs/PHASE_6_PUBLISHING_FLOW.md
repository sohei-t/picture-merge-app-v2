# 📚 Phase 6: GitHubポートフォリオ公開フロー詳細

## 🎯 設計思想

### 問題と解決
**問題**: 同じアプリを修正するたびに日付違いのフォルダがGitHubに増える
**解決**: slug方式で管理し、同じアプリは同じリポジトリ/フォルダを使用

## 📊 2つの公開方式

### 方式1: 統合ポートフォリオ（simplified_github_publisher.py）
```
~/Desktop/AI-Apps/20241210-todo-app-agent/
                    ↓ slug変換（日付除去）
GitHub: ai-agent-portfolio/todo-app/
                    ↓ GitHub Actions 自動デプロイ（v9.0〜）
GitHub Pages: https://sohei-t.github.io/ai-agent-portfolio/todo-app/
```
- **用途**: 全作品を1箇所で管理・公開
- **メリット**: ポートフォリオ全体を見せやすい
- **実行**: `python3 ./_workflow/src/simplified_github_publisher.py .`
- **v9.0**: deploy.yml が gh-pages を自動更新、release.yml がタグからzip自動生成

### 方式2: 個別リポジトリ（github_portfolio_publisher.py）
```
~/Desktop/AI-Apps/20241210-todo-app-agent/
                    ↓ リポジトリ名生成
GitHub: portfolio-todo-app （個別リポジトリ）
```
- **用途**: 各アプリを独立したリポジトリとして公開
- **メリット**: 詳細なREADME、Issues、GitHub Pagesが使える
- **実行**: `python3 ./_workflow/src/github_portfolio_publisher.py`

## 📋 Phase 6 実行の判断フロー

```mermaid
graph TD
    A[Phase 5完了] --> B{PROJECT_INFO.yaml確認}
    B -->|Portfolio App| C[worktreeマージ確認]
    B -->|Client App| Z[Phase 6スキップ]

    C --> D{公開方式選択}

    D -->|統合ポートフォリオ| E[simplified_github_publisher.py]
    E --> F[ai-agent-portfolio/{slug}/]

    D -->|個別リポジトリ| G[github_portfolio_publisher.py]
    G --> H[portfolio-{app-name}リポジトリ]

    D -->|両方| I[両方実行]
    I --> F
    I --> H

    F --> J[公開URL表示]
    H --> J
```

## 🚀 実行手順（Phase 6）

### 🚨 Step 0: セキュリティチェック（最重要・必須）

**絶対にGitHubにプッシュしてはいけないもの:**

```bash
# 1. credentials/ フォルダ全体
ls -la credentials/ 2>/dev/null && echo "❌ credentials/ が存在します - 削除またはgit rm必須"

# 2. GCP認証キー
find . -name "*.key.json" -o -name "*-key.json" -o -name "service-account*.json"

# 3. .env ファイル（.env.example以外）
find . -name ".env" -not -name ".env.example"

# 4. 開発ツール・テストコード
find . -name "*agent*.py" -o -name "generate_audio*.js" -o -name "tests/"

# 5. Git追跡状態を確認
git status

# 6. 過去のコミット履歴に機密ファイルが含まれていないか確認
git log --all --full-history --oneline -- credentials/ "*.key.json" "*.pem"
```

**チェックリスト:**
- [ ] credentials/ フォルダが.gitignoreに含まれているか確認
- [ ] git status に credentials/ や *.key.json が表示されないか確認
- [ ] .gitignore に以下が含まれているか確認:
  ```
  credentials/
  *.key.json
  *-key.json
  service-account*.json
  gcp-*.json
  imagen-*.json
  .env
  .env.*
  !.env.example
  tests/
  *agent*.py
  generate_audio*.js
  ```
- [ ] project/public/ フォルダに開発ツールやテストコードが含まれていないか確認

**⚠️ 機密ファイルが見つかった場合:**
1. 即座に作業を中断
2. `SECURITY_INCIDENT_REPORT.md` を参照
3. Git履歴から完全削除（BFG/filter-repo）
4. GCPキーを無効化・再生成

**✅ clean_public() による自動除外:**
`simplified_github_publisher.py` が以下を自動除外します：
- 認証情報（credentials/, *.key.json, .env）
- 開発ツール（*agent*.py, generate_audio*.js）
- テストコード（tests/, *.test.js, pytest.ini）
- 開発用ドキュメント（WBS*.json, DESIGN*.md, docs/）
- 依存関係フォルダ（node_modules/, venv/）

### Step 1: Worktreeの確認とマージ（マージ後はメイン環境で実行）
```bash
# 作業場所を専用環境に移動
cd ~/Desktop/AI-Apps/{app-name}-agent/

# worktreeの状態確認
git worktree list

# worktreeが残っていたら main にマージ（Worktree自体は維持してよい）
git merge feat/{app-name}
```

### Step 2: PROJECT_INFO.yamlの確認
```bash
# Portfolio Appかどうか確認
cat PROJECT_INFO.yaml | grep development_type
# "Portfolio App" なら続行
# "Client App" ならPhase 6スキップ
```

### Step 3A: 統合ポートフォリオへ公開
```bash
# ai-agent-portfolio リポジトリが存在する場合（公開に不要/機密なファイルは自動除外）
python3 ./_workflow/src/simplified_github_publisher.py .

# 結果: ai-agent-portfolio/todo-app/ に配置（日付なし・同名フォルダは中身だけ更新）
# v9.0: deploy.yml が自動で gh-pages 同期、release.yml がタグから zip 生成
```

**🆕 v9.0 GitHub Actions 自動化（deploy.yml + release.yml）:**
```
GitHub Actions がデプロイとリリースを自動実行:

1. deploy.yml（main push トリガー）:
   main push → peaceiris/actions-gh-pages@v4 → gh-pages ブランチ自動更新
   → GitHub Pages が自動的に最新に（エージェントによる手動同期は不要）

2. release.yml（タグ push トリガー）:
   タグ({slug}-v1.0.0) push → zip 自動生成 → Releases ページに公開
   → ユーザーがワンクリックでダウンロード可能

エージェントの責任:
- main push 後に gh run list で deploy.yml の成功を確認
- リリースタグ({slug}-v1.0.0)を作成 & push して release.yml をトリガー
- Actions 完了後に Phase 6.5 セキュリティ検証に進む

確認方法:
✅ GitHub Pages: https://sohei-t.github.io/ai-agent-portfolio/{slug}/
✅ Releases: https://github.com/sohei-t/ai-agent-portfolio/releases
✅ Actions: gh run list --repo sohei-t/ai-agent-portfolio --limit 3
⚠️ 404の場合: 数分待ってから再確認（GitHub Pagesのビルドに時間がかかる場合あり）
```

**📋 公開される最小限のファイル（自動選別）:**
```
✅ 公開対象:
  - index.html, about.html （公開ページ）
  - assets/ （画像、CSS、JS等の静的ファイル）
  - dist/ または build/ （ビルド済み成果物、必要な場合のみ）
  - README.md （使い方・技術説明）
  - explanation.mp3 （音声解説、オプション）
  - package.json （依存関係情報、実行に必要な場合のみ）

❌ 自動除外されるファイル:
  - tests/, test/, __tests__/ （テストコード）
  - *agent*.py, documenter_agent.py （開発ツール）
  - generate_audio*.js, audio_generator*.py （音声生成ツール）
  - credentials/, *.key.json, .env （認証情報）
  - WBS*.json, DESIGN*.md, PROJECT_INFO.yaml （開発用ドキュメント）
  - docs/, design/, planning/ （内部ドキュメントフォルダ）
  - node_modules/, venv/, package-lock.json （依存関係フォルダ）
  - launch_app.command （ローカル実行スクリプト）
  - *.test.js, *.spec.ts, pytest.ini （テストファイル）
```

**🎯 公開ポリシー:**
「そのコードをローカルにコピーすれば、アプリが実行できる最低限のファイル」+ 「解説ドキュメント（README.md, about.html）」のみを公開。開発プロセスやテストコードは一切含めない。

### Step 3B: 個別リポジトリとして公開
```bash
# 新規GitHubリポジトリを作成
python3 ./_workflow/src/github_portfolio_publisher.py .

# 結果: portfolio-todo-app リポジトリ作成
```

### Step 4: 公開確認
```
========================================
🎉 GitHubポートフォリオ公開完了！
========================================

📦 リポジトリ:
[統合] https://github.com/sohei-t/ai-agent-portfolio/tree/main/todo-app
[個別] https://github.com/{user}/portfolio-todo-app

🌐 GitHub Pages:
[統合] https://sohei-t.github.io/ai-agent-portfolio/todo-app/  ← deploy.yml 自動デプロイ
[個別] https://{user}.github.io/portfolio-todo-app/

📦 Releases（v9.0〜）:
https://github.com/sohei-t/ai-agent-portfolio/releases

🔄 GitHub Actions:
- deploy.yml: main push → gh-pages 自動同期
- release.yml: タグ push → zip 自動生成

========================================
```

**⚠️ GitHub Pagesで404が表示される場合:**
1. `gh run list --repo sohei-t/ai-agent-portfolio --workflow deploy.yml --limit 3` で Actions の状態を確認
2. GitHub Settings → Pages で Source が `gh-pages` ブランチになっているか確認
3. 数分待ってから再確認（ビルドに時間がかかる場合あり）

## 🔄 更新時の挙動

### 同じアプリを後日修正した場合

1. **開発環境**: 既存のagentフォルダを再利用（日付なし）
   ```
   ~/Desktop/AI-Apps/todo-app-agent/  # 同じフォルダを使用
   ```

2. **GitHub公開時**: 同じ場所を更新
   ```
   統合: ai-agent-portfolio/todo-app/      # フォルダ名はそのまま、中身のみ上書き更新
   個別: portfolio-todo-app リポジトリ     # push更新
   ```

3. **バージョン管理**: Gitの履歴で管理
   ```
   git log --oneline
   # 2024-12-15: 機能追加
   # 2024-12-10: 初版作成
   ```

## 📝 サブエージェントへの指示

### Phase 6 実行プロンプト
```markdown
あなたはGitHub公開担当者です。

【前提確認】
1. 現在の作業ディレクトリ: ~/Desktop/AI-Apps/{app-name}-agent/
2. worktreeはマージ済みか確認
3. PROJECT_INFO.yamlでPortfolio App確認
4. project/public/ に公開ファイルが生成されているか確認

【公開方式の選択】
以下のいずれか、または両方を実行：

A. 統合ポートフォリオ（複数アプリ管理）- 推奨
   ```bash
   python3 ./_workflow/src/simplified_github_publisher.py .
   ```
   結果: ai-agent-portfolio/{app-name}/ に配置

B. 個別リポジトリ（このアプリ専用）
   ```bash
   python3 ./_workflow/src/github_portfolio_publisher.py .
   ```
   結果: portfolio-{app-name} リポジトリ作成

【公開ファイルソース】
- project/public/ 配下のファイルをGitHubに公開
- clean_public()が開発ツール・テスト・認証情報を自動除外

【slug管理の原則】
- create_new_app.commandは日付プレフィックスなしのフォルダ作成
- 同じアプリ名は同じslug/リポジトリ使用（フォルダ名は固定、内容のみ差し替え）
- バージョン管理はGit履歴で実施

【成果物】
- GitHubでの公開URL
- GitHub Pages URL（設定した場合）
```

## ✅ チェックリスト

### Claude Codeが確実に実行するために

- [ ] Phase 5完了後、PROJECT_INFO.yaml確認
- [ ] Portfolio Appの場合のみPhase 6実行
- [ ] project/public/ が生成されているか確認
- [ ] worktreeマージ済み確認
- [ ] 専用環境のmainブランチから実行
- [ ] 公開方式を選択（統合/個別/両方）
- [ ] slugによる重複管理（日付除去）
- [ ] 公開URLを表示

## 🚨 注意事項

### やってはいけないこと
- ❌ worktreeから直接push
- ❌ 日付付きフォルダ名でGitHubリポジトリ作成
- ❌ Client AppをGitHubに公開

### 必ず守ること
- ✅ 専用環境のmainブランチから公開
- ✅ slug形式で管理（todo-app, calculator等）
- ✅ 同じアプリは同じ場所を更新
