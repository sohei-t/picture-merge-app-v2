# Phase別Worktree実行セクション（CLAUDE.md挿入用）

## 🏗️ Phase別Worktree自律開発システム

### 概要

このワークフローは**9個のPhase別worktree**を使用し、複数アプローチを並列開発して最良を自律選択します。

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

**詳細:** `PHASE_WORKTREE_AUTONOMOUS_STRATEGY.md` を参照

---

## 🚀 実行フロー

### Phase 0: 初期化（自動完了済み）

`create_new_app.command` で既に9個のworktreeが作成されています。

### Phase 1: 計画（2案並列生成 → 自律評価）

**実行方法:**
```yaml
並列Task実行（1メッセージで2つ同時）:
  Task 1: Planning A
    subagent_type: "general-purpose"
    prompt: |
      【Phase 1: 計画案A - 保守的アプローチ】
      作業ディレクトリ: ./worktrees/phase1-planning-a/

      以下を作成:
      1. REQUIREMENTS.md - 要件定義
      2. WBS.json - タスク分割（保守的・安定重視）
      3. CRITICAL_PATH.md - クリティカルパス分析

      アプローチ: 実績のある技術、堅実な設計

  Task 2: Planning B
    subagent_type: "general-purpose"
    prompt: |
      【Phase 1: 計画案B - 革新的アプローチ】
      作業ディレクトリ: ./worktrees/phase1-planning-b/

      以下を作成:
      1. REQUIREMENTS.md - 要件定義
      2. WBS.json - タスク分割（革新的・効率重視）
      3. CRITICAL_PATH.md - クリティカルパス分析

      アプローチ: 最新技術、革新的な設計
```

**評価・選択:**
```bash
# 自律評価システムで最良を選択
python3 ~/Desktop/git-worktree-agent/_workflow/src/autonomous_evaluator.py . \
  phase1-planning-a phase1-planning-b

# 結果: EVALUATION_REPORT.json に記録
# 最良の計画を main にマージ
```

**重要:**
- 2つのTaskを必ず1つのメッセージで同時実行
- 評価システムが自動的に最良を選択
- 選択されなかった案も保持（後で参照可能）

---

### Phase 2: 実装（3アーキテクチャ並列開発 → UX重視評価）

**🎯 アーキテクチャ差別化戦略:**
シンプル版に偏らないよう、異なるアーキテクチャで並列開発し、UXを最優先基準に評価します。

**実行方法:**
```yaml
並列Task実行（1メッセージで3つ同時）:
  Task 1: Prototype A - マイクロサービス実装
    subagent_type: "general-purpose"
    prompt: |
      【Phase 2: プロトタイプA - マイクロサービスアーキテクチャ】
      作業ディレクトリ: ./worktrees/phase2-impl-prototype-a/

      Phase 1の計画を基に実装:
      - サービス分割型アーキテクチャ
      - 各機能を独立したサービスとして実装
      - API Gateway + 複数マイクロサービス
      - 疎結合・高スケーラビリティ

      UX重視ポイント:
      - レスポンス速度の最適化（並列処理活用）
      - 段階的ローディング（Progressive Loading）
      - エラーハンドリングの明確化

  Task 2: Prototype B - モノリシック実装
    subagent_type: "general-purpose"
    prompt: |
      【Phase 2: プロトタイプB - モノリシックアーキテクチャ】
      作業ディレクトリ: ./worktrees/phase2-impl-prototype-b/

      Phase 1の計画を基に実装:
      - 単一アプリケーション型アーキテクチャ
      - レイヤー分離（UI/Business/Data）
      - 統合された一体型システム
      - シンプル・保守性重視

      UX重視ポイント:
      - 高速な初期表示（Single Bundle最適化）
      - 一貫したユーザー体験
      - オフライン対応・PWA化

  Task 3: Prototype C - サーバーレス実装
    subagent_type: "general-purpose"
    prompt: |
      【Phase 2: プロトタイプC - サーバーレスアーキテクチャ】
      作業ディレクトリ: ./worktrees/phase2-impl-prototype-c/

      Phase 1の計画を基に実装:
      - イベント駆動型アーキテクチャ
      - 関数ベースの実装（FaaS）
      - スケーラブル・コスト最適化
      - インフラレス管理

      UX重視ポイント:
      - 高速なコールドスタート対策
      - リアルタイム性の確保
      - レスポンシブデザイン（Core Web Vitals最適化）
```

**評価・選択（UX最優先）:**
```bash
# 3つのプロトタイプをUX重視で自律評価
python3 ~/Desktop/git-worktree-agent/_workflow/src/autonomous_evaluator_ux.py . \
  phase2-impl-prototype-a phase2-impl-prototype-b phase2-impl-prototype-c

# 評価軸（UX最優先）:
# - ユーザー体験 (35%) ← 最優先！
#   * パフォーマンスUX (LCP, FID, CLS)
#   * ユーザビリティ（使いやすさ、直感性）
#   * アクセシビリティ（WCAG準拠）
#   * レスポンシブデザイン（モバイル対応）
# - 機能完成度 (20%)
# - パフォーマンス (15%)
# - テスト品質 (15%)
# - セキュリティ (10%)
# - 保守性 (5%)

# 最良のプロトタイプを main にマージ
```

**重要:**
- アーキテクチャが異なるため、シンプル版に偏らない
- UXを35%の重みで評価（最優先基準）
- Core Web Vitals（LCP/FID/CLS）で性能測定
- アクセシビリティ・レスポンシブも評価対象

---

### Phase 3: テスト（選択されたプロトタイプをテスト）

**実行方法:**
```yaml
単一Task実行:
  Task: Testing
    subagent_type: "general-purpose"
    prompt: |
      【Phase 3: テスト】
      作業ディレクトリ: ./worktrees/phase3-testing/

      mainブランチの最新コードをテスト:
      1. 全テスト実行
      2. 失敗があれば修正（100%合格まで継続）
      3. カバレッジ確認（70%以上目標）

      完了条件:
      - 作成済みテスト: 100%合格（必須）
      - 実カバレッジ: 70%以上
      - クリティカルパス: 100%カバー
```

**ループ実行:**
- テストが100%合格するまで修正を繰り返す
- 合格後、phase3-testing を main にマージ

---

### Phase 4: 品質改善（2最適化案 → 自律評価）

**実行方法:**
```yaml
並列Task実行（1メッセージで2つ同時）:
  Task 1: Quality Optimization A - カバレッジ重視
    subagent_type: "general-purpose"
    prompt: |
      【Phase 4: 品質改善A - カバレッジ重視】
      作業ディレクトリ: ./worktrees/phase4-quality-opt-a/

      改善目標:
      - カバレッジ80-90%達成
      - テスト追加
      - エッジケース対応

  Task 2: Quality Optimization B - パフォーマンス重視
    subagent_type: "general-purpose"
    prompt: |
      【Phase 4: 品質改善B - パフォーマンス重視】
      作業ディレクトリ: ./worktrees/phase4-quality-opt-b/

      改善目標:
      - パフォーマンス最適化
      - ボトルネック解消
      - リソース使用量削減
```

**評価・選択:**
```bash
# 2つの最適化案を評価
python3 ~/Desktop/git-worktree-agent/_workflow/src/autonomous_evaluator.py . \
  phase4-quality-opt-a phase4-quality-opt-b

# 最良の最適化を main にマージ
```

---

### Phase 5: 完成処理（ドキュメント生成）

**実行方法:**
```yaml
単一Task実行:
  Task: Completion
    subagent_type: "general-purpose"
    prompt: |
      【Phase 5: 完成処理】
      作業ディレクトリ: ./worktrees/phase5-delivery/

      必須タスク（3つを1メッセージで並列実行）:

      Task 1: Documenter
      - python3 ~/Desktop/git-worktree-agent/_workflow/src/documenter_agent.py
      - README.md生成
      - about.html生成（frontend-design skill使用）
      - audio_script.txt生成

      Task 2: Launcher Creator
      - launch_app.command生成
      - 実行権限付与

      Task 3: Audio Generator（オプション）
      - explanation.mp3生成（GCP認証がある場合のみ）

      検証:
      - 公開用ファイルリスト明示
      - index.html/about.htmlのレスポンシブ確認
```

**完了後:**
```bash
# phase5-delivery を main にマージ
git merge phase/delivery
```

---

### Phase 5.5: DELIVERY生成（自動実行）

```bash
# Phase 5完了直後に自動実行
python3 ~/Desktop/git-worktree-agent/_workflow/src/delivery_organizer.py

# 確認:
# - DELIVERY/<app-name>/ が標準構造で生成
# - index.html, about.html, assets/, explanation.mp3, README.md
```

---

### Phase 6: GitHub公開（Portfolio Appのみ、自動実行）

```bash
# Phase 5.5完了直後に自動実行（Portfolio Appの場合のみ）
python3 ~/Desktop/git-worktree-agent/_workflow/src/simplified_github_publisher.py .

# 結果:
# - ai-agent-portfolio/<app-name>/ に公開
# - GitHub Pages URL表示
```

---

## 🤖 サブエージェントプロンプトの標準形式

**Phase別worktree対応の標準プロンプト:**

```
あなたは{エージェント名}です。

【作業環境】
- 作業ディレクトリ: ./worktrees/{phase-worktree-name}/
- このディレクトリ内でのみファイル操作を行う

【Phase情報】
- 現在のPhase: {phase-number}
- このworktreeの目的: {purpose}
- 並列開発中の他のworktree: {other-worktrees}

【品質基準】
- 作成済みテスト: 100%合格必須
- 実カバレッジ目標: 80-90%
- クリティカルパス: 100%必須
- エラーフリーで動作すること

【タスク】
{具体的なタスク内容}

【完了条件】
- テスト合格
- 動作確認済み
- コミット完了（メッセージ: "feat({phase}): {機能名} implemented"）

【評価への意識】
このworktreeは他の{n-1}個のworktreeと並列開発されています。
自律評価システムが以下の観点で評価します（UX最優先）:
- ユーザー体験 (35%) ← 最重要！
  * パフォーマンスUX (LCP < 2.5s, FID < 100ms, CLS < 0.1)
  * ユーザビリティ（直感的な操作性、明確なフィードバック）
  * アクセシビリティ（WCAG 2.1 AA準拠）
  * レスポンシブデザイン（モバイル/デスクトップ対応）
- 機能完成度 (20%)
- パフォーマンス (15%)
- テスト品質 (15%)
- セキュリティ (10%)
- 保守性 (5%)

**UXで勝つ実装を目指してください。**
```

---

## 📊 自律評価システムの活用

### autonomous_evaluator.py の使用方法

```bash
# 基本的な使用方法
python3 ~/Desktop/git-worktree-agent/_workflow/src/autonomous_evaluator.py <project-path> <worktree1> <worktree2> ...

# 例: Phase 1の2案を評価
python3 ~/Desktop/git-worktree-agent/_workflow/src/autonomous_evaluator.py . \
  phase1-planning-a phase1-planning-b

# 例: Phase 2の3プロトタイプを評価
python3 ~/Desktop/git-worktree-agent/_workflow/src/autonomous_evaluator.py . \
  phase2-impl-prototype-a phase2-impl-prototype-b phase2-impl-prototype-c
```

### 評価結果の確認

```bash
# 評価レポートを確認
cat EVALUATION_REPORT.json

# 出力例:
{
  "selected": "phase2-impl-prototype-b",
  "results": {
    "phase2-impl-prototype-a": {
      "total_score": 75.3,
      "details": {...}
    },
    "phase2-impl-prototype-b": {
      "total_score": 89.7,
      "details": {...}
    },
    "phase2-impl-prototype-c": {
      "total_score": 82.1,
      "details": {...}
    }
  }
}
```

---

## ⚠️ 重要な注意事項

### 1. 並列Task実行の徹底

**必ず1つのメッセージで複数Taskを同時実行:**
```yaml
正しい:
  - Phase 1: 2つのTask を1メッセージで実行
  - Phase 2: 3つのTask を1メッセージで実行
  - Phase 4: 2つのTask を1メッセージで実行

間違い:
  - Task 1を実行 → 完了を待つ → Task 2を実行（逐次実行）
```

### 2. worktreeの保持

**Phase別worktreeは削除しない:**
- 評価後も全てのworktreeを保持
- 後で参照・比較可能
- 問題があれば別のworktreeを選択可能

### 3. mainブランチの管理

**mainは常に最良の選択結果を統合:**
```bash
# Phase 1完了後
git merge phase/planning-a  # または planning-b

# Phase 2完了後
git merge phase/impl-prototype-b  # 最高スコア

# Phase 3完了後
git merge phase/testing

# Phase 4完了後
git merge phase/quality-opt-a  # または opt-b

# Phase 5完了後
git merge phase/delivery
```

---

## 🎯 成功の鍵

1. **並列実行の活用**: 複数Taskを同時に実行
2. **自律評価の信頼**: 評価システムの判断を尊重
3. **worktreeの保持**: 全ての成果物を保持
4. **反復改善**: Phase 3は100%合格まで継続
5. **品質基準の遵守**: 妥協しない品質管理
