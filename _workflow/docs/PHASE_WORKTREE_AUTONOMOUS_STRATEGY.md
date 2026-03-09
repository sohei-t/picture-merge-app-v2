# Phase別Worktree自律戦略 v1.0

## 🎯 設計目標

**3つの柱:**
1. **精度の高い生成** - 複数プロトタイプを自動評価して最良を選択
2. **効率的な生成** - 並列実行とクリティカルパス最適化
3. **自律的な判断** - AIが自動的にベストプラクティスを選択

---

## 🏗️ アーキテクチャ

### 基本構造

```yaml
~/Desktop/AI-Apps/{app-name}-agent/
├── main ブランチ（常に最良の選択結果を統合）
└── worktrees/
    ├── phase1-planning-a/           # 計画案A
    ├── phase1-planning-b/           # 計画案B（代替案）
    ├── phase2-impl-prototype-a/     # 実装プロトタイプA
    ├── phase2-impl-prototype-b/     # 実装プロトタイプB
    ├── phase2-impl-prototype-c/     # 実装プロトタイプC
    ├── phase3-testing/              # テスト環境
    ├── phase4-quality-opt-a/        # 最適化アプローチA
    ├── phase4-quality-opt-b/        # 最適化アプローチB
    └── phase5-delivery/             # 最終成果物
```

---

## 📊 Phase 0: 初期化（環境準備）

### 目的
- 全Phase用のworktreeを事前作成
- 並列開発の基盤を構築

### 実行内容

```bash
#!/bin/bash
# create_new_app.command に統合

APP_NAME=$1
BASE_DIR=~/Desktop/AI-Apps/${APP_NAME}-agent

cd $BASE_DIR

# Phase 1: 計画（複数案）
git worktree add worktrees/phase1-planning-a -b phase/planning-a
git worktree add worktrees/phase1-planning-b -b phase/planning-b

# Phase 2: 実装（プロトタイプ並列開発）
git worktree add worktrees/phase2-impl-prototype-a -b phase/impl-prototype-a
git worktree add worktrees/phase2-impl-prototype-b -b phase/impl-prototype-b
git worktree add worktrees/phase2-impl-prototype-c -b phase/impl-prototype-c

# Phase 3: テスト
git worktree add worktrees/phase3-testing -b phase/testing

# Phase 4: 品質改善（複数最適化案）
git worktree add worktrees/phase4-quality-opt-a -b phase/quality-opt-a
git worktree add worktrees/phase4-quality-opt-b -b phase/quality-opt-b

# Phase 5: 完成処理
git worktree add worktrees/phase5-delivery -b phase/delivery

echo "✅ All phase worktrees created successfully"
```

**所要時間:** 5-10秒

---

## 🧪 Phase 1: 計画（複数案自動生成・評価）

### 戦略

**コンセプト:** 異なるアプローチで計画を作成し、自律評価して最良を選択

### 実行フロー

```yaml
step_1_parallel_planning:
  description: "2つの計画アプローチを並列生成"

  Task 1: Planning Approach A（保守的）
    worktree: phase1-planning-a/
    prompt: |
      あなたは保守的なアーキテクトです。
      - 実績のある技術スタックを選択
      - リスクを最小化
      - 段階的な実装計画
    output: TECH_STACK_A.md, WBS_A.json, ARCHITECTURE_A.md

  Task 2: Planning Approach B（革新的）
    worktree: phase1-planning-b/
    prompt: |
      あなたは革新的なアーキテクトです。
      - 最新技術を積極採用
      - パフォーマンス最優先
      - アグレッシブな実装計画
    output: TECH_STACK_B.md, WBS_B.json, ARCHITECTURE_B.md

step_2_autonomous_evaluation:
  description: "AI自身が両案を評価"

  Task 3: Evaluator（評価専門エージェント）
    prompt: |
      あなたは技術評価の専門家です。
      以下の2つの計画案を評価してください：

      【評価基準】
      1. 技術スタックの適切性（30点）
      2. 実装可能性（25点）
      3. 保守性（20点）
      4. パフォーマンス（15点）
      5. 拡張性（10点）

      【評価対象】
      - Approach A: worktrees/phase1-planning-a/
      - Approach B: worktrees/phase1-planning-b/

      【出力形式】
      {
        "approach_a": {
          "score": 85,
          "strengths": ["実績がある", "リスク低"],
          "weaknesses": ["最新技術未使用"]
        },
        "approach_b": {
          "score": 78,
          "strengths": ["高パフォーマンス"],
          "weaknesses": ["リスク高"]
        },
        "recommendation": "approach_a",
        "reason": "安定性と実装可能性が高い"
      }

    output: EVALUATION_REPORT.json

step_3_selection_and_merge:
  description: "最良案をmainにマージ"

  action:
    - 評価スコアが高い方を選択
    - 選択されたworktreeをmainにマージ
    - 他のworktreeは保持（履歴として）

  commands: |
    # Approach A が選ばれた場合
    git checkout main
    git merge phase/planning-a -m "feat(phase1): Adopt planning approach A (score: 85)"

    # Phase 2 に成果物を引き継ぎ
    cp worktrees/phase1-planning-a/TECH_STACK_A.md TECH_STACK.md
```

**所要時間:** 15-20分
**効果:** 複数案から最良を選択 → 精度向上

---

## 🚀 Phase 2: 実装（プロトタイプ並列開発・自律選択）

### 戦略

**コンセプト:** 重要機能を3つのアプローチで実装し、自動テスト・評価で最良を選択

### 実行フロー

```yaml
step_1_prototype_parallel_development:
  description: "3つの実装プロトタイプを並列開発"

  critical_decision: "認証システムの実装方法"

  Task 1: Prototype A（JWT + LocalStorage）
    worktree: phase2-impl-prototype-a/
    prompt: |
      認証システムをJWT + LocalStorageで実装してください。
      - シンプルで高速
      - クライアントサイド完結
      - TECH_STACK.md の仕様に準拠
    features:
      - ユーザー登録/ログイン
      - JWT トークン発行
      - LocalStorage 保存

  Task 2: Prototype B（Session + Cookie）
    worktree: phase2-impl-prototype-b/
    prompt: |
      認証システムをSession + Cookieで実装してください。
      - セキュリティ重視
      - サーバーサイド管理
      - TECH_STACK.md の仕様に準拠
    features:
      - ユーザー登録/ログイン
      - セッション管理
      - HttpOnly Cookie

  Task 3: Prototype C（OAuth2 統合）
    worktree: phase2-impl-prototype-c/
    prompt: |
      認証システムをOAuth2で実装してください。
      - Google/GitHub認証
      - 実装の簡便性
      - TECH_STACK.md の仕様に準拠
    features:
      - OAuth2 フロー
      - ソーシャルログイン

step_2_automated_testing:
  description: "3つのプロトタイプを自動テスト"

  Task 4: Test Runner（並列実行）
    action: |
      各prototypeでテスト実行（並列）

      # Prototype A
      cd worktrees/phase2-impl-prototype-a/
      npm test > ../../test-results-a.json

      # Prototype B
      cd worktrees/phase2-impl-prototype-b/
      npm test > ../../test-results-b.json

      # Prototype C
      cd worktrees/phase2-impl-prototype-c/
      npm test > ../../test-results-c.json

    metrics:
      - テスト合格率
      - カバレッジ
      - 実行時間
      - パフォーマンス（API応答速度）

step_3_autonomous_evaluation:
  description: "AI自身がプロトタイプを評価"

  Task 5: Prototype Evaluator
    prompt: |
      あなたはプロトタイプ評価の専門家です。
      以下の3つの実装を評価してください：

      【評価基準】
      1. テスト合格率（30点）
      2. コード品質（25点）
      3. パフォーマンス（20点）
      4. セキュリティ（15点）
      5. 実装の簡潔さ（10点）

      【評価データ】
      - test-results-a.json
      - test-results-b.json
      - test-results-c.json
      - 各worktreeのソースコード

      【出力形式】
      {
        "prototype_a": {
          "score": 88,
          "test_pass_rate": 100,
          "performance": "excellent",
          "security": "moderate"
        },
        "prototype_b": {
          "score": 85,
          "test_pass_rate": 98,
          "performance": "good",
          "security": "excellent"
        },
        "prototype_c": {
          "score": 72,
          "test_pass_rate": 95,
          "performance": "moderate",
          "security": "excellent"
        },
        "recommendation": "prototype_a",
        "reason": "最高のテスト合格率とパフォーマンス"
      }

    output: PROTOTYPE_EVALUATION.json

step_4_selection_and_merge:
  description: "最良のプロトタイプをmainにマージ"

  action: |
    # Prototype A が選ばれた場合
    git checkout main
    git merge phase/impl-prototype-a -m "feat(phase2): Adopt prototype A - JWT authentication (score: 88)"

    # 他のprototypeは保持（参考実装として）
    echo "✅ Best prototype selected and merged"

step_5_learning_feedback:
  description: "評価結果を次の開発に活用"

  action: |
    # 評価レポートを保存
    cp PROTOTYPE_EVALUATION.json docs/phase2-prototype-evaluation.json

    # 次のPhaseへのフィードバック
    echo "Phase 3では Prototype A の優れた点を活かす" > PHASE3_STRATEGY.md
```

**所要時間:** 30-40分
**効果:**
- 3つのアプローチから最良を自動選択
- テストデータに基づく客観的評価
- 精度が劇的に向上

---

## 🧪 Phase 3: テスト（自動検証・フィードバック）

### 戦略

**コンセプト:** Phase 2の成果物を徹底テスト。失敗時は自動的にPhase 2にフィードバック

### 実行フロー

```yaml
step_1_comprehensive_testing:
  worktree: phase3-testing/

  action: |
    # Phase 2の最良プロトタイプを継承
    git merge main

    # 全テスト実行
    npm run test:all
    npm run test:integration
    npm run test:e2e

step_2_failure_detection:
  description: "テスト失敗を検出して自動対応"

  condition: "if test_pass_rate < 95%"

  automatic_action: |
    # Phase 2 worktreeに自動フィードバック
    cd worktrees/phase2-impl-prototype-a/

    # 失敗テストのレポート作成
    echo "Phase 3で以下のテストが失敗しました：" > PHASE3_FEEDBACK.md
    cat ../phase3-testing/test-failures.log >> PHASE3_FEEDBACK.md

    # 修正を実施
    # （AIが自動的に修正を試みる）

    # 再テスト
    cd ../phase3-testing/
    git merge phase/impl-prototype-a
    npm run test:all

step_3_quality_check:
  description: "品質基準を満たすまで繰り返し"

  loop_until: "test_pass_rate >= 95% AND coverage >= 80%"
  max_iterations: 3
```

**所要時間:** 10-15分
**効果:** 自動フィードバックループで品質保証

---

## ⚡ Phase 4: 品質改善（複数最適化案・ベンチマーク選択）

### 戦略

**コンセプト:** 2つの最適化アプローチを並列実装し、ベンチマークで最良を選択

### 実行フロー

```yaml
step_1_optimization_parallel_development:
  description: "2つの最適化アプローチを並列実装"

  Task 1: Optimization A（メモリ最適化）
    worktree: phase4-quality-opt-a/
    prompt: |
      メモリ使用量を最小化する最適化を実装してください。
      - メモ化の追加
      - 不要なオブジェクト削除
      - ガベージコレクション最適化

  Task 2: Optimization B（速度最適化）
    worktree: phase4-quality-opt-b/
    prompt: |
      実行速度を最大化する最適化を実装してください。
      - アルゴリズム改善
      - 非同期処理の活用
      - キャッシュ戦略

step_2_benchmark_testing:
  description: "ベンチマークテストで比較"

  action: |
    # Optimization A のベンチマーク
    cd worktrees/phase4-quality-opt-a/
    npm run benchmark > ../../benchmark-opt-a.json

    # Optimization B のベンチマーク
    cd worktrees/phase4-quality-opt-b/
    npm run benchmark > ../../benchmark-opt-b.json

step_3_performance_evaluation:
  description: "パフォーマンスデータに基づく自律選択"

  Task 3: Performance Evaluator
    prompt: |
      ベンチマーク結果を分析し、最良の最適化を選択してください。

      【評価データ】
      - benchmark-opt-a.json
      - benchmark-opt-b.json

      【評価基準】
      - API応答速度（40点）
      - メモリ使用量（30点）
      - CPU使用率（20点）
      - コード可読性（10点）

    output: OPTIMIZATION_EVALUATION.json

step_4_selection_and_merge:
  action: |
    # 最良の最適化をmainにマージ
    # （ベンチマーク結果に基づく自動選択）
```

**所要時間:** 15-20分
**効果:** データドリブンな最適化選択

---

## 📦 Phase 5: 完成処理（統合・公開）

### 実行フロー

```yaml
worktree: phase5-delivery/

action: |
  # Phase 4の最良成果物を継承
  git merge main

  # ドキュメント生成
  python3 ~/Desktop/git-worktree-agent/_workflow/src/documenter_agent.py

  # DELIVERY生成
  python3 ~/Desktop/git-worktree-agent/_workflow/src/delivery_organizer.py

  # GitHub公開
  python3 ~/Desktop/git-worktree-agent/_workflow/src/simplified_github_publisher.py .
```

---

## 🤖 自律判断アルゴリズム

### 評価関数

```python
def evaluate_worktree(worktree_path: str, criteria: dict) -> float:
    """
    worktreeを評価してスコアを返す

    Args:
        worktree_path: 評価対象のworktreeパス
        criteria: 評価基準の辞書
            {
                "test_pass_rate": 0.3,  # 重み30%
                "code_quality": 0.25,
                "performance": 0.2,
                "security": 0.15,
                "simplicity": 0.1
            }

    Returns:
        float: 総合スコア（0-100）
    """
    scores = {}

    # テスト合格率
    test_result = run_tests(worktree_path)
    scores['test_pass_rate'] = test_result['pass_rate'] * 100

    # コード品質（静的解析）
    quality_result = analyze_code_quality(worktree_path)
    scores['code_quality'] = quality_result['score']

    # パフォーマンス（ベンチマーク）
    perf_result = run_benchmark(worktree_path)
    scores['performance'] = perf_result['score']

    # セキュリティ（脆弱性スキャン）
    security_result = security_scan(worktree_path)
    scores['security'] = security_result['score']

    # シンプルさ（行数、複雑度）
    simplicity_result = measure_simplicity(worktree_path)
    scores['simplicity'] = simplicity_result['score']

    # 加重平均
    total_score = sum(
        scores[key] * criteria[key]
        for key in criteria
    )

    return total_score

def select_best_worktree(worktrees: list, criteria: dict) -> str:
    """
    複数のworktreeから最良を自動選択

    Returns:
        str: 選択されたworktreeのパス
    """
    results = {}

    for wt in worktrees:
        score = evaluate_worktree(wt, criteria)
        results[wt] = score

    # 最高スコアを選択
    best = max(results, key=results.get)

    logger.info(f"✅ Selected: {best} (score: {results[best]})")

    return best
```

---

## 📊 自律的な品質保証

### 品質ゲート

```yaml
phase_transition_gates:
  phase1_to_phase2:
    condition: "planning_score >= 80"
    action: "自動的にPhase 2開始"
    failure: "Phase 1を再実行"

  phase2_to_phase3:
    condition: "best_prototype_score >= 85 AND test_pass_rate >= 90%"
    action: "Phase 3開始"
    failure: "全プロトタイプ再実装"

  phase3_to_phase4:
    condition: "test_pass_rate >= 95% AND coverage >= 80%"
    action: "Phase 4開始"
    failure: "Phase 2にフィードバック"

  phase4_to_phase5:
    condition: "optimization_score >= 85"
    action: "Phase 5開始"
    failure: "最適化をスキップ"
```

---

## 🎯 期待される効果

### 精度向上

| 項目 | 従来 | Phase別worktree |
|------|------|----------------|
| **設計精度** | 1案のみ | 複数案から最良を選択 → +30% |
| **実装品質** | 1実装 | 3プロトタイプから選択 → +40% |
| **最適化効果** | 1アプローチ | 2アプローチ比較 → +25% |
| **総合精度** | 基準 | **+35-50%向上** |

### 効率向上

| 項目 | 従来 | Phase別worktree |
|------|------|----------------|
| **並列実行** | 部分的 | 完全並列 → 1.5-2倍速 |
| **やり直しコスト** | 高い | 低い（worktree削除・再作成） |
| **意思決定時間** | 人間判断 | AI自動評価 → 90%削減 |
| **総合効率** | 基準 | **+50-80%向上** |

---

## 🚀 実装優先順位

### Phase 1（即座に実装）
- ✅ Phase 0: worktree事前作成
- ✅ Phase 1: 複数計画案の自動評価
- ✅ Phase 2: プロトタイプ並列開発

### Phase 2（段階的実装）
- ⏳ 自律評価関数の実装
- ⏳ ベンチマークシステムの統合
- ⏳ 品質ゲートの自動化

### Phase 3（将来拡張）
- 🔮 機械学習による評価精度向上
- 🔮 過去プロジェクトからの学習
- 🔮 最適化パターンのデータベース化

---

## 📝 使用方法

### 開発者（あなた）
```bash
# 1. プロジェクト作成
./create_new_app.command

# 2. あとは全自動
# - AIが複数案を生成
# - AIが自律評価
# - AIが最良を選択
# - 完成まで自動実行
```

### AI（Claude Code）
```yaml
# CLAUDE.md に統合される指示
Phase 1開始時:
  → 2つの計画案を並列生成
  → 自律評価
  → 最良をmainにマージ

Phase 2開始時:
  → 3つのプロトタイプを並列開発
  → 自動テスト・評価
  → 最良をmainにマージ

以降自動...
```

---

**バージョン:** v1.0
**作成日:** 2025-12-17
**ステータス:** ✅ 設計完了、実装準備完了
