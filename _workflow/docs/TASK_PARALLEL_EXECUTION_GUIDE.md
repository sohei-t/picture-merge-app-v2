# 📚 Taskツール並列実行ガイド

## 🎯 目的

このガイドは、git-worktree-agentワークフローでTaskツールを正しく使用し、並列処理を実現するための実装ガイドです。

## ⚠️ 最重要原則

### ワークフローの本来の設計思想
- **Git worktree**: 物理的なワーキングツリーの分離
- **Taskツール**: サブエージェントによるタスク分業
- **コンテキスト分離**: 各タスクが自身の役割に集中
- **並列処理**: 複数タスクの同時実行による高速化

## ❌ よくある間違い（現在の問題）

```python
# 間違い1: 自分で直接実装
def execute_phase_wrong():
    cd("./worktrees/mission-todo/")
    create_file("src/index.js")
    run_tests()
    # → Taskツール未使用、並列処理不可、コンテキスト肥大化

# 間違い2: 順次実行
def execute_tasks_wrong():
    execute_frontend()   # 15分
    execute_backend()    # 10分
    execute_database()   # 5分
    # → 合計30分（並列なら15分で済む）
```

## ✅ 正しい実装方法

### 1. 単一タスクの実行

```python
# 正しい実装: Taskツールでサブエージェントを起動
Task(
    description="Requirements Analysis",
    subagent_type="general-purpose",
    prompt="""
    あなたは要件定義アナリストです。

    【作業環境】
    - 作業ディレクトリ: ./worktrees/mission-todo/

    【タスク】
    - 要件定義書を作成
    - REQUIREMENTS.mdに出力

    【完了条件】
    - 明確な要件定義
    - テスト可能な成功基準
    """
)
```

### 2. 並列タスクの実行

```python
# 正しい実装: 1つのメッセージで複数Task呼び出し
# 以下の3つを同じメッセージで実行（重要！）

Task(
    description="Frontend Development",
    subagent_type="general-purpose",
    prompt=FRONTEND_PROMPT
)

Task(
    description="Backend Development",
    subagent_type="general-purpose",
    prompt=BACKEND_PROMPT
)

Task(
    description="Database Implementation",
    subagent_type="general-purpose",
    prompt=DATABASE_PROMPT
)

# → 3つが並列実行される（15分で完了）
```

## 📊 実行パターン別ガイド

### Phase 1: 要件定義・計画（順次実行）

```yaml
execution_pattern: sequential
reason: "後続タスクが前タスクの成果物に依存"

tasks:
  1. Requirements Analysis:
     - Task(requirements_prompt)
     - 出力: REQUIREMENTS.md

  2. WBS Creation:
     - Task(wbs_prompt)
     - 入力: REQUIREMENTS.md
     - 出力: WBS.json

  3. Test Design:
     - Task(test_design_prompt)
     - 入力: WBS.json
     - 出力: tests/*.test.js
```

### Phase 2: 実装（並列実行）

```yaml
execution_pattern: parallel
reason: "独立したコンポーネント"

# 1メッセージで同時実行
parallel_tasks:
  - Task(frontend_prompt)   # 15分
  - Task(backend_prompt)    # 10分
  - Task(database_prompt)   # 5分

total_time: 15分（最長タスクの時間）
```

### Phase 3: テスト・修正（条件付き並列）

```yaml
execution_pattern: conditional_parallel
reason: "テスト結果に応じた修正"

flow:
  1. Test Execution:
     - Task(test_runner_prompt)

  2. If failures (parallel fixes):
     - Task(fix_frontend_prompt)
     - Task(fix_backend_prompt)
     - Task(fix_database_prompt)

  3. Re-test:
     - Task(test_runner_prompt)
```

## 🔍 並列実行の判定基準

### 並列実行可能な条件

```yaml
can_parallel_execute:
  - 依存関係なし: タスク間に入出力の依存がない
  - リソース競合なし: 同じファイルを編集しない
  - 順序不問: 実行順序が結果に影響しない

examples:
  - Frontend/Backend/Database実装
  - 複数コンポーネントのテスト
  - ドキュメント生成タスク
```

### 順次実行が必要な条件

```yaml
must_sequential_execute:
  - 依存関係あり: 前タスクの出力が必要
  - リソース競合: 同じファイルを更新
  - 順序重要: 実行順序が結果に影響

examples:
  - 要件定義 → WBS作成
  - テスト実行 → 修正
  - ビルド → デプロイ
```

## 📈 パフォーマンス比較

| フェーズ | 順次実行（現在） | 並列実行（改善後） | 短縮率 |
|---------|-----------------|-------------------|--------|
| Phase 2（実装） | 30分 | 15分 | 50% |
| Phase 3（テスト修正） | 20分 | 10分 | 50% |
| Phase 5（完成処理） | 15分 | 5分 | 66% |
| **合計** | **65分** | **30分** | **54%** |

## 🛠️ 実装チェックリスト

### 各フェーズ開始前

```markdown
□ Taskツールを使用する準備はできているか？
□ 並列実行可能なタスクを特定したか？
□ プロンプトテンプレートを準備したか？
□ 自分で直接実装していないか？（重要）
```

### Task呼び出し時

```markdown
□ description: 明確なタスク名を設定
□ subagent_type: "general-purpose"を指定
□ prompt: 詳細な指示を含む
□ 並列タスクは1メッセージで呼び出し
```

### 実行後の確認

```markdown
□ すべてのタスクが完了したか？
□ 期待される成果物が生成されたか？
□ テストが合格しているか？
□ 次のフェーズに進む準備ができたか？
```

## 💡 トラブルシューティング

### Q: Taskツールが使用されない
A: CLAUDE.mdの冒頭の警告を確認。自分で直接実装していないか確認。

### Q: 並列実行されない
A: 複数のTaskを別々のメッセージで送信していないか確認。1つのメッセージで送信すること。

### Q: サブエージェントがエラーを返す
A: プロンプトに作業ディレクトリと具体的なタスクが明記されているか確認。

### Q: 実行時間が短縮されない
A: 依存関係を見直し、本当に並列実行可能か再評価。

## 📝 実装例：Todoアプリ開発

```python
# Phase 1: 要件定義（順次）
task1 = Task(requirements_prompt)
# task1完了を待つ

task2 = Task(wbs_prompt)
# task2完了を待つ

# Phase 2: 実装（並列 - 1メッセージ）
Task(frontend_prompt)
Task(backend_prompt)
Task(database_prompt)
# 3つ同時実行

# Phase 3: テスト
test_result = Task(test_prompt)

# Phase 4: 修正（必要に応じて並列）
if test_result.has_failures:
    Task(fix_frontend_prompt)
    Task(fix_backend_prompt)
    # 2つ同時実行
```

## 🎯 まとめ

### 成功のポイント
1. **Taskツールを必ず使用** - 自分で直接実装しない
2. **並列タスクは1メッセージ** - 複数Taskを同時呼び出し
3. **コンテキスト分離** - 各エージェントが専門領域に集中
4. **依存関係の明確化** - 並列可能なタスクを正しく識別

### 期待される効果
- 実行時間: 50-60%短縮
- 品質向上: 各エージェントが役割に集中
- スケーラビリティ: タスク数が増えても対応可能

---

**重要**: このガイドに従って、すべてのワークフロー実行でTaskツールを使用し、並列処理を実現してください。

---

## 🆕 Agent Teams パターン（Opus 4.6 対応）

### 概要

Agent Teams は Claude Code の実験的機能（`CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`）で、
チームメイト間のリアルタイムメッセージングが可能です。

### 使用するツール

```yaml
Agent_Teams_ツール:
  TeamCreate: "チームを作成（team_name を指定）"
  Task: "team_name + name パラメータでチームメイトを起動"
  SendMessage:
    message: "type='message' でチームメイト間メッセージ送信"
    shutdown: "type='shutdown_request' でチームメイト終了要求"
    shutdown_response: "type='shutdown_response' でシャットダウン応答"
  TaskCreate_etc: "共有タスクリストで進捗管理"

実行フロー:
  1: "TeamCreate(team_name='チーム名') でチーム作成"
  2: "Task(team_name='チーム名', name='メイト名', ...) でチームメイト起動"
  3: "SendMessage(type='message', recipient='メイト名', ...) でメッセージ交換"
  4: "SendMessage(type='shutdown_request', recipient='メイト名', ...) で終了"
```

### Task ツール vs Agent Teams の判断基準

```yaml
判断基準:
  Agent_Teams_を使う場合:
    - "チームメイト間で API仕様・データモデル等の調整が必要"
    - "成果物の整合性をリアルタイムに確保したい"
    - "例: Phase 2 の Frontend / Backend / DB 間連携"

  Task_ツールを使う場合:
    - "独立した作業で相互依存が少ない"
    - "トークン消費を節約したい"
    - "Agent Teams が不安定な場合のフォールバック"
    - "例: Phase 1 の2案並列生成、Phase 5 の独立タスク"

  フェーズ別推奨:
    Phase_1: "Task ツール"
    Phase_2: "Agent Teams 推奨（Task フォールバック）"
    Phase_3: "Task ツール"
    Phase_4: "Agent Teams オプション（Task フォールバック）"
    Phase_5: "Task ツール"
```

### Phase 2: Agent Teams 実装パターン

```yaml
team_structure:
  lead: "統合担当（親エージェント）"
  teammates:
    frontend:
      name: "Frontend Developer"
      worktree: "phase2-impl-prototype-a/"
    backend:
      name: "Backend Developer"
      worktree: "phase2-impl-prototype-b/"
    database:
      name: "Database/Architecture Developer"
      worktree: "phase2-impl-prototype-c/"

チームメイト間メッセージング例:
  api_spec_共有:
    Backend → Frontend: |
      POST /api/users レスポンス形式を確定しました:
      { "id": "uuid", "name": "string", "email": "string", "token": "jwt" }
      フロントエンドのAPI呼び出しをこの形式に合わせてください。

  data_model_共有:
    DB_Dev → Backend: |
      users テーブルに role カラム（VARCHAR(20)、デフォルト 'user'）を追加しました。
      API側で role フィールドの読み書きを対応してください。

  auth_flow_調整:
    Backend → Frontend: |
      認証はJWTを使用。ログイン成功時に token を返すので、
      以降のリクエストで Authorization: Bearer {token} ヘッダーを付与してください。
      トークン有効期限は24時間です。
```

### Phase 4: Agent Teams 最適化パターン

```yaml
team_structure:
  lead: "品質管理リード"
  teammates:
    performance:
      name: "Performance Optimizer"
      worktree: "phase4-quality-opt-a/"
    quality:
      name: "Code Quality Optimizer"
      worktree: "phase4-quality-opt-b/"

連携例:
  Performance → Quality: |
    バンドルサイズ分析の結果、lodash が全体の30%を占めています。
    リファクタリング時に lodash の個別インポートへの変更を検討してください。

  Quality → Performance: |
    認証ミドルウェアをリファクタリングしました。
    パフォーマンステストで認証付きエンドポイントの応答時間を再測定してください。
```