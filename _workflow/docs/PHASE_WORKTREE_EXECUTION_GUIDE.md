# 🏗️ Phase別Worktree実行ガイド v2.0

**このガイドはPhase別worktree自律開発システムの実行手順書です**

> **v2.0 変更点:**
> - Phase 1を2段階構成に変更（Phase 1-A: 要件分析、Phase 1-B: 設計・計画）
> - `--skip-file-check` オプション追加（早期Phase評価時のファイルチェックスキップ）
> - `--auto-merge` オプションで自動マージ・同期を実行
> - Phase 5のタスク実行順序を明確化（documenter_agent.pyは逐次実行）
> - Worktree-Branchマッピングの明確化

---

## 📌 前提条件

`create_new_app.command` 実行時に、以下の9個のworktreeが自動作成されています：

```
worktrees/
├── phase1-planning-a/           # 計画案A（保守的）
├── phase1-planning-b/           # 計画案B（革新的）
├── phase2-impl-prototype-a/     # 実装プロトタイプA
├── phase2-impl-prototype-b/     # 実装プロトタイプB
├── phase2-impl-prototype-c/     # 実装プロトタイプC
├── phase3-testing/              # テスト環境
├── phase4-quality-opt-a/        # 最適化アプローチA
├── phase4-quality-opt-b/        # 最適化アプローチB
└── phase5-delivery/             # 最終成果物
```

**詳細な設計:** `PHASE_WORKTREE_AUTONOMOUS_STRATEGY.md`

---

## 🎯 実行原則

### 1. 並列Task実行の徹底

**必ず1つのメッセージで複数Taskを同時実行:**

```yaml
Phase 1: 2つのTaskを1メッセージで実行
Phase 2: 3つのTaskを1メッセージで実行
Phase 3: 単一Task（テストループ）
Phase 4: 2つのTaskを1メッセージで実行
Phase 5: 3つのTaskを1メッセージで実行
```

### 2. 自律評価の活用

各Phaseの並列タスク完了後、`autonomous_evaluator.py` で最良を選択：

```bash
python3 ~/Desktop/git-worktree-agent/_workflow/src/autonomous_evaluator.py . <worktree1> <worktree2> ...
```

### 3. mainブランチ統合

評価で選ばれたworktreeを main にマージ：

```bash
git merge <selected-branch>
```

---

## 🚀 Phase別実行フロー

### Phase 0: 初期化（完了済み）

`create_new_app.command` で既に完了しています。

**確認:**
```bash
ls -la worktrees/
# 9個のworktreeが存在することを確認
```

---

### Phase 1: 計画（2段階構成 - v2.0）

#### 📌 Phase 1の構成

```yaml
Phase 1-A（要件分析・評価・選択）:
  実行: ステップ1 → ステップ2
  必須成果物: REQUIREMENTS.md
  オプション成果物: なし（この時点ではIMAGE_PROMPTS.json等は不要）
  評価オプション: --skip-file-check（IMAGE_PROMPTS.json等の存在チェックをスキップ）

Phase 1-B（設計・計画・プロンプト生成）:
  実行: ステップ3以降（選択された計画案のworktreeで継続）
  必須成果物: SPEC.md, TECH_STACK.md, WBS.json
  オプション成果物: IMAGE_PROMPTS.json, AUDIO_PROMPTS.json（プロジェクトに応じて）
```

#### ステップ1: 並列Task実行（Phase 1-A）

**必ず1つのメッセージで2つのTaskを同時実行:**

```yaml
Task 1: Planning A - 保守的アプローチ
  subagent_type: "general-purpose"
  prompt: |
    あなたは Requirements Analyst（保守的アプローチ）です。

    【作業環境】
    - 作業ディレクトリ: ./worktrees/phase1-planning-a/
    - このディレクトリ内でのみファイル操作を行う

    【Phase情報】
    - 現在のPhase: Phase 1 - 計画
    - このworktreeの目的: 保守的・安定重視の計画案作成
    - 並列開発中: phase1-planning-b（革新的アプローチ）

    【タスク】
    以下のファイルを作成:

    1. REQUIREMENTS.md
       - ユーザーストーリー
       - 機能要件
       - 非機能要件（保守性・安定性重視）

    2. WBS.json
       - タスク分割（細かく・確実に）
       - 依存関係の明確化
       - クリティカルパスの特定
       - 実績のある技術スタックを選択

    3. CRITICAL_PATH.md
       - クリティカルパスの詳細分析
       - リスク評価（保守的に）
       - スケジュール見積もり

    4. ARCHITECTURE.md
       - 堅実なアーキテクチャ設計
       - 実績のあるパターンを使用
       - 保守性・可読性を最優先

    【アプローチの特徴】
    - 実績のある技術・パターンを選択
    - 堅実な設計
    - リスク最小化
    - 保守性・可読性優先
    - 段階的な実装計画

    【完了条件】
    - 全ファイル作成完了
    - WBS.jsonが正しいJSON形式
    - クリティカルパスが明確
    - コミット完了: "feat(phase1): conservative planning approach"

Task 2: Planning B - 革新的アプローチ
  subagent_type: "general-purpose"
  prompt: |
    あなたは Requirements Analyst（革新的アプローチ）です。

    【作業環境】
    - 作業ディレクトリ: ./worktrees/phase1-planning-b/
    - このディレクトリ内でのみファイル操作を行う

    【Phase情報】
    - 現在のPhase: Phase 1 - 計画
    - このworktreeの目的: 革新的・効率重視の計画案作成
    - 並列開発中: phase1-planning-a（保守的アプローチ）

    【タスク】
    以下のファイルを作成:

    1. REQUIREMENTS.md
       - ユーザーストーリー
       - 機能要件
       - 非機能要件（効率性・革新性重視）

    2. WBS.json
       - タスク分割（大胆に・効率的に）
       - 依存関係の最適化
       - クリティカルパスの短縮
       - 最新技術スタックを積極採用

    3. CRITICAL_PATH.md
       - クリティカルパスの最適化分析
       - 効率化のポイント
       - 攻めのスケジュール

    4. ARCHITECTURE.md
       - モダンなアーキテクチャ設計
       - 最新のベストプラクティス採用
       - パフォーマンス・DX最優先

    【アプローチの特徴】
    - 最新技術・パターンを積極採用
    - 革新的な設計
    - 効率化・高速化優先
    - パフォーマンス・DX重視
    - 大胆な実装計画

    【完了条件】
    - 全ファイル作成完了
    - WBS.jsonが正しいJSON形式
    - クリティカルパスが最適化
    - コミット完了: "feat(phase1): innovative planning approach"
```

#### ステップ2: 自律評価（Phase 1-A完了）

```bash
# 2つの計画案を評価（--skip-file-check で IMAGE_PROMPTS.json チェックをスキップ）
# --auto-merge で自動的にmainへマージ＆全worktreeへ同期
python3 ~/Desktop/git-worktree-agent/_workflow/src/autonomous_evaluator.py . \
  phase1-planning-a phase1-planning-b \
  --auto-merge --skip-file-check --phase=phase1

# 出力例:
# 🏆 EVALUATION RESULTS
# ============================================================
# phase1-planning-b: 87.3/100
# phase1-planning-a: 78.5/100
#
# ✅ SELECTED: phase1-planning-b
# 🔄 Auto-merging to main...
# 🔄 Syncing to all worktrees...
# ============================================================

# ⚠️ --skip-file-check の役割:
# Phase 1-AではIMAGE_PROMPTS.jsonやAUDIO_PROMPTS.jsonはまだ生成されていないため、
# これらのファイル存在チェックをスキップしてエラーを防ぎます
```

#### ステップ3: Phase 1-B 設計・計画の実行

```bash
# Phase 1-A完了後、選択された計画案を基に設計・計画を進める
# 以下のタスクは main ブランチまたは選択されたworktreeで実行:

# 1. SPEC.md 作成（仕様設計）
# 2. TECH_STACK.md 作成（技術選定）
# 3. WBS.json 作成（タスク分割）
# 4. IMAGE_PROMPTS.json 作成（画像生成が必要な場合）
# 5. AUDIO_PROMPTS.json 作成（音声生成が必要な場合）

# これらが完了したら、再度評価してPhase 2用worktreeに同期:
python3 ~/Desktop/git-worktree-agent/_workflow/src/autonomous_evaluator.py . \
  phase1-planning-a phase1-planning-b \
  --auto-merge

# 確認
git log --oneline -5
ls -la IMAGE_PROMPTS.json AUDIO_PROMPTS.json SPEC.md TECH_STACK.md
```

---

### Phase 2: 実装（3アーキテクチャ並列 → UX重視評価） - v10.0更新

**🎯 アーキテクチャ差別化戦略:**
シンプル版に偏らないよう、異なるアーキテクチャで並列開発し、UXを最優先基準に評価します。

#### 🆕 Agent Teams 実行フロー（推奨 - v10.0）

```yaml
agent_teams_phase2:
  概要: |
    Agent Teams を使用して3名のチームメイトがリアルタイム連携しながら実装。
    各チームメイトは異なるworktreeで作業し、API仕様・データモデル・認証フローを
    メッセージで調整します。

  チームメイトとworktreeの対応:
    Frontend_Developer: "worktrees/phase2-impl-prototype-a/"
    Backend_Developer: "worktrees/phase2-impl-prototype-b/"
    DB_Architecture_Developer: "worktrees/phase2-impl-prototype-c/"

  実行手順（具体的なツール呼び出し）:
    1_チーム作成: |
      TeamCreate(team_name="phase2-impl")
    2_チームメイト起動（3つの Task を1メッセージで同時実行）: |
      Task(subagent_type="general-purpose", team_name="phase2-impl",
           name="frontend-dev", prompt="...worktree: phase2-impl-prototype-a/...")
      Task(subagent_type="general-purpose", team_name="phase2-impl",
           name="backend-dev", prompt="...worktree: phase2-impl-prototype-b/...")
      Task(subagent_type="general-purpose", team_name="phase2-impl",
           name="db-dev", prompt="...worktree: phase2-impl-prototype-c/...")
    3_リアルタイム調整（SendMessage でメッセージ交換）: |
      チームメイト間は SendMessage(type="message") で直接やり取り:
      - backend-dev → frontend-dev: API仕様（エンドポイント、レスポンス形式）
      - db-dev → backend-dev: スキーマ変更（カラム追加、型定義）
      - backend-dev → 全員: 認証フロー（JWT仕様、ヘッダー形式）
    4_統合確認: |
      リードが各チームメイトの成果物を確認
      - Frontend→Backend API呼び出しが動作するか
      - Backend→Database CRUD操作が正常か
      - 認証フローがエンドツーエンドで通るか
    5_シャットダウン: |
      SendMessage(type="shutdown_request", recipient="frontend-dev", ...)
      SendMessage(type="shutdown_request", recipient="backend-dev", ...)
      SendMessage(type="shutdown_request", recipient="db-dev", ...)
    6_評価_マージ: |
      autonomous_evaluator_ux.py で評価 → mainにマージ

  フォールバック: |
    Agent Teams が不安定な場合、下記の Task ツール版を使用
```

#### ステップ1: 並列Task実行（UX最優先版 - Task ツール版）

**必ず1つのメッセージで3つのTaskを同時実行:**

```yaml
Task 1: Prototype A - マイクロサービスアーキテクチャ
  subagent_type: "general-purpose"
  prompt: |
    あなたはUX重視のFull Stack Developer（マイクロサービス担当）です。

    【作業環境】
    - 作業ディレクトリ: ./worktrees/phase2-impl-prototype-a/
    - Phase 1の計画を参照（mainブランチのREQUIREMENTS.md, WBS.json, TECH_STACK.md等）

    【Phase情報】
    - 現在のPhase: Phase 2 - 実装
    - このworktreeの目的: マイクロサービスアーキテクチャでUX最適化
    - 並列開発中: prototype-b（モノリシック）, prototype-c（サーバーレス）

    【アーキテクチャ方針】
    - サービス分割型アーキテクチャ
    - 各機能を独立したサービスとして実装
    - API Gateway + 複数マイクロサービス
    - 疎結合・高スケーラビリティ

    【UX重視ポイント】
    - レスポンス速度の最適化（並列処理活用）
    - 段階的ローディング（Progressive Loading）
    - エラーハンドリングの明確化
    - Core Web Vitals準拠（LCP < 2.5s, FID < 100ms, CLS < 0.1）

    【評価基準の認識】
    このプロトタイプは以下の基準で評価されます（UX最優先）:
    - ユーザー体験 (35%) ← 最優先！
    - 機能完成度 (20%)
    - パフォーマンス (15%)
    - テスト品質 (15%)
    - セキュリティ (10%)
    - 保守性 (5%)

    【タスク】
    1. SUBAGENT_PROMPT_TEMPLATE.md の「8. Frontend Developer」を参照してUI実装
    2. SUBAGENT_PROMPT_TEMPLATE.md の「9. Backend Developer」を参照してAPI実装
    3. テストを同時作成（TDD）
    4. UX最適化（パフォーマンス、アクセシビリティ、レスポンシブ）
    5. 動作確認
    6. コミット

    【完了条件】
    - 全機能が動作
    - テスト合格率 70%以上
    - UX評価項目を満たす（特にLCP, FID, CLS）
    - コミット: "feat(phase2-a): microservices architecture with UX focus"

Task 2: Prototype B - モノリシックアーキテクチャ
  subagent_type: "general-purpose"
  prompt: |
    あなたはUX重視のFull Stack Developer（モノリシック担当）です。

    【作業環境】
    - 作業ディレクトリ: ./worktrees/phase2-impl-prototype-b/
    - Phase 1の計画を参照

    【Phase情報】
    - 現在のPhase: Phase 2 - 実装
    - このworktreeの目的: モノリシックアーキテクチャでUX最適化
    - 並列開発中: prototype-a（マイクロサービス）, prototype-c（サーバーレス）

    【アーキテクチャ方針】
    - 単一アプリケーション型アーキテクチャ
    - レイヤー分離（UI/Business/Data）
    - 統合された一体型システム
    - シンプル・保守性重視

    【UX重視ポイント】
    - 高速な初期表示（Single Bundle最適化）
    - 一貫したユーザー体験
    - オフライン対応・PWA化
    - Core Web Vitals準拠（LCP < 2.5s, FID < 100ms, CLS < 0.1）

    【評価基準の認識】
    このプロトタイプは以下の基準で評価されます（UX最優先）:
    - ユーザー体験 (35%) ← 最優先！
    - 機能完成度 (20%)
    - パフォーマンス (15%)
    - テスト品質 (15%)
    - セキュリティ (10%)
    - 保守性 (5%)

    【タスク】
    1. SUBAGENT_PROMPT_TEMPLATE.md の「8. Frontend Developer」を参照してUI実装
    2. SUBAGENT_PROMPT_TEMPLATE.md の「9. Backend Developer」を参照してAPI実装
    3. 高度なテストを作成
    4. UX最適化（パフォーマンス、アクセシビリティ、レスポンシブ）
    5. PWA対応
    6. コミット

    【完了条件】
    - 全機能が高品質で動作
    - テスト合格率 80%以上
    - UX評価項目を満たす（特にアクセシビリティ）
    - コミット: "feat(phase2-b): monolithic architecture with UX focus"

Task 3: Prototype C - サーバーレスアーキテクチャ
  subagent_type: "general-purpose"
  prompt: |
    あなたはUX重視のFull Stack Developer（サーバーレス担当）です。

    【作業環境】
    - 作業ディレクトリ: ./worktrees/phase2-impl-prototype-c/
    - Phase 1の計画を参照

    【Phase情報】
    - 現在のPhase: Phase 2 - 実装
    - このworktreeの目的: サーバーレスアーキテクチャでUX最適化
    - 並列開発中: prototype-a（マイクロサービス）, prototype-b（モノリシック）

    【アーキテクチャ方針】
    - イベント駆動型アーキテクチャ
    - 関数ベースの実装（FaaS）
    - スケーラブル・コスト最適化
    - インフラレス管理

    【UX重視ポイント】
    - 高速なコールドスタート対策
    - リアルタイム性の確保
    - レスポンシブデザイン（Core Web Vitals最適化）
    - Core Web Vitals準拠（LCP < 2.5s, FID < 100ms, CLS < 0.1）

    【評価基準の認識】
    このプロトタイプは以下の基準で評価されます（UX最優先）:
    - ユーザー体験 (35%) ← 最優先！
    - 機能完成度 (20%)
    - パフォーマンス (15%)
    - テスト品質 (15%)
    - セキュリティ (10%)
    - 保守性 (5%)

    【タスク】
    1. SUBAGENT_PROMPT_TEMPLATE.md の「8. Frontend Developer」を参照してUI実装
    2. SUBAGENT_PROMPT_TEMPLATE.md の「9. Backend Developer」を参照してAPI実装
    3. 実用的なテストを作成
    4. UX最適化（パフォーマンス、アクセシビリティ、レスポンシブ）
    5. サーバーレス最適化
    6. コミット

    【完了条件】
    - 全機能が動作
    - テスト合格率 75%以上
    - UX評価項目を満たす（特にレスポンシブデザイン）
    - コミット: "feat(phase2-c): serverless architecture with UX focus"
```

#### ステップ2: UX重視の自律評価（v9.0 + v2.0更新）

```bash
# 3つのプロトタイプをUX最優先で評価し、自動マージ
python3 ~/Desktop/git-worktree-agent/_workflow/src/autonomous_evaluator_ux.py . \
  phase2-impl-prototype-a phase2-impl-prototype-b phase2-impl-prototype-c \
  --auto-merge --phase=phase2

# ⚠️ v2.0で追加されたオプション:
# --auto-merge: 選択されたworktreeを自動でmainにマージし全worktreeに同期
# --phase=phase2: Phase固有のファイルチェックを適用

# 評価軸（UX最優先 - v9.0）:
# - ユーザー体験 (35%) ← 最優先！
#   * パフォーマンスUX (LCP < 2.5s, FID < 100ms, CLS < 0.1)
#   * ユーザビリティ（使いやすさ、直感性）
#   * アクセシビリティ（WCAG 2.1 AA準拠）
#   * レスポンシブデザイン（モバイル/デスクトップ対応）
# - 機能完成度 (20%)
# - パフォーマンス (15%)
# - テスト品質 (15%)
# - セキュリティ (10%)
# - 保守性 (5%)

# 出力例:
# 🏆 UX-FOCUSED EVALUATION RESULTS (v9.0)
# ============================================================
# phase2-impl-prototype-b (Monolithic): 92.3/100
#   - User Experience: 33.5/35 ⭐ (Excellent accessibility)
#   - Feature Completeness: 18.0/20
#   - Performance: 13.5/15
#   - Test Quality: 14.0/15
#   - Security: 9.5/10
#   - Maintainability: 3.8/5
#
# phase2-impl-prototype-a (Microservices): 87.1/100
#   - User Experience: 31.2/35 (Good performance)
#   - Feature Completeness: 17.5/20
#   - Performance: 14.5/15
#   - ...
#
# phase2-impl-prototype-c (Serverless): 83.7/100
#   - User Experience: 29.8/35 (Good responsive design)
#   - ...
#
# ✅ SELECTED: phase2-impl-prototype-b (Monolithic)
# 理由: アクセシビリティとユーザビリティで最高評価
# ============================================================
```

#### ステップ3: mainにマージ（--auto-merge使用時は自動実行）

```bash
# --auto-merge オプションを使用した場合、このステップは自動実行されます
# 手動で実行する場合のみ以下を実行:
git merge phase/impl-prototype-b  # 最高スコアのworktree

# 確認
git log --oneline -5
ls -la src/ index.html
```

---

### Phase 3: テスト（100%合格まで継続）

#### 単一Task実行（ループ）

```yaml
Task: Testing and Bug Fixing
  subagent_type: "general-purpose"
  prompt: |
    あなたは QA Engineer です。

    【作業環境】
    - 作業ディレクトリ: ./worktrees/phase3-testing/
    - mainブランチの最新コードをテスト

    【Phase情報】
    - 現在のPhase: Phase 3 - テスト
    - このworktreeの目的: 作成済みテスト100%合格

    【タスク】
    1. mainブランチの最新コードを phase3-testing にマージ
    2. 全テストを実行
    3. 失敗があれば修正（無制限に繰り返す）
    4. テスト100%合格まで継続

    【完了条件（妥協なし）】
    - 作成済みテスト: 100%合格（必須）
    - 実カバレッジ: 70%以上
    - クリティカルパス: 100%カバー
    - エラーフリーで動作

    【ループ実行】
    while (test_pass_rate < 100%):
        修正 → テスト実行 → 評価

    コミット: "fix(phase3): all tests passing"
```

#### mainにマージ

```bash
# テスト100%合格後
git merge phase/testing
```

---

### Phase 4: 品質改善（2最適化案 → 自律評価）

#### ステップ1: 並列Task実行

**必ず1つのメッセージで2つのTaskを同時実行:**

```yaml
Task 1: Quality Optimization A - カバレッジ重視
  subagent_type: "general-purpose"
  prompt: |
    あなたは Quality Engineer（カバレッジ重視）です。

    【作業環境】
    - 作業ディレクトリ: ./worktrees/phase4-quality-opt-a/
    - mainブランチの最新コードを改善

    【Phase情報】
    - 現在のPhase: Phase 4 - 品質改善
    - このworktreeの目的: カバレッジ80-90%達成
    - 並列開発中: quality-opt-b（パフォーマンス重視）

    【改善目標】
    - カバレッジ 80-90% 達成
    - エッジケース対応
    - テスト追加（特に重要機能）

    【タスク】
    1. カバレッジレポート分析
    2. 未カバー部分のテスト追加
    3. エッジケースのテスト追加
    4. テスト実行（100%合格維持）

    【完了条件】
    - カバレッジ 80-90%
    - 全テスト合格（100%）
    - コミット: "test(phase4-a): improve coverage to 80-90%"

Task 2: Quality Optimization B - パフォーマンス重視
  subagent_type: "general-purpose"
  prompt: |
    あなたは Performance Engineer です。

    【作業環境】
    - 作業ディレクトリ: ./worktrees/phase4-quality-opt-b/
    - mainブランチの最新コードを改善

    【Phase情報】
    - 現在のPhase: Phase 4 - 品質改善
    - このworktreeの目的: パフォーマンス最適化
    - 並列開発中: quality-opt-a（カバレッジ重視）

    【改善目標】
    - パフォーマンス最適化
    - ボトルネック解消
    - リソース使用量削減

    【タスク】
    1. パフォーマンスプロファイリング
    2. ボトルネック特定・解消
    3. メモリ使用量最適化
    4. ベンチマーク実行

    【完了条件】
    - 応答時間 20%以上改善
    - メモリ使用量 15%以上削減
    - 全テスト合格（100%）
    - コミット: "perf(phase4-b): optimize performance"
```

#### ステップ2: 自律評価

```bash
python3 ~/Desktop/git-worktree-agent/_workflow/src/autonomous_evaluator.py . \
  phase4-quality-opt-a phase4-quality-opt-b
```

#### ステップ3: mainにマージ

```bash
git merge phase/quality-opt-a  # または opt-b
```

---

### Phase 5: 完成処理（逐次実行 - v2.0更新）

#### ⚠️ 実行順序の重要な変更（v2.0）

**documenter_agent.pyは内部で複数タスクを逐次実行するため、並列Task実行ではありません:**

```yaml
# 実行順序（documenter_agent.py が自動で実行）
1. README.md 生成
2. about.html 生成（frontend-design skill使用）
3. audio_script.txt 生成
4. explanation.mp3 生成（Gemini TTS優先、GCP TTSフォールバック）
5. launch_app.command 生成

# 上記は documenter_agent.py 1回の実行で全て完了します
# 音声生成の優先順位:
#   1. Gemini 2.5 Flash Preview TTS（GEMINI_API_KEY設定時）
#   2. GCP Text-to-Speech（GCP認証ファイル存在時）
#   3. スキップ（両方失敗時、理由をREADME.mdに記録）
```

#### 実行手順（シンプル化）

```yaml
Task: Phase 5 完成処理
  subagent_type: "general-purpose"
  prompt: |
    あなたは Technical Writer & DevOps Engineer です。

    【作業環境】
    - 作業ディレクトリ: ./worktrees/phase5-delivery/
    - mainブランチの完成コードをドキュメント化

    【タスク】
    1. mainブランチの最新コードを phase5-delivery にマージ
       ```bash
       cd ./worktrees/phase5-delivery/
       git merge main
       ```

    2. documenter_agent.py 実行（全成果物を一括生成）
       ```bash
       python3 ~/Desktop/git-worktree-agent/_workflow/src/documenter_agent.py
       ```

    3. 生成物確認:
       - README.md（技術仕様）
       - about.html（frontend-design skill使用、ビジュアル的に魅力的）
       - audio_script.txt（音声スクリプト）
       - explanation.mp3（Gemini TTS優先、GCP TTSフォールバック）
       - launch_app.command（実行権限付き）

    4. launch_app.command 動作確認
       ```bash
       chmod +x launch_app.command
       ./launch_app.command
       ```

    5. project/public/ 構成確認
       ```bash
       ls -la project/public/
       # 必須: index.html, about.html, README.md, assets/
       # オプション: explanation.mp3
       ```

    【完了条件】
    - 全ドキュメント生成完了
    - about.htmlがビジュアル的に魅力的
    - launch_app.command が動作確認済み
    - project/public/ が正しく構成されている
    - コミット: "docs(phase5): generate all deliverables"

    【音声生成の認証について】
    - documenter_agent.py は以下の優先順位で音声生成を試行:
      1. **Gemini TTS（推奨）**: GEMINI_API_KEY 環境変数が設定されている場合
      2. **GCP TTS（フォールバック）**: GCP認証ファイルがある場合
    - GCP認証の検出順序:
      1. ./ai-agents-config/credentials/gcp.json（ローカル設定）
      2. ./credentials/gcp-workflow-key.json（プロジェクト内）
      3. ../credentials/gcp-workflow-key.json（親ディレクトリ）
      4. ~/.config/ai-agents/credentials/gcp/default.json（グローバル設定）
    - 両方未設定の場合: explanation.mp3 はスキップされ、理由が記録されます
```

#### mainにマージ

```bash
git merge phase/delivery
```

---

### Phase 5.5: DELIVERY生成（自動実行）

```bash
# Phase 5完了直後に自動実行
python3 ~/Desktop/git-worktree-agent/_workflow/src/delivery_organizer.py

# 確認:
ls DELIVERY/<app-name>/
# index.html, about.html, assets/, explanation.mp3, README.md
```

---

### Phase 6: GitHub公開（Portfolio Appのみ、自動実行）

```bash
# Phase 5.5完了直後に自動実行（Portfolio Appの場合のみ）
python3 ~/Desktop/git-worktree-agent/_workflow/src/simplified_github_publisher.py .

# 結果:
# https://github.com/{username}/ai-agent-portfolio/tree/main/{app-name}/
```

---

## 📊 まとめ

### 実行フロー全体像（v2.0）

```
Phase 0: 初期化（完了済み）
  ↓
Phase 1-A: 要件分析（2案並列 → 評価[--skip-file-check] → マージ）
  ↓
Phase 1-B: 設計・計画（選択案で継続 → 評価[--auto-merge] → 全worktree同期）
  ↓
Phase 2: 実装（3プロトタイプ並列 → UX重視評価 → マージ）
  ↓
Phase 3: テスト（100%合格まで継続 → マージ）
  ↓
Phase 4: 品質改善（2最適化案並列 → 評価 → マージ）
  ↓
Phase 5: 完成処理（documenter_agent.py 逐次実行 → マージ）
  ↓
Phase 6: GitHub公開（自動、Portfolio Appのみ）
  ↓
Phase 6.5: セキュリティ検証（自動）
```

### 並列Task実行のポイント（v2.0更新）

- **Phase 1-A**: 2つのTaskを1メッセージで（要件分析）
- **Phase 1-B**: 単一Task（設計・計画、選択された案で継続）
- **Phase 2**: 3つのTaskを1メッセージで
- **Phase 3**: 単一Task（ループ）
- **Phase 4**: 2つのTaskを1メッセージで
- **Phase 5**: 単一Task（documenter_agent.pyが内部で逐次実行）← v2.0変更

### autonomous_evaluator.py オプション一覧（v2.0）

| オプション | 説明 | 使用タイミング |
|-----------|------|---------------|
| `--auto-merge` | 評価後に自動でmainへマージ＆全worktreeへ同期 | Phase 1-B完了後、Phase 2/4完了後 |
| `--skip-file-check` | IMAGE_PROMPTS.json等の存在チェックをスキップ | Phase 1-A完了時（まだ生成されていない） |
| `--phase=<phase>` | Phase固有の必須ファイルチェックを適用 | 各Phase完了時 |

### 自律評価のタイミング

- Phase 1-A完了後（`--skip-file-check` 使用）
- Phase 1-B完了後（`--auto-merge` 使用、全worktreeに同期）
- Phase 2完了後
- Phase 4完了後

### 品質基準

- Phase 3: 作成済みテスト100%合格（必須）
- Phase 4: カバレッジ80-90%（目標）
- 全Phase: エラーフリーで動作

### Worktree-Branch マッピング

詳細は `WORKTREE_INDEX.md` の「Worktree-Branch マッピング表」を参照してください。

---

**このガイドに従って、Phase別worktree自律開発を実行してください。**
