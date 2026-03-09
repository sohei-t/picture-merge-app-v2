# AI エージェント完全自動実行ガイドライン

## 🤖 Opus 4.6 / Agent Teams 対応（v10.0）

### Agent Teams の有効化確認
```yaml
agent_teams:
  概要: |
    Agent Teams は Claude Code の実験的機能で、複数のチームメイト（サブエージェント）が
    リアルタイムにメッセージをやり取りしながら協調作業できるシステムです。
    従来の Task ツールでは独立した並列実行のみでしたが、Agent Teams では
    チームメイト間の情報共有・調整がリアルタイムに可能です。

  有効化確認:
    環境変数: "CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1"
    設定場所: "~/.claude/settings.json の env セクション"
    確認方法: "claude 起動後に Agent Teams 関連ツールが利用可能か確認"

  利用可能なツール:
    - "TeamCreate: チームを作成（チーム名を指定）"
    - "Task（team_name + name 指定）: チームメイトを起動"
    - "SendMessage（type: 'message'）: チームメイト間のリアルタイムメッセージング"
    - "SendMessage（type: 'shutdown_request'）: チームメイト終了要求"
    - "TaskCreate / TaskUpdate / TaskList / TaskGet: 共有タスクリストで進捗管理"

  Agent_Teams_実行手順:
    1_チーム作成: "TeamCreate(team_name='phase2-impl') でチームを作成"
    2_チームメイト起動: |
      Task(subagent_type='general-purpose', team_name='phase2-impl',
           name='frontend-dev', prompt=...) でチームメイトを起動
    3_メッセージ送信: |
      SendMessage(type='message', recipient='backend-dev',
                  content='API仕様を確認しました', summary='API spec confirmed')
    4_シャットダウン: |
      SendMessage(type='shutdown_request', recipient='frontend-dev',
                  content='タスク完了。シャットダウンしてください')
```

### Agent Teams vs Task ツール 使い分けガイドライン

```yaml
tool_selection_guide:
  agent_teams_推奨:
    条件:
      - "チームメイト間でリアルタイムの情報共有が必要"
      - "API仕様、データモデル、認証フロー等の調整が必要"
      - "成果物の整合性を動的に確保したい"
    適用フェーズ:
      - "Phase 2（実装）: Frontend / Backend / DB 間の API 連携"
      - "Phase 4（品質改善）: 2つの最適化アプローチ間の発見共有"

  task_ツール_推奨:
    条件:
      - "独立した作業で相互依存が少ない"
      - "トークン消費を節約したい"
      - "Agent Teams が不安定な場合のフォールバック"
    適用フェーズ:
      - "Phase 1（計画）: 意図的に独立させた2案の並列生成"
      - "Phase 3（テスト）: 順次処理が中心"
      - "Phase 5（完成処理）: 独立タスクの並列実行"

  フェーズ別ツール対応表:
    Phase_1_計画: "Task ツール（独立した2案生成のため）"
    Phase_2_実装: "Agent Teams 推奨 / Task ツール（フォールバック）"
    Phase_3_テスト: "Task ツール（順次処理）"
    Phase_4_品質改善: "Agent Teams オプション / Task ツール"
    Phase_5_完成処理: "Task ツール（独立タスク）"
    Phase_6_公開: "Task ツール（単一処理）"

  フォールバック:
    条件: "Agent Teams が不安定、またはトークン消費を抑えたい場合"
    方法: "従来の Task ツール並列実行パターンを使用"
    参照: "TASK_PARALLEL_EXECUTION_GUIDE.md"
```

---

## 🚨 最優先実行ルール

### 0️⃣ ワークフロー遵守の絶対原則（最重要）
```yaml
workflow_enforcement:
  priority: "最優先（他のすべてのルールより優先）"

  絶対ルール:
    - CLAUDE.mdで定義された手順を変更・省略しない
    - コスト削減を理由に手順を短絡しない
    - "簡単だから" "効率的だから" で代替案を使わない
    - API管理システムを必ず使用する（画像生成・音声生成）

  例外なし:
    - ユーザーが "簡単に" と言っても正規手順を実行
    - エラーリスクがあっても正規手順を実行
    - 時間がかかっても正規手順を実行
    - コストがかかっても正規手順を実行（$0.02/画像は許容範囲）

  代替案の使用（最終手段のみ）:
    - 正規手順を試みて失敗した場合のみ使用可能
    - 失敗理由を明確に記録（README.md）
    - ユーザーに正規手順の重要性を説明

  具体例（画像生成）:
    ❌ 禁止: "SVGで簡単に作れるから" API使用をスキップ
    ✅ 正解: IMAGE_PROMPTS.json生成 → use the gcp skill → Imagen API → 失敗時のみSVG

  具体例（音声生成）:
    ❌ 禁止: "音声なしでもいいから" GCP認証をスキップ
    ✅ 正解: use the gcp skill → GCP認証 → TTS API → 失敗時のみスキップ理由記録
```

### 1️⃣ 各タスク実行前に必ずCLAUDE.mdを読み直す
```yaml
task_execution_rule:
  before_each_task:
    - "必ずCLAUDE.mdを読み直す"
    - "現在のフェーズを確認"
    - "実行すべきタスクを確認"
    - "チェックポイントを確認"
  reason: "長時間の実行でワークフローを忘れないため"
```

### 2️⃣ DEFAULT_POLICY.mdを最初に必ず読む
```yaml
initial_check:
  step_1: "_workflow/docs/DEFAULT_POLICY.mdを読む"
  step_2: "外部API要否を判定"
  step_3: "ワークフロー選択（$0優先）"
```

### 3️⃣ frontend-designスキルは必ず明示的に宣言
```yaml
ui_generation:
  必須: "use the frontend design skill"
  対象: ["about.html", "UIコンポーネント", "ランディング"]
```

### 4️⃣ 認証情報の発見ルール（階層型設定システム）
```yaml
credential_discovery:
  priority: "ローカル設定を優先、なければグローバル設定を参照"

  # 設定解決の優先順位
  resolution_order:
    1_local_env: "./ai-agents-config/local.env"        # プロジェクト固有の上書き
    2_profile_yaml: "./ai-agents-config/profile.yaml"  # 使用するプロファイル指定
    3_global_profile: "~/.config/ai-agents/profiles/{profile_name}.env"  # グローバルプロファイル
    4_default_profile: "~/.config/ai-agents/profiles/default.env"        # デフォルト

  # ローカル設定の確認手順
  check_local_config:
    - "プロジェクトルートに ./ai-agents-config/ があるか確認"
    - "profile.yaml があれば、指定されたプロファイル名を取得"
    - "local.env があれば、その値で上書き"

  # 認証ファイルのパス
  credential_files:
    gcp: "~/.config/ai-agents/credentials/gcp/default.json"
    firebase: "~/.config/ai-agents/credentials/firebase/default.json"

  # 環境変数の読み込み方法
  load_env:
    python: |
      from dotenv import load_dotenv
      import os
      # ローカル設定を優先
      local_env = "./ai-agents-config/local.env"
      global_env = os.path.expanduser("~/.config/ai-agents/profiles/default.env")
      if os.path.exists(local_env):
          load_dotenv(local_env)
      load_dotenv(global_env)  # ローカルにない値はグローバルから
    shell: |
      # ローカル設定を優先
      if [ -f "./ai-agents-config/local.env" ]; then
        source ./ai-agents-config/local.env
      fi
      source ~/.config/ai-agents/profiles/default.env

  # 認証状態の確認コマンド
  check_command: "python3 ~/.config/ai-agents/scripts/credential_manager.py check"

  # 重要ルール
  rules:
    - "認証情報が見つからない場合、ダミーデータで代用しない"
    - "API使用前に必ず認証情報の存在を確認する"
    - "新しいサービスが必要な場合、GUIで追加を依頼する"
    - "顧客向けプロジェクトはローカル設定で認証情報を上書きする"

  # GUIでの設定管理
  gui:
    launch: "streamlit run ~/.config/ai-agents/scripts/config_gui.py"
    template_launcher: "./launch_config_gui.command"
    features:
      - "プロファイル管理（顧客ごとの設定）"
      - "プロジェクトへのローカル設定作成"
      - "GCPセットアップウィザード"
      - "API有効化状態の確認"
```

### 5️⃣ GCP/API認証の確認手順
```yaml
api_auth_check:
  before_api_use:
    step_1: "認証情報の存在確認"
    step_2: "プロジェクトIDの確認"
    step_3: "APIが有効化されているか確認"

  gcp_settings:
    project_id_env: "GCP_PROJECT_ID"
    credentials_env: "GOOGLE_APPLICATION_CREDENTIALS"
    default_project: "ai-agent-workflow-2024"
    default_credentials: "~/.config/ai-agents/credentials/gcp/default.json"

  enabled_apis:
    - texttospeech.googleapis.com    # 音声生成
    - aiplatform.googleapis.com      # Vertex AI（Imagen/音楽生成）
    - run.googleapis.com             # Cloud Run（デプロイ）

  usage:
    tts: "音声生成（explanation.mp3）"
    imagen: "画像生成（IMAGE_PROMPTS.json → 画像ファイル）"
    lyria: "音楽生成（AUDIO_PROMPTS.json → BGM/効果音）"
```

## 📋 ワークフロー実行チェックリスト

### 開始前チェック
- [ ] _workflow/docs/DEFAULT_POLICY.md 確認済み
- [ ] 外部API要否を判定済み
- [ ] ワークフロー選択済み（通常/$0 or 外部API対応）
- [ ] 認証情報確認済み（`python3 ~/.config/ai-agents/scripts/credential_manager.py check`）
- [ ] ローカル設定確認（`./ai-agents-config/` があれば使用）

### Phase 0: 初期化
- [ ] Git worktree作成
- [ ] PROJECT_INFO.yaml生成
- [ ] CLAUDE.md再読み込み ← 必須

### Phase 1: 計画（拡張版 - 精度向上）
- [ ] CLAUDE.md再読み込み ← 必須
- [ ] 1-1. 並列計画生成（2案）
- [ ] 1-2. 自律評価・選択・mainへマージ
- [ ] 1-3. 仕様設計完了（SPEC.md生成）
- [ ] 1-4. WBS作成（初回）
- [ ] 1-5. テスト設計（初回）
- [ ] 1-6. 技術選定・アーキテクチャ設計完了（TECH_STACK.md, API_DESIGN.md, ARCHITECTURE.md）
- [ ] 1-7. WBS作成・クリティカルパス特定完了（最終版）
- [ ] 1-8. AIプロンプト生成完了（必要な場合のみ）
  - 画像必要な場合: IMAGE_PROMPTS.json
  - ゲームの場合: AUDIO_PROMPTS.json（BGM/効果音プロンプト）
- [ ] 1-9. テスト設計（最終版）

### Phase 2: 実装
- [ ] CLAUDE.md再読み込み ← 必須
- [ ] Frontend実装（frontend-design skill使用）
- [ ] Backend実装
- [ ] Database実装

### Phase 3: テスト合格
- [ ] CLAUDE.md再読み込み ← 必須
- [ ] 作成済みテスト100%合格
- [ ] カバレッジ70%以上
- [ ] クリティカルパス100%カバー

### Phase 4: 品質改善
- [ ] CLAUDE.md再読み込み ← 必須
- [ ] カバレッジ80-90%達成
- [ ] パフォーマンス最適化
- [ ] 改善回数3回以内

### Phase 5: 完成処理
- [ ] CLAUDE.md再読み込み ← 必須
- [ ] README.md生成
- [ ] _workflow/src/documenter_agent.py実行
- [ ] about.html生成（日英切り替え式、デフォルト: 日本語）← 重要！
- [ ] explanation.mp3生成
- [ ] launch_app.command生成
- [ ] 公開用ファイルセット（README.md/about.html/explanation.mp3）を project/public/ に配置
- [ ] スマホ縦/横でのindex.html・about.htmlレスポンシブ確認
- [ ] project/public/ の構成を検証（index.html/about.html/assets/explanation.mp3/README.md）
- [ ] 🌐 日英切り替え機能の確認（about.html）
  - 右上の言語切り替えボタン（🇯🇵 日本語 / 🇺🇸 English）が動作すること
  - デフォルト表示が日本語であること
  - LocalStorageで言語選択が保存されること
- [ ] 🔍 GitHub Pages用パス検証（自動実行 - _workflow/src/documenter_agent.py に統合）
  - 絶対パス（/で始まる）を相対パスに自動変換
  - file:// プロトコル検出
  - ../の過度な使用を警告
  - 検証結果: "✅ パス検証完了"を確認

### Phase 6: GitHubポートフォリオ公開（一気通貫・ハイブリッドセキュリティ）

**🔧 使用スクリプト:** `_workflow/src/publish_portfolio.py`

**実行コマンド:**
```bash
# 標準実行（セキュリティチェック + エージェントレビュー + 公開）
python3 _workflow/src/publish_portfolio.py /path/to/app app-name

# ドライラン（実際の公開なし）
python3 _workflow/src/publish_portfolio.py /path/to/app app-name --dry-run
```

**7段階サブフェーズ:**
- [ ] Phase 6-1: DELIVERY準備（除外パターンでフィルタリング）
- [ ] Phase 6-2: セキュリティチェック（スクリプト）
  - 63種類の除外パターン
  - 24種類のAPIキー検出パターン
  - CRITICAL検出時は自動中止
- [ ] Phase 6-3: エージェントセキュリティレビュー（ハイブリッド）
  - 公開対象ファイルをAIがレビュー
  - SAFE/UNSAFE/REVIEW_NEEDED を判定
- [ ] Phase 6-4: Git操作（コミット作成）
- [ ] Phase 6-5: GitHub公開（mainブランチにプッシュ）
- [ ] Phase 6-5.5: GitHub Actions 完了確認 + リリースタグ作成
  - deploy.yml: main push を検知して gh-pages に自動デプロイ（エージェントは確認のみ）
  - release.yml: タグ push を検知して zip を自動生成・Release ページに公開
  - `gh run list` で Actions の成功を確認
- [ ] Phase 6-6: 状態更新・レビュー待ち移行

**完了後:**
- `.workflow_state.json` に状態保存
- ステータスが `awaiting_review` に変更
- ユーザーに公開URLを通知
- Phase 7（修正ワークフロー）待機状態へ

### Phase 7: 修正ワークフロー（ユーザーフィードバック対応）

**🔧 使用スクリプト:** `_workflow/src/modification_workflow.py`

**トリガー:** ユーザーから修正依頼があった場合のみ実行

**実行コマンド:**
```bash
# 修正依頼を登録
python3 _workflow/src/modification_workflow.py --request "ボタンの色を青から緑に変更"

# 修正実行ガイダンス表示
python3 _workflow/src/modification_workflow.py --execute

# 修正後の再公開（Phase 6 再実行）
python3 _workflow/src/modification_workflow.py --republish

# ワークフロー完了
python3 _workflow/src/modification_workflow.py --complete

# 状態確認
python3 _workflow/src/modification_workflow.py --status
```

**修正タイプと再実行フェーズ:**
| タイプ | キーワード | 再実行フェーズ |
|--------|-----------|---------------|
| UI | デザイン、色、レイアウト | Phase 3 → 6 |
| ロジック | 機能、バグ、エラー | Phase 3 → 4 → 6 |
| ドキュメント | README、説明 | Phase 5 → 6 |
| セキュリティ | 認証、パスワード | Phase 3 → 4 → 6 |
| 大規模 | 全体、作り直し | Phase 3 → 4 → 5 → 6 |

**フロー:**
1. ユーザーが修正依頼 → `.workflow_state.json` に記録
2. 修正タイプを自動判定 → 必要なフェーズを特定
3. 該当フェーズを再実行
4. Phase 6を再実行して再公開
5. ユーザーレビュー待ちに戻る
6. 問題なければ `--complete` でワークフロー完了

## 🔴 記憶保持ルール

**各フェーズ開始時に必ずチェックポイントを確認して出力すること**

```
=================================
📌 チェックポイント: [フェーズ名]
=================================
実行すべきタスク:
✅ [タスク1]
✅ [タスク2]
✅ [タスク3]
=================================
```

## 🎯 並列開発の評価基準（UX最優先）

### Phase別worktree並列開発における評価軸

Phase 2（実装）とPhase 4（品質改善）では、複数のアプローチを並列開発し、**UX（ユーザー体験）を最優先基準**に自律評価します。

```yaml
evaluation_criteria:
  user_experience: 35%  # 最優先！
    - performance_ux: "Core Web Vitals準拠（LCP < 2.5s, FID < 100ms, CLS < 0.1）"
    - usability: "直感的な操作性、明確なフィードバック"
    - accessibility: "WCAG 2.1 AA準拠（色コントラスト、キーボード操作、スクリーンリーダー対応）"
    - responsive_design: "モバイル/デスクトップ両対応、タッチフレンドリー"

  feature_completeness: 20%
    - requirement_coverage: "全要件の実装完了度"
    - api_completeness: "APIエンドポイントの完全性"
    - error_handling: "適切なエラーハンドリング"

  performance: 15%
    - response_time: "API応答時間 < 200ms"
    - bundle_size: "JavaScriptバンドルサイズ最適化"
    - database_efficiency: "クエリ最適化、インデックス適用"

  test_quality: 15%
    - coverage: "カバレッジ70-90%"
    - critical_path: "クリティカルパス100%カバー"
    - test_reliability: "テストの安定性"

  security: 10%
    - authentication: "認証・認可の実装"
    - input_validation: "入力バリデーション"
    - owasp_compliance: "OWASP Top 10対策"

  maintainability: 5%
    - code_readability: "コードの可読性"
    - documentation: "コメント・ドキュメント"
    - consistency: "コーディング規約の一貫性"
```

### Phase 2: アーキテクチャ差別化戦略

シンプル版に偏らないよう、以下の3つの異なるアーキテクチャで並列開発します：

1. **Prototype A - マイクロサービスアーキテクチャ**
   - サービス分割型、疎結合
   - UX重視: レスポンス速度最適化（並列処理活用）、段階的ローディング

2. **Prototype B - モノリシックアーキテクチャ**
   - 単一アプリケーション型、シンプル・保守性重視
   - UX重視: 高速な初期表示（Single Bundle最適化）、PWA化

3. **Prototype C - サーバーレスアーキテクチャ**
   - イベント駆動型、スケーラブル
   - UX重視: コールドスタート対策、Core Web Vitals最適化

**評価実行:**
```bash
python3 ./_workflow/src/autonomous_evaluator_ux.py . \
  phase2-impl-prototype-a phase2-impl-prototype-b phase2-impl-prototype-c
```

### UXで勝つための実装ポイント

1. **パフォーマンスUX（Core Web Vitals）**
   - LCP < 2.5s: 重要コンテンツの優先ロード、フォントpreload
   - FID < 100ms: JavaScript最適化、code splitting
   - CLS < 0.1: 画像width/height指定、CSSアニメーション最適化

2. **ユーザビリティ**
   - 即座のフィードバック（ボタン、フォーム）
   - 親切なエラーメッセージ
   - マイクロインタラクション（ホバー、トランジション）

3. **アクセシビリティ（WCAG 2.1 AA）**
   - セマンティックHTML、ARIA属性
   - キーボードナビゲーション完全対応
   - 色のコントラスト比4.5:1以上

4. **レスポンシブデザイン**
   - モバイルファースト設計
   - タッチフレンドリー（最低44x44px）
   - 横向き・縦向き両対応

token_optimization:
  CLAUDE_md_reread:
    理想: "毎回全文読み直し"
    現実的: "各フェーズの該当セクションのみ読む"
  checkpoint_output:
    フォーマット: "phase: 2, tasks: [task1, task2], status: in_progress"（簡潔なYAMLでOK）

## 🚨 初期設定（必ず実行前に確認）

**重要: 実行環境を確認**
- テンプレート環境（この専用環境）: 保護対象、直接開発禁止
- 専用環境（AI-Apps/*-agent）: ここで開発を実行

### 必須確認ファイル（ワークフロー実行前に必ず Read ツールで確認）
1. `WORKFLOW_EXECUTION_GUIDE.md` - 実行ガイド（最初に読む）
2. `_workflow/docs/DEFAULT_POLICY.md` - デフォルトポリシー（最優先で確認）
3. **`PHASE_WORKTREE_EXECUTION_GUIDE.md`** - **Phase別worktree実行ガイド（最重要！）** ← NEW!
4. `PHASE_WORKTREE_AUTONOMOUS_STRATEGY.md` - Phase別worktree設計戦略
5. `TASK_PARALLEL_EXECUTION_GUIDE.md` - Taskツール並列実行ガイド（最重要！）
6. `WORKFLOW_CHECKPOINT_SYSTEM.md` - チェックポイントシステム（タスク忘れ防止）
7. `FRONTEND_DESIGN_SKILL_GUIDE.md` - frontend-designスキル使用ガイド（重要）
8. `PHASE_6_PUBLISHING_FLOW.md` - GitHub公開フロー（Phase 6用）
9. `_workflow/config/agent_config.yaml` - エージェント設定
10. `_workflow/config/WBS_TEMPLATE.json` - タスク分割テンプレート
11. `_workflow/config/SUBAGENT_PROMPT_TEMPLATE.md` - サブエージェント用プロンプト
12. `API_CREDENTIALS_SETUP.md` - API認証セットアップガイド ← NEW!

## 📋 実行開始手順

### STEP -2: API認証チェック（推奨）
```bash
# 認証状態を確認
python3 ~/.config/ai-agents/scripts/credential_manager.py check

# 出力例:
# ✅ GCP (Text-to-Speech & Imagen): OK
# ✅ GitHub: OK
# 🚀 ワークフローを実行できます

# ❌ 未設定の場合:
# ⚠️ GCP認証が未設定です
# 📝 セットアップガイド: API_CREDENTIALS_SETUP.md
```

**重要**: API認証を設定することで以下が完全自動化されます：
- ✅ Phase 5: `explanation.mp3` 生成（Gemini TTS 優先、GCP TTS フォールバック）
- ✅ Phase 5: ゲーム画像生成（Vertex AI Imagen）
- ✅ Phase 6: GitHub自動公開

**セットアップ手順**: `API_CREDENTIALS_SETUP.md` を参照

### STEP -1: ポリシー判定（最重要）
```yaml
policy_decision:
  最優先: "デフォルトポリシー（$0、全自動）"

  判定基準:
    - 外部API要求なし → 通常ワークフロー（全自動）
    - 明示的な外部API要求 → 承認フロー後に外部API対応
    - 曖昧な場合 → デフォルトポリシー適用

  examples:
    "Todoアプリ作って": → SQLite、ローカル実行（$0）
    "Cloud SQL使ったTodoアプリ": → 承認確認後、Cloud SQL対応
    "データベースアプリ": → SQLite（デフォルト）

詳細: _workflow/docs/DEFAULT_POLICY.md を参照
```

### STEP 0: プロジェクト初期化

**このステップは `create_new_app.command` で既に完了しています**

```bash
# 完了済みの内容:
1. 環境チェック ✅
   - Git状態確認
   - 依存関係確認
   - 権限確認

2. プロジェクトセットアップ ✅
   - PROJECT_INFO.yaml 生成
   - .gitignore 作成（.env, credentials/*.json含む）
   - ディレクトリ構造作成

3. API認証セットアップ ✅
   - _workflow/.env.template コピー
   - テンプレート環境の認証ファイル検出
   - _workflow/.env 自動生成（認証パス設定済み）
   - GitHub認証自動設定

4. Phase別Worktree作成（9個）✅
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

# 確認コマンド:
ls -la worktrees/  # 9個のworktreeを確認
ls -la _workflow/.env        # 認証設定を確認
python3 ~/.config/ai-agents/scripts/credential_manager.py check  # 認証状態確認
```

**詳細:**
- Phase別worktree戦略: `PHASE_WORKTREE_AUTONOMOUS_STRATEGY.md`
- 実行ガイド: `PHASE_WORKTREE_EXECUTION_GUIDE.md`
- API認証: `API_CREDENTIALS_SETUP.md`

### STEP 1: ワークフロー開始
以下のフェーズを順番に実行する（Task ツールを使用）：

## 🚀 ワークフロー v7.0 - 一気通貫自動実行

### 📌 重要変更点
```
Portfolio Appの場合:
Phase 0 → 1 → 2 → 3 → 4 → 5 → 6 → 6.5 まで中断なく自動実行
ユーザー確認は最後のみ（セキュリティ検証完了後）

Client Appの場合:
Phase 0 → 1 → 2 → 3 → 4 → 5 で完了
```

## 🤖 Phase別Worktree自律開発システム

### 🏗️ システム概要

このワークフローは**9個のPhase別worktree**を使用し、複数アプローチを並列開発して最良を自律選択します。

```
worktrees/
├── phase1-planning-a/b          # 計画（2案）
├── phase2-impl-prototype-a/b/c  # 実装（3プロトタイプ）
├── phase3-testing               # テスト
├── phase4-quality-opt-a/b       # 品質改善（2最適化）
└── phase5-delivery              # 完成処理
```

**詳細な実行手順:** `PHASE_WORKTREE_EXECUTION_GUIDE.md` を参照

### 🚨 最重要警告：Taskツールと並列実行の徹底

**worktree・ディレクトリ指定の徹底**
- すべてのTaskプロンプトで作業ディレクトリを `./worktrees/phase{N}-{name}/` と明示
- テンプレート直下（この専用環境ルート）では絶対に作業しない
- 並列タスクを送る前に `pwd` / `ls` で phase worktree であることを確認してから委任
- Task経由で正しく実行できていれば この専用環境 本体に変更が入らない

**並列Task実行の必須パターン:**
- Phase 1: 2つのTaskを1メッセージで同時実行
- Phase 2: 3つのTaskを1メッセージで同時実行
- Phase 4: 2つのTaskを1メッセージで同時実行
- Phase 5: 3つのTaskを1メッセージで同時実行

**⛔ 絶対にやってはいけないこと:**
```yaml
wrong_approach:
  ❌ 自分で直接worktreeに移動して作業
  ❌ 自分で直接ファイルを作成・編集
  ❌ 自分で直接テストを実行
  ❌ 自分で直接コマンドを実行
```

**✅ 必ず行うべきこと:**
```yaml
correct_approach:
  ✅ 各フェーズはTaskツールでサブエージェントを起動
  ✅ 並列タスクは1つのメッセージで複数Task呼び出し
  ✅ サブエージェントに作業を委任
  ✅ 結果を待って統合
```

### 🔴 重要：Task実行前の必須ルール
```yaml
before_task_execution:
  必須手順:
    1. "CLAUDE.mdを読み直す"
    2. "現在のフェーズを確認"
    3. "Taskツールを使用しているか確認" ← 重要追加
    4. "チェックポイント出力"
  理由: "並列処理とコンテキスト分離を実現するため"
```

### 1. 要件定義・計画フェーズ（Phase別worktree並列開発）

#### 🚀 Phase 1: 複数計画案の並列生成・自律評価

**戦略:** 2つの計画アプローチを並列生成し、自律評価して最良を選択

#### 1-1. 並列計画生成
```
📌 Task実行前に必須:
1. CLAUDE.mdを読み直す
2. Phase 1のチェックリストを確認
3. PHASE_WORKTREE_AUTONOMOUS_STRATEGY.md を参照
4. ⚠️ 2つのTaskを1つのメッセージで並列実行

Task 1: Planning Approach A（保守的）
- worktree: phase1-planning-a/
- subagent_type: "general-purpose"
- prompt: |
    あなたは保守的なアーキテクトです。
    作業ディレクトリ: ./worktrees/phase1-planning-a/

    【作業内容】
    - FINDY高評価を意識した技術スタックを選択（Webアプリ: React+TypeScript標準）
    - リスクを最小化
    - 段階的な実装計画
    - _workflow/config/SUBAGENT_PROMPT_TEMPLATE.md の「1. Requirements Analyst」に準拠

Task 2: Planning Approach B（革新的）
- worktree: phase1-planning-b/
- subagent_type: "general-purpose"
- prompt: |
    あなたは革新的なアーキテクトです。
    作業ディレクトリ: ./worktrees/phase1-planning-b/

    【作業内容】
    - 最新技術を積極採用
    - パフォーマンス最優先
    - アグレッシブな実装計画
    - _workflow/config/SUBAGENT_PROMPT_TEMPLATE.md の「1. Requirements Analyst」に準拠

⚠️ 重要: 1つのメッセージで2つのTaskを同時に呼び出す
```

#### 1-2. 自律評価・選択・同期（Phase 1-A完了）

```bash
📌 2つの計画案が完成したら自動実行

# ⚠️ 重要: Phase 1-Aでは --skip-file-check を使用
# （IMAGE_PROMPTS.json, AUDIO_PROMPTS.jsonはPhase 1-8で生成されるため）
python3 ./_workflow/src/autonomous_evaluator.py . \
  phase1-planning-a phase1-planning-b \
  --auto-merge --skip-file-check

# 🔄 自動実行される処理:
# 1. 2つの計画案を評価
# 2. 最高スコアを選択
# 3. mainにマージ
# 4. ファイルチェックをスキップ（--skip-file-check）
# 5. 全worktreeに同期（phase2-*, phase3-*, phase4-*, phase5-*）

# ✅ 結果確認（Phase 1-A完了時点の必須ファイル）
ls -la REQUIREMENTS.md
# → Phase 1-Aの成果物が存在することを確認

# ℹ️ 注: SPEC.md, IMAGE_PROMPTS.json等はPhase 1-3以降で生成される
```

**🚨 重要: Phase 1の2段階構成**
```yaml
Phase 1-A（要件分析・評価・選択）:
  実行: 1-1 → 1-2
  必須成果物: REQUIREMENTS.md
  オプション: --skip-file-check（IMAGE_PROMPTS.json等は未生成のため）

Phase 1-B（設計・計画・プロンプト生成）:
  実行: 1-3 → 1-4 → 1-5 → 1-6 → 1-7 → 1-8 → 1-9
  必須成果物: SPEC.md, TECH_STACK.md, WBS.json
  オプション成果物: IMAGE_PROMPTS.json, AUDIO_PROMPTS.json（画像/音声が必要な場合）

Phase 1完了後の最終同期:
  # Phase 1-9完了後に全成果物を含めて再同期（ファイルチェック有効）
  git add -A && git commit -m "feat(phase1): complete planning phase"
  # 各worktreeへ同期
  for wt in worktrees/phase2-* worktrees/phase3-* worktrees/phase4-* worktrees/phase5-*; do
    cd "$wt" && git merge --no-edit main && cd -
  done
```

**詳細:** `PHASE_WORKTREE_EXECUTION_GUIDE.md` の Phase 1 セクション参照

#### 1-3. 仕様設計（選択された計画案を基に）
```
📌 Task実行前に必須:
1. CLAUDE.mdを読み直す
2. 要件定義の成果物（REQUIREMENTS.md）を確認
3. チェックポイント出力
4. ⚠️ Taskツール使用確認

Task実行（必ずTaskツールを使用）:
- subagent_type: "general-purpose"
- prompt: _workflow/config/SUBAGENT_PROMPT_TEMPLATE.md の「2. Specification Designer」を使用

成果物:
  - SPEC.md: 詳細仕様書
    * 機能一覧（優先度付き）
    * 画面遷移図（テキスト表現）
    * データフロー図（入出力定義）
    * 制約条件（性能、セキュリティ、UX）
  - user_stories.json: 実装可能な粒度のユーザーストーリー
  - data_models.md: 主要データ構造の定義

重要性:
  - 要件定義とWBSのギャップを埋める
  - 実装時の手戻りを防ぐ
  - テスト設計の品質向上に寄与

次フェーズへの引き継ぎ:
  - SPEC.md → WBS作成の入力
  - data_models.md → 技術選定の参考
  - user_stories.json → テスト設計の基準
```

#### 1-4. WBS作成とクリティカルパス分析（改善ループ：最大3回）
```
📌 Task実行前に必須:
1. CLAUDE.mdを読み直す
2. WBS作成の重要性を再確認
3. チェックポイント出力

Task実行:
- subagent_type: "general-purpose"
- prompt: _workflow/config/SUBAGENT_PROMPT_TEMPLATE.md の「2. Planner（WBS作成）」を使用
- 追加指示: WBS_CRITICAL_PATH_TEMPLATE.json を参照してクリティカルパスを特定
- 改善ループ: 初回実行 → タスク粒度評価 → 依存関係最適化（最大2回追加実行）

重要:
- WBSの品質が全体の成否を決定
- クリティカルパスを明確に識別
- 並列実行可能なタスクをグループ化
```

#### 1-5. テスト設計（改善ループ：最大3回）
```
📌 ワークフロー再確認を出力してから実行

Task実行:
- subagent_type: "general-purpose"
- prompt: _workflow/config/SUBAGENT_PROMPT_TEMPLATE.md の「7. Test Designer」を使用
- 改善ループ: 初回実行 → カバレッジ評価 → 追加生成（最大2回追加実行）
重要: テストの品質が実装の品質を保証
```

#### 1-6. 技術選定・アーキテクチャ設計（NEW - 拡張版）
```
📌 Task実行前に必須:
1. CLAUDE.mdを読み直す
2. SPEC.md（Phase 1-2の成果物）を確認
3. 技術選定基準を確認（_workflow/docs/DEFAULT_POLICY.md、API_USAGE_POLICY.md）

Task実行:
- subagent_type: "general-purpose"
- prompt: _workflow/config/SUBAGENT_PROMPT_TEMPLATE.md の「4. Tech Stack Selector」を使用

成果物:
  - TECH_STACK.md: 技術スタック決定書
    * フロントエンド: フレームワーク、ライブラリ、UIコンポーネント
    * バックエンド: 言語、フレームワーク、ランタイム
    * データベース: RDBMS/NoSQL選択、理由
    * 外部API: 必要なAPI、コスト試算、代替案
    * インフラ: デプロイ方式、ホスティング
  - API_DESIGN.md: API仕様
    * RESTful/GraphQL選択
    * エンドポイント一覧
    * リクエスト/レスポンス例
  - ARCHITECTURE.md: システムアーキテクチャ
    * コンポーネント図
    * データフロー
    * 依存関係

重要な判定:
  1. 外部API要否（_workflow/docs/DEFAULT_POLICY.md確認）
  2. コスト試算（API_USAGE_POLICY.md確認）
  3. $0優先、価値向上のための低コストAPIは自動承認
  4. 認証・決済など高コストAPIは明示的承認を求める

選定基準:
  - FINDY高評価（偏差値60以上）を最優先とする
  - コード品質・保守性・型安全性を重視した技術選択
  - ポートフォリオ向けは最新のモダン技術を積極採用
  - Client向けは安定性・保守性優先
  - セキュリティ・パフォーマンス考慮

フロントエンド技術スタック標準（FINDY偏差値対応）:
  デフォルト構成（Webアプリは原則この構成を採用）:
    フレームワーク: "React（関数コンポーネント + Hooks）"
    言語: "TypeScript（型定義必須）"
    スタイリング: "Tailwind CSS"
    UIライブラリ: "MUI または Lucide React（プロジェクト特性に応じて選択）"
    ビルドツール: "Vite（推奨）"

  採用理由:
    - AIがReactのベストプラクティスを最も多く学習しており、高品質コード生成に有利
    - コンポーネント単位の構造がAIへの具体的指示と相性が良い
    - TypeScriptの型定義によりバグの早期発見とコードの堅牢性が向上
    - Tailwind CSSでスタイリングの一貫性と開発速度を両立
    - UIライブラリ活用でゼロからCSS記述を回避し、プロ品質のデザインを実現
    - FINDY偏差値の評価で高スコアを獲得しやすい構成

  例外（React以外を選択するケース）:
    - ユーザーが明示的に別の技術を指定した場合
    - Canvas/WebGL ベースのゲーム（2D/3Dゲーム、物理シミュレーション等）
      → vanilla JavaScript + Canvas API / Three.js を使用
      → ただしUI/HUD部分はReactで実装することを推奨
    - 特定のフレームワーク指定がある研修コンテンツ
    - サーバーサイド専用アプリケーション（CLIツール、APIサーバー等）

  Reactプロジェクトのビルド・デプロイ手順:
    Phase 2: Vite + React + TypeScript でプロジェクト作成
    Phase 5: npm run build → dist/ の中身を project/public/ にコピー
    手順:
      1. "npm run build で dist/ を生成"
      2. "dist/ の中身（index.html, assets/ 等）を project/public/ にコピー"
      3. "about.html, README.md, explanation.mp3 を project/public/ に追加"
      4. "相対パス検証を実行（GitHub Pages対応）"
    注意: "dist/ を直接 project/public/ にせず、中身だけをコピーすること"
```

#### 1-7. WBS作成とクリティカルパス分析（改善ループ：最大3回）
```
📌 Task実行前に必須:
1. CLAUDE.mdを読み直す
2. SPEC.md、TECH_STACK.md を確認
3. WBS作成の重要性を再確認
4. チェックポイント出力

Task実行:
- subagent_type: "general-purpose"
- prompt: _workflow/config/SUBAGENT_PROMPT_TEMPLATE.md の「6. Planner（WBS作成）」を使用
- 追加指示: WBS_CRITICAL_PATH_TEMPLATE.json を参照してクリティカルパスを特定
- 改善ループ: 初回実行 → タスク粒度評価 → 依存関係最適化（最大2回追加実行）

重要:
- WBSの品質が全体の成否を決定
- クリティカルパスを明確に識別
- 並列実行可能なタスクをグループ化
- TECH_STACK.mdの技術選定を反映
```

#### 1-8. AIプロンプト生成（NEW - 画像生成が必要な場合のみ）
```
📌 実行条件:
- 画像アセットが必要なプロジェクト（ゲーム、ビジュアル重視アプリ等）
- Vertex AI Imagenを使用する場合

📌 Task実行前に必須:
1. CLAUDE.mdを読み直す
2. SPEC.md、TECH_STACK.md を確認
3. 画像アセット一覧を抽出

Task実行:
- subagent_type: "general-purpose"
- prompt: _workflow/config/SUBAGENT_PROMPT_TEMPLATE.md の「4. Prompt Engineer」を使用

成果物:
  - IMAGE_PROMPTS.json: 画像生成プロンプト集
    ```json
    {
      "assets": [
        {
          "filename": "player_ship.png",
          "prompt": "Cute pixel art spaceship flying upward, blue metallic, glowing engine, top-down view for mobile game",
          "aspect_ratio": "1:1",
          "priority": "high"
        },
        {
          "filename": "enemy_alien.png",
          "prompt": "Cute pixel art alien enemy facing downward, green skin, purple eyes, top-down view",
          "aspect_ratio": "1:1",
          "priority": "high"
        }
      ],
      "fallback_strategy": "SVG代替（カラフル幾何学図形）",
      "estimated_cost": "$0.50"
    }
    ```

重要:
  - プロンプトは英語で作成（Imagen最適化）
  - 優先度付け（クリティカルな画像から生成）
  - フォールバック戦略を明記
  - コスト試算を含める（$0.020/画像）
```

#### 1-9. テスト設計（改善ループ：最大3回）
```
📌 ワークフロー再確認を出力してから実行

Task実行:
- subagent_type: "general-purpose"
- prompt: _workflow/config/SUBAGENT_PROMPT_TEMPLATE.md の「7. Test Designer」を使用
- 改善ループ: 初回実行 → カバレッジ評価 → 追加生成（最大2回追加実行）
重要: テストの品質が実装の品質を保証
```

### 2. 実装フェーズ（クリティカルパス優先・並列実行）

#### 🆕 Agent Teams による実装（推奨）

```yaml
agent_teams_phase2:
  概要: |
    Agent Teams を使用して3名のチームメイト + リード（統合担当）で実装。
    キックオフ → スケルトン作成 → 中間レビュー → 改善提案 → 本実装の
    協調レビュー型ワークフローにより、統合時の手戻りを最小化する。
    人間チームの「朝会・レビュー・振り返り」をAI速度で実行する設計。

  チーム構成:
    lead: "統合担当（親エージェント）- 計画修正・影響分析・品質管理"
    teammates:
      - name: "Frontend Developer"
        worktree: "phase2-impl-prototype-a/"
        role: "フロントエンド実装"
      - name: "Backend Developer"
        worktree: "phase2-impl-prototype-b/"
        role: "バックエンド・API実装"
      - name: "Database/Architecture Developer"
        worktree: "phase2-impl-prototype-c/"
        role: "データベース・アーキテクチャ実装"

  協調レビュー型ワークフロー:

    phase_2a_キックオフ（認識合わせ）:
      目的: "作業開始前にチーム全員で要件・仕様の認識を合わせる"
      手順:
        1: "全チームメイトが SPEC.md, API_DESIGN.md, TECH_STACK.md, WBS.json を読む"
        2: "各自が担当領域の実装方針を SendMessage で全員に共有"
        3: "不明点・懸念事項を Lead に質問"
        4: "Lead が全員の方針を確認し、Go/修正を判断"
      例: |
        frontend-dev → broadcast:
        「SPEC.md を確認しました。認証画面は JWT + httpOnly Cookie で実装予定。
         Backend さん、/api/auth/login のレスポンスに refreshToken も含めますか？」

    phase_2b_スケルトン作成（インターフェース先行定義）:
      目的: "本実装前にAPI契約・型定義・コンポーネント構造を先に定義"
      手順:
        1: "Frontend: コンポーネント構成 + API呼び出しインターフェース定義"
        2: "Backend: APIエンドポイント定義 + リクエスト/レスポンス型"
        3: "DB Dev: テーブルスキーマ + 型定義（TypeScript types / Python models）"
        4: "各自のスケルトンを SendMessage で全員に共有"
      成果物: "実装の骨格（動作はしないが、インターフェースが定義された状態）"

    phase_2c_中間レビュー（相互レビュー + 改善議論）:
      目的: "スケルトンを相互レビューし、不整合・改善点を洗い出す"
      観点:
        - "API契約の整合性（Frontend の期待 vs Backend の提供）"
        - "データモデルの一貫性（DB スキーマ vs Backend の型定義）"
        - "認証フローの統一性（トークン管理、セッション管理）"
        - "エラーハンドリングの方針統一"
        - "UX向上のための追加機能・改善案"
      手順:
        1: "各チームメイトが他2名のスケルトンをレビュー"
        2: "不整合・改善点を SendMessage で共有"
        3: "チーム内で議論し、合意を形成"
      例: |
        db-dev → backend-dev:
        「users テーブルに role カラム（VARCHAR(20)）を追加しました。
         API側で role の読み書き対応が必要です。
         また、将来の拡張を考えて roles テーブルに分離した方がいいかも？」
        backend-dev → db-dev:
        「当面は VARCHAR で十分です。ただし ENUM 制約は入れましょう。
         role の取りうる値は 'admin', 'user', 'viewer' の3つで合意しませんか？」

    phase_2d_改善提案（チームメイト → Lead）:
      目的: "中間レビューの気づきを構造化し、Lead に提案"
      提案フォーマット: |
        SendMessage(type="message", recipient="lead（親エージェント）",
          content="【改善提案】
            提案内容: {具体的な変更案}
            理由: {なぜ必要か}
            影響範囲: {WBS上のどのタスクに影響するか}
            優先度: Critical / High / Medium / Low",
          summary="Improvement proposal: {概要}")
      Leadの対応:
        - "WBS.json の依存関係グラフで影響範囲を分析"
        - "Critical/High は即座に計画修正、SPEC.md / API_DESIGN.md を更新"
        - "Medium/Low は記録して Phase 4 で対応"
        - "修正内容を SendMessage(type='broadcast') で全チームメイトに通知"

    phase_2e_本実装（合意されたインターフェースに基づく）:
      目的: "合意されたインターフェースと修正計画に基づいて完全な実装を行う"
      手順:
        1: "各チームメイトがスケルトンを完全な実装に拡充"
        2: "実装中も仕様変更があれば即座に SendMessage で共有"
        3: "単体テストを含めて実装"

    phase_2f_最終統合レビュー:
      目的: "統合前に全コンポーネントの結線を確認"
      手順:
        1: "リードが統合テストを実行"
        2: "Frontend→Backend API呼び出し動作確認"
        3: "Backend→Database CRUD操作確認"
        4: "認証フローのエンドツーエンド確認"
        5: "問題があれば該当チームメイトに修正依頼"

  このワークフローの価値:
    ウォーターフォール的要素: "Phase 1 の設計を基盤とした構造的な品質保証"
    アジャイル的要素: "中間レビューで実装者視点の気づきを計画にフィードバック"
    AI固有の強み: "キックオフ〜レビュー〜合意形成が数十秒で完了（人間なら数時間）"

  実行手順（具体的なツール呼び出し）:
    step_1_チーム作成: |
      TeamCreate(team_name="phase2-impl")
    step_2_チームメイト起動: |
      # 3つの Task を1メッセージで同時実行
      Task(
        subagent_type="general-purpose",
        team_name="phase2-impl",
        name="frontend-dev",
        prompt="_workflow/config/SUBAGENT_PROMPT_TEMPLATE.md の Frontend Developer チームメイト版を使用"
      )
      Task(
        subagent_type="general-purpose",
        team_name="phase2-impl",
        name="backend-dev",
        prompt="_workflow/config/SUBAGENT_PROMPT_TEMPLATE.md の Backend Developer チームメイト版を使用"
      )
      Task(
        subagent_type="general-purpose",
        team_name="phase2-impl",
        name="db-dev",
        prompt="_workflow/config/SUBAGENT_PROMPT_TEMPLATE.md の DB/Architecture Developer チームメイト版を使用"
      )
    step_3_キックオフ: |
      Lead が仕様確認を指示:
      SendMessage(type="broadcast",
                  content="キックオフ: SPEC.md, API_DESIGN.md, TECH_STACK.md を読み、
                           担当領域の実装方針を共有してください。
                           不明点・懸念事項があれば質問してください。",
                  summary="Kickoff: share implementation approach")
    step_4_スケルトンレビュー指示: |
      スケルトン完成後、Lead がレビューを指示:
      SendMessage(type="broadcast",
                  content="中間レビュー: 他チームメイトのスケルトンをレビューし、
                           不整合・改善点を共有してください。
                           改善提案がある場合は Lead にも送ってください。",
                  summary="Mid-review: cross-review skeletons")
    step_5_改善提案処理: |
      提案を受けて Lead が WBS 影響分析 → 計画修正 → broadcast で通知
    step_6_本実装完了待ち: |
      各チームメイトの本実装完了を待つ
    step_7_最終統合レビュー: |
      リードが統合テストを実行し、結線確認
    step_8_シャットダウン: |
      SendMessage(type="shutdown_request", recipient="frontend-dev", ...)
      SendMessage(type="shutdown_request", recipient="backend-dev", ...)
      SendMessage(type="shutdown_request", recipient="db-dev", ...)
    step_9_評価マージ: |
      _workflow/src/autonomous_evaluator_ux.py で評価 → mainにマージ

  フォールバック: "Agent Teams が不安定な場合は従来の Task ツール並列実行を使用（下記参照）"
```

#### 🚨 並列実行の正しい実装方法（Task ツール版 - フォールバック）

**❌ 間違った実装（絶対に避ける）:**
```python
# 自分で直接実装してしまう - これは間違い！
implement_frontend()  # 順次実行
implement_backend()   # 順次実行
implement_database()  # 順次実行
```

**✅ 正しい実装（必ずこの方法を使う）:**
```python
# 1つのメッセージで3つのTaskツールを同時に呼び出す
Task(
  description="Frontend Development",
  subagent_type="general-purpose",
  prompt=FRONTEND_DEVELOPER_TEMPLATE
)
Task(
  description="Backend Development",
  subagent_type="general-purpose",
  prompt=BACKEND_DEVELOPER_TEMPLATE
)
Task(
  description="Database Implementation",
  subagent_type="general-purpose",
  prompt=DATABASE_TEMPLATE
)
# → 3つが並列実行される
```

#### 実装フェーズの実行手順
```
📌 ワークフロー再確認を出力してから実行
📌 クリティカルパスのタスクを最優先で実行
📌 Taskツールを使用しているか必ず確認

実行戦略:
1. クリティカルパスタスク（最優先）
2. クリティカルパスに依存するタスク（高優先）
3. 独立した並列可能タスク（通常優先）

sequential_critical_path:
  step_1: "API仕様定義（単独Task）"
  step_2: "データモデル定義（単独Task）"

parallel_execution (step_1, step_2 完了後):
  - Frontend（API仕様参照）
  - Backend（API仕様+データモデル参照）
  - Database（データモデル参照）

integration:
  step_3: "統合テストと結線確認（親エージェントが実行）"
  統合確認項目（親の責任）:
    - Frontend→Backend API呼び出しが動作するか
    - Backend→Database CRUD操作が正常か
    - 認証フローがエンドツーエンドで通るか
    - 環境変数の整合性（.env.exampleとコードの一致）

並列実行グループ（WBSのクリティカルパス分析に基づく）:

Group 1: クリティカルパス（最初に実行）
- API仕様定義
- 認証システム基盤
- データモデル定義

Group 2: 並列実行可能タスク（Group 1完了後 - 1メッセージで同時実行）
Task 1: Frontend
- subagent_type: "general-purpose"
- prompt: _workflow/config/SUBAGENT_PROMPT_TEMPLATE.md の「8. Frontend Developer」
- 依存: API仕様定義完了

Task 2: Backend
- subagent_type: "general-purpose"
- prompt: _workflow/config/SUBAGENT_PROMPT_TEMPLATE.md の「9. Backend Developer」
- 依存: API仕様定義、データモデル定義完了

Task 3: Database
- subagent_type: "general-purpose"
- prompt: データベース実装の標準プロンプト
- 依存: データモデル定義完了

⚠️ 重要: Group 2の3つのTaskは必ず1つのメッセージで同時に呼び出す

【NEW】モバイルゲーム判定（条件付き）:
  実装前確認:
    1. PROJECT_INFO.yaml を確認
    2. platform が "mobile" または mobile_features に "tilt_control" があるか判定
    3. YES の場合: Frontend Developer に以下を追加指示

  追加タスク（自動的にFrontend Developerに含まれる）:
    - GYRO_CONTROLS_STANDARD.md v2.0 に完全準拠した実装
    - GyroControls.js 作成（sensitivity = 3.5, v2で高感度化）
    - VirtualJoystick.js 作成（必須フォールバック）
    - InputSystem.js でジャイロ + ジョイスティック統合
    - デフォルト操作: ジョイスティック（ジャイロはオプション）
    - 操作モード切り替えUI（🎯 傾き / 🕹️ スティック）
    - iOS 18対応: clickまたはtouchendイベントで許可取得（touchstart不可）
    - 横向き/縦向き自動対応
    - テスト項目: ジャイロ許可なしでも遊べることを確認（最重要）

  重要:
    - Frontend Developerプロンプト（8番）に詳細手順が含まれている
    - 専用エージェント不要（条件分岐で対応）
    - GYRO_CONTROLS_STANDARD.md v2.0が成功事例の完全な実装を提供
    - バーチャルジョイスティックで100%プレイ可能を保証

【NEW】画像生成が必要な場合（ゲーム・ビジュアル重視アプリ）:

  🚨 ワークフロー遵守の絶対ルール（必読）:
    ❌ 禁止事項（例外なし）:
      - IMAGE_PROMPTS.json をスキップしてSVG作成
      - API認証を試さずにSVG代替
      - コスト削減を理由にAPI使用を回避
      - "SVGで十分" と判断して正規手順をスキップ
      - "エラーが出そうだから" とAPI使用を避ける

    ✅ 必須手順（この順番で実行、省略・変更禁止）:
      1. IMAGE_PROMPTS.json 確認（Phase 1-6で生成済み）
      2. use the gcp skill 宣言
      3. GCP認証セットアップ
      4. Vertex AI Imagen API 実行
      5. 失敗した場合のみSVG代替（失敗理由を記録）

    ⚠️ SVG代替の使用条件:
      - 上記1-4を実行して失敗した場合のみ
      - 失敗理由をREADME.mdに明記（例: "GCP認証エラー", "クォータ超過"）
      - 正規手順を試さずにSVGを使用することは絶対禁止

  ⚠️ 最重要: use the gcp skill を必ず明示的に宣言

  画像生成実行フロー（完全自動化、省略禁止）:

    ステップ0: 前提条件確認
      - TECH_STACK.md で画像生成が決定されていること
      - IMAGE_PROMPTS.json（Phase 1-6で生成）が存在すること
      - 存在しない場合: Phase 1に戻ってIMAGE_PROMPTS.jsonを生成

    ステップ1: GCP認証の自動セットアップ（必須）
      ⚠️ use the gcp skill を宣言してから以下を実行:

      ```bash
      # 認証ファイルパスを環境に応じて決定（階層型設定システム）
      # パターン1: ローカル設定（プロジェクト固有）
      CRED_PATH_LOCAL="./ai-agents-config/credentials/gcp.json"
      # パターン2: グローバル設定（集中管理）
      CRED_PATH_GLOBAL="$HOME/.config/ai-agents/credentials/gcp/default.json"

      # 環境検出（ローカル優先）
      if [ -f "$CRED_PATH_LOCAL" ]; then
        CRED_FILE="$CRED_PATH_LOCAL"
        echo "✅ ローカル設定の認証ファイルを検出: $CRED_FILE"
      elif [ -f "$CRED_PATH_GLOBAL" ]; then
        CRED_FILE="$CRED_PATH_GLOBAL"
        echo "✅ グローバル設定の認証ファイルを検出: $CRED_FILE"
      else
        CRED_FILE=""
      fi

      if [ -z "$CRED_FILE" ] || [ ! -f "$CRED_FILE" ]; then
        echo "⚠️ GCP認証ファイルが存在しません - 自動セットアップを開始します"

        # プロジェクトID取得
        PROJECT_ID=$(gcloud config get-value project 2>/dev/null)

        if [ -z "$PROJECT_ID" ]; then
          echo "❌ GCPプロジェクトが設定されていません"
          echo "以下のいずれかを実行してください："
          echo "  1. gcloud auth login"
          echo "  2. gcloud config set project YOUR_PROJECT_ID"
          echo ""
          echo "⚠️ GCP認証失敗のため、SVG代替を使用します"
          echo "⚠️ 失敗理由: GCPプロジェクト未設定"
          echo "⚠️ この理由をREADME.mdに記録してください"
          # SVG代替フローへ移行（正規手順失敗後のみ）
          exit 0
        fi

        # Vertex AI API有効化
        echo "🔧 Vertex AI APIを有効化しています..."
        gcloud services enable aiplatform.googleapis.com --project=$PROJECT_ID

        # サービスアカウント作成（TTS用と統合）
        SA_NAME="ai-agent"
        SA_EMAIL="$SA_NAME@$PROJECT_ID.iam.gserviceaccount.com"

        if ! gcloud iam service-accounts describe $SA_EMAIL --project=$PROJECT_ID &>/dev/null; then
          gcloud iam service-accounts create $SA_NAME \
            --display-name="AI Agent (TTS + Imagen)" \
            --project=$PROJECT_ID

          # 権限付与（TTS + Vertex AI）
          gcloud projects add-iam-policy-binding $PROJECT_ID \
            --member="serviceAccount:$SA_EMAIL" \
            --role="roles/cloudtts.admin" \
            --condition=None

          gcloud projects add-iam-policy-binding $PROJECT_ID \
            --member="serviceAccount:$SA_EMAIL" \
            --role="roles/aiplatform.user" \
            --condition=None
        else
          # 既存のサービスアカウントにVertex AI権限を追加
          gcloud projects add-iam-policy-binding $PROJECT_ID \
            --member="serviceAccount:$SA_EMAIL" \
            --role="roles/aiplatform.user" \
            --condition=None 2>/dev/null || true
        fi

        # キー生成（階層型設定システムに保存）
        # 保存先を決定（グローバル設定に統一）
        CRED_DIR="$HOME/.config/ai-agents/credentials/gcp"
        CRED_FILE="$HOME/.config/ai-agents/credentials/gcp/default.json"
        mkdir -p "$CRED_DIR"

        gcloud iam service-accounts keys create \
          "$CRED_FILE" \
          --iam-account=$SA_EMAIL \
          --project=$PROJECT_ID

        chmod 600 "$CRED_FILE"

        echo "✅ GCP認証セットアップ完了（TTS + Imagen統合）: $CRED_FILE"
      else
        echo "✅ GCP認証ファイル既存"

        # Vertex AI権限を追加（TTSのみの場合）
        SA_EMAIL=$(cat $CRED_FILE | python3 -c "import sys, json; print(json.load(sys.stdin)['client_email'])")
        PROJECT_ID=$(gcloud config get-value project 2>/dev/null)

        gcloud projects add-iam-policy-binding $PROJECT_ID \
          --member="serviceAccount:$SA_EMAIL" \
          --role="roles/aiplatform.user" \
          --condition=None 2>/dev/null || true

        echo "✅ Vertex AI権限確認完了"
      fi

      export GOOGLE_APPLICATION_CREDENTIALS="$CRED_FILE"
      ```

    ステップ2: IMAGE_PROMPTS.json を読み込み
      - Phase 1-6で生成されたプロンプトを使用
      - 優先度順（CRITICAL → HIGH → MEDIUM → LOW）で生成

    ステップ3: 画像生成実行
      - gcp-skill/IMAGEN_API.md のPython実装を使用
      - 各画像生成後、2秒待機（クォータ対策）
      - 生成成功: PNGファイル保存
      - 生成失敗: SVG代替を使用（IMAGE_PROMPTS.jsonのfallback_svg）

    ステップ4: 結果記録
      - 成功した画像数、失敗した画像数をカウント
      - コスト試算（成功数 × $0.020）
      - README.mdに記録:
        ```markdown
        ## 画像生成結果
        - Imagen生成: 25/30枚成功
        - SVG代替: 5枚
        - コスト: $0.50
        ```

  コスト管理:
    - 1画像: $0.020
    - 1ゲーム: 20-30画像 → $0.40-0.60
    - 月間予算: $25推奨
    - クォータ: 分間5-10リクエスト（2秒待機推奨）

  エラーハンドリング（正規手順を試みた後のみ）:
    - GCPプロジェクト未設定:
      1. "gcloud auth login" を試みる
      2. 失敗: 警告 → SVG代替 → 失敗理由をREADME.mdに記録
    - API未有効化: 自動有効化 → リトライ
    - 認証エラー: 自動セットアップ → リトライ
    - クォータ超過: 待機時間延長 → リトライ（最大3回） → 失敗時SVG代替
    - その他エラー: エラー内容記録 → SVG代替 → 継続

  重要な注意事項:
    ⚠️ SVG代替は「正規手順失敗後の最終手段」
    ❌ 正規手順を試さずにSVGを使用することは絶対禁止
    ✅ 画像生成失敗はプロジェクト全体の失敗ではない
    ✅ SVG代替で動作可能なゲーム/アプリを作成
    ✅ 失敗理由を明確にREADME.mdに記録（必須）
    ✅ ユーザーに手動セットアップ方法を提示
```

【NEW】音声生成が必要な場合（ゲームプロジェクト）:

  🚨 ワークフロー遵守の絶対ルール（必読）:
    ❌ 禁止事項（例外なし）:
      - AUDIO_PROMPTS.json をスキップして無音完成
      - API認証を試さずに音声なしで完成
      - コスト削減を理由にAPI使用を回避
      - "音声なしでもいい" と判断して正規手順をスキップ
      - "エラーが出そうだから" とAPI使用を避ける

    ✅ 必須手順（この順番で実行、省略・変更禁止）:
      1. AUDIO_PROMPTS.json 確認（Phase 1-6で生成済み）
      2. use the gcp skill 宣言（画像生成と同じGCP認証を使用）
      3. GCP認証セットアップ（画像生成と共通）
      4. Vertex AI Lyria API 実行（BGM/効果音生成）
      5. 失敗した場合のみ無音完成（失敗理由を記録）

    ⚠️ 音声なし完成の条件:
      - 上記1-4を実行して失敗した場合のみ
      - 失敗理由をREADME.mdに明記（例: "GCP認証エラー", "Lyria APIクォータ超過"）
      - 正規手順を試さずに音声なしで完成することは絶対禁止

  ⚠️ 最重要: use the gcp skill を必ず明示的に宣言

  音声生成実行フロー（完全自動化、省略禁止）:

    ステップ0: 前提条件確認
      - プロジェクトタイプが "game" であること（PROJECT_INFO.yaml確認）
      - AUDIO_PROMPTS.json（Phase 1-6で生成）が存在すること
      - 存在しない場合: Phase 1に戻ってAUDIO_PROMPTS.jsonを生成

    ステップ1: GCP認証の確認（画像生成と共通）
      ⚠️ use the gcp skill を宣言してから以下を実行:

      - 画像生成で既にGCP認証が完了している場合: 同じ認証を使用
      - 認証ファイル: ~/.config/ai-agents/credentials/gcp/default.json
      - 画像生成未実行の場合: 画像生成と同じ自動セットアップ手順を実行

    ステップ2: Vertex AI Lyria API で音声生成
      ```bash
      # AUDIO_PROMPTS.json から音声生成
      python3 ./_workflow/src/audio_generator_lyria.py AUDIO_PROMPTS.json

      # 生成結果確認
      if [ $? -eq 0 ]; then
        echo "✅ 音声生成成功"
        ls -lh assets/audio/
      else
        echo "❌ 音声生成失敗 - 失敗理由をREADME.mdに記録してください"
      fi
      ```

    ステップ3: HTMLに音声を自動統合
      ```javascript
      // BGM自動ロード（main_theme.wav）
      const bgm = new Audio('assets/audio/bgm_main.wav');
      bgm.loop = true;
      bgm.volume = 0.3;

      // ゲーム開始時にBGM再生
      document.getElementById('startButton').addEventListener('click', () => {
        bgm.play();
      });

      // 効果音プリロード
      const sfx = {
        action: new Audio('assets/audio/sfx_action.wav'),
        hit: new Audio('assets/audio/sfx_enemy_hit.wav'),
        item: new Audio('assets/audio/sfx_item.wav')
      };

      // 効果音再生関数
      function playSfx(name) {
        if (sfx[name]) {
          sfx[name].currentTime = 0;
          sfx[name].play();
        }
      }
      ```

    ステップ4: 成果物確認
      ```bash
      # 生成されたファイル
      assets/audio/
        ├── bgm_main.wav          (30秒、$0.06)
        ├── bgm_game_over.wav     (10秒、$0.02)
        ├── sfx_action.wav        (1秒、$0.06)
        ├── sfx_enemy_hit.wav     (1秒、$0.06)
        └── sfx_item.wav          (0.5秒、$0.06)

      # 総コスト: 約$0.30（5音声）
      ```

  コスト管理:
    - BGM（30秒）: $0.06/曲
    - 効果音（短時間）: $0.06/音（30秒分の課金だが1-2秒で使用）
    - 1ゲーム: BGM 2曲 + 効果音 3-5音 → $0.25-0.45
    - 画像生成と合計: $0.70-1.00/ゲーム
    - 月間予算: $30-50推奨（画像+音声含む）
    - クォータ: 分間5-10リクエスト（2秒待機推奨）

  Lyria API仕様:
    - モデル: lyria-002
    - 出力: WAV（48kHz）
    - 時間: 30秒固定（短い音でも30秒分課金）
    - ジャンル: 8-bit, chiptune, retro, 各種ゲーム音楽に対応
    - BPM設定: 60-200
    - ムード指定: upbeat, sad, adventurous, chill など

  エラーハンドリング（正規手順を試みた後のみ）:
    - GCPプロジェクト未設定:
      1. "gcloud auth login" を試みる
      2. 失敗: 警告 → 音声なし完成 → 失敗理由をREADME.mdに記録
    - Lyria API未有効化: 自動有効化 → リトライ
    - 認証エラー: 画像生成と同じ認証を確認 → リトライ
    - クォータ超過: 待機時間延長 → リトライ（最大3回） → 失敗時無音完成
    - その他エラー: エラー内容記録 → 音声なし完成 → 継続

  重要な注意事項:
    ⚠️ 音声なし完成は「正規手順失敗後の最終手段」
    ❌ 正規手順を試さずに音声なしで完成することは絶対禁止
    ✅ 音声生成失敗はプロジェクト全体の失敗ではない
    ✅ 音声なしでもプレイ可能なゲームを作成
    ✅ 失敗理由を明確にREADME.mdに記録（必須）
    ✅ ユーザーに手動セットアップ方法を提示
```

### 3. テスト合格フェーズ（作成済みテストは100%合格必須）

#### 3-1. ユニットテスト・統合テスト（既存）
```
📌 ワークフロー再確認を出力してから実行

テスト実行ループ（作成済みテストは100%合格まで継続）:
1. すべてのテストを実行
2. 失敗があれば修正（Fixerエージェント）
3. 再度テスト実行

【カバレッジ基準】
- 作成済みテスト: 100%合格必須（妥協なし）
- 実カバレッジ: 70%以上（最低限）
- クリティカルパス: 100%必須（認証、決済、データ検証）

※ 作成済みテストが100%合格するまで次へ進まない
```

#### 3-2. E2Eテスト（Playwright MCP）← NEW!
```
🎭 Playwright MCPを使用した実環境テスト

📌 Phase 3-1（ユニット・統合テスト）が100%合格した後に実行

手順:
1. アプリケーションサーバーを起動
   ```bash
   # ポートを確認（通常3000, 8080など）
   npm run dev &
   # または
   python3 -m http.server 8080 &
   # または
   node server.js &
   ```

2. E2Eシナリオを自動生成
   ```bash
   python3 ./_workflow/src/playwright_e2e_tester.py http://localhost:3000
   # → E2E_SCENARIOS.json が生成される
   ```

3. Playwright MCPでE2Eテストを実行
   Claude Codeに以下のように指示:

   "E2E_SCENARIOS.jsonのシナリオをPlaywright MCPで実行してください。
   全シナリオが成功するまで、問題を修正して繰り返してください。"

4. 自動実行される処理:
   - Playwright MCPがブラウザを自動操作
   - 各シナリオを順番に実行
   - スクリーンショット付きでエラーを報告
   - 失敗したシナリオを特定

5. 修正ループ（失敗がある場合）:
   - Claude CodeがPlaywright MCPのエラーを分析
   - コードを修正
   - 再度E2Eテスト実行
   - すべて成功するまで繰り返し

【E2Eテスト対象（自動生成）】
- TODOアプリ: 追加/完了/削除フロー
- ゲーム: 開始/操作/ゲームオーバー/リスタート
- チャット: メッセージ送信/受信
- 計算機: 基本演算
- 一般Webアプリ: ナビゲーション/フォーム送信

【成功基準】
✅ すべてのE2Eシナリオが成功
✅ 実際のブラウザで全機能が動作確認済み
✅ ユーザーフローに問題なし

⚠️ 重要: E2Eテストが100%成功するまで次フェーズへ進まない
```

### 4. 品質改善フェーズ（カバレッジ80-90%目標、最大3回改善）

#### 🆕 Agent Teams オプション（Phase 4）

```yaml
agent_teams_phase4:
  概要: |
    Agent Teams を使用して2つの最適化アプローチ間で発見を共有。
    協調レビュー型ワークフローで、改善の方向性を合意してから実施。

  チーム構成:
    lead: "品質管理リード（親エージェント）"
    teammates:
      - name: "Performance Optimizer"
        worktree: "phase4-quality-opt-a/"
        role: "パフォーマンス最適化（レスポンス時間、バンドルサイズ）"
      - name: "Code Quality Optimizer"
        worktree: "phase4-quality-opt-b/"
        role: "コード品質・テストカバレッジ改善"

  協調レビュー型ワークフロー:
    phase_4a_現状分析共有:
      目的: "改善開始前に現状のメトリクスと改善方針を共有"
      手順:
        1: "Performance: プロファイリング結果（ボトルネック箇所）を共有"
        2: "Quality: カバレッジ分析・コード品質レポートを共有"
        3: "両者の改善が競合しないよう方針を調整"

    phase_4b_改善実施_中間共有:
      目的: "改善中に相互影響を検出し、手戻りを防ぐ"
      手順:
        1: "各自が改善を実施"
        2: "他メンバーに影響する変更は即座に SendMessage で共有"
        3: "競合が発生した場合は Lead が調整"
      例: |
        perf-optimizer → quality-optimizer:
        「lodash を個別インポートに変更しました。リファクタリング時に
         import { debounce } from 'lodash' の形式に統一してください」

    phase_4c_改善提案:
      目的: "Phase 2 で見逃された設計上の問題を Lead にフィードバック"
      例: |
        quality-optimizer → Lead:
        「【改善提案】認証ミドルウェアの責務が大きすぎます。
         認証と認可を分離すると、テストカバレッジ向上 + パフォーマンス改善の
         両方に効果があります。WBS の Phase 4 タスクに追加を提案します。」

  実行手順:
    1_チーム作成: "TeamCreate(team_name='phase4-quality')"
    2_チームメイト起動: |
      Task(subagent_type='general-purpose', team_name='phase4-quality',
           name='perf-optimizer', prompt=...)
      Task(subagent_type='general-purpose', team_name='phase4-quality',
           name='quality-optimizer', prompt=...)
    3_キックオフ: |
      SendMessage(type='broadcast',
                  content='現状のメトリクスを分析し、改善方針を共有してください。
                           相互に影響する改善がないか確認しましょう。',
                  summary='Phase 4 kickoff: share analysis')
    4_中間共有_改善提案: |
      改善中の発見や提案を SendMessage で共有
    5_シャットダウン: |
      SendMessage(type='shutdown_request', recipient='perf-optimizer', ...)
      SendMessage(type='shutdown_request', recipient='quality-optimizer', ...)

  フォールバック: "従来の Task ツール並列実行"
```

```
📌 ワークフロー再確認を出力してから実行

改善ループ実行（最大3回）:
1. Task: Evaluator
   - prompt: _workflow/config/SUBAGENT_PROMPT_TEMPLATE.md の「10. Evaluator」
   - 品質評価（カバレッジ、パフォーマンス、可読性、セキュリティ）

2. カバレッジ改善（目標: 80-90%）
   - 現在のカバレッジを確認
   - 不足している重要なテストを追加
   - クリティカルパスは100%を目指す

3. Task: Improvement Planner（改善余地がある場合）
   - prompt: _workflow/config/SUBAGENT_PROMPT_TEMPLATE.md の「11. Improvement Planner」

4. Task: Fixer（改善実装）
   - prompt: _workflow/config/SUBAGENT_PROMPT_TEMPLATE.md の「12. Fixer」
   - 作成済みテストは100%合格を維持
   - 新規テストも追加

【目標カバレッジ】
- 全体: 80-90%
- ビジネスロジック: 90-100%
- API/統合: 80-90%
- UI/E2E: 70-80%

収束条件:
- 目標カバレッジに達したら早期終了可
- 既存テスト100%合格を維持

【FINDY偏差値60達成基準】（Reactプロジェクト必須チェック）
Phase 4では以下の4項目を必ず確認・改善すること:

1. TypeScript型定義の徹底
   - 全コンポーネントのProps型をinterfaceで定義
   - API レスポンスの型定義（any型の使用禁止）
   - ユーティリティ関数の引数・戻り値に型を付与
   - 確認: "any" や "as any" がコード内に残っていないこと

2. カスタムフックによるロジック分離
   - UIコンポーネントからビジネスロジックを use〇〇 フックに分離
   - データ取得ロジック → useXxxQuery / useXxxFetch
   - フォーム管理ロジック → useXxxForm
   - 状態管理ロジック → useXxxState
   - 確認: コンポーネント内に50行以上のロジックが残っていないこと

3. 再レンダリング最適化
   - 重い計算処理に useMemo を適用
   - 子コンポーネントに渡すコールバック関数に useCallback を適用
   - リストの子コンポーネントに React.memo を適用
   - 確認: React DevTools Profilerで不要な再レンダリングがないこと

4. エラー処理・ローディング状態の実装
   - API通信中のローディング表示（スピナー/スケルトン）
   - エラー発生時のユーザーフレンドリーなエラーメッセージ表示
   - ErrorBoundary の実装（予期しないエラーのキャッチ）
   - 確認: loading / error / success の3状態が全データ取得箇所で処理されていること

改善実行指示テンプレート:
  「このReactコンポーネントをリファクタリングしてください。
   TypeScriptで型定義を行い、複雑なロジックはカスタムフックに分離し、
   再レンダリングの最適化（useMemo/useCallback/React.memo）も考慮してください。
   エラー処理とローディング状態も追加してください。」

非Reactプロジェクト（Canvas/ゲーム等）の場合:
  上記1〜4の代わりに以下を適用:
  1. TypeScript型定義 → そのまま適用（Canvas/ゲームでもTS推奨）
  2. カスタムフック → モジュール分離（GameEngine, InputHandler, Renderer 等のクラス/関数分離）
  3. 再レンダリング最適化 → ゲームループ最適化（requestAnimationFrame、オブジェクトプール等）
  4. エラー処理 → ゲーム状態管理（loading/playing/paused/gameover の状態遷移）
```

### 5. 完成処理フェーズ（全タスク必須）
```
🚨 Phase 5 実行前の必須確認
=================================
1. CLAUDE.mdを読み直す ← 必須！
2. WORKFLOW_CHECKPOINT_SYSTEM.mdを読む
3. 以下のチェックポイントを出力
=================================

=================================
📌 チェックポイント: フェーズ5 - 完成処理
=================================
出口条件（全て必須）:
✅ Reactプロジェクト: npm run build → dist/ の中身を project/public/ にコピー済み
✅ README.md 生成（公開用の概要を含む）
✅ _workflow/src/documenter_agent.py 実行 ← 最重要！忘れやすい！
✅ about.html 生成（日英切り替え式、デフォルト: 日本語、mp3埋め込み済み）
✅ explanation.mp3 生成（存在しない場合はスキップ理由を明記）
✅ launch_app.command 生成（実行権限付与）
✅ 公開用ファイルリストを明示（README.md/about.html/explanation.mp3/launch_app.command/index.html/必要なassets）
✅ index.html / about.html のスマホ縦・横でのレスポンシブ確認（レイアウト崩れ/タップ検証）
✅ 🔍 GitHub Pages用パス検証（_workflow/src/documenter_agent.py内で自動実行）
  - 絶対パス（/で始まる）→ 相対パスに自動変換
  - file:// プロトコル検出
  - ../の過度な使用を警告
  - 検証結果を確認: "✅ パス検証完了"
Phase 5完了後の自動検証:
  bash: validate_phase5()  # project/public/ 必須ファイル確認
  pass: Phase 6へ自動進行（Portfolio Appの場合）
  fail: 不足ファイルを生成して再検証
=================================

📌 ファイル生成責任の明確化:
=================================
| ファイル | 生成元 | 生成タイミング |
|---------|--------|--------------|
| index.html | Phase 2実装（Frontend Developer） | Phase 2 |
| about.html | _workflow/src/documenter_agent.py | Phase 5 |
| README.md | Documenter Task | Phase 5 |
| explanation.mp3 | Documenter（Gemini TTS 優先、GCP TTS フォールバック） | Phase 5（オプション）|
| launch_app.command | Launcher Creator Task | Phase 5 |
| assets/ | Phase 2実装 | Phase 2 |
=================================

⚠️ Phase 5 完了後の自動処理:
→ PROJECT_INFO.yamlを確認
→ Phase 6（GitHub公開）を自動実行（Portfolio Appの場合のみ）
=================================

⚠️ 注意: _workflow/src/documenter_agent.pyを忘れると about.html が生成されません！
_workflow/src/documenter_agent.py失敗時の対応:
  retry: 最大3回自動リトライ
  fallback:
    - about.html をテンプレートから手動生成（日英切り替え式、デフォルト: 日本語）
    - audio_script.txt を手動作成
    - explanation.mp3 は後続タスクでスキップし、理由を記録

📌 Phase 5のタスク実行方式（実態に合わせた説明）:
  _workflow/src/documenter_agent.py は単一スクリプトで以下を順次実行:
    1. about.html 生成（日英切り替え式）
       - 右上に言語切り替えボタン配置（🇯🇵 日本語 / 🇺🇸 English）
       - デフォルト表示: 日本語
       - LocalStorageで言語選択を記憶
       - 全セクション（概要、機能、技術スタック、開発プロセス、メトリクス）が日英対応
    2. audio_script.txt 生成
    3. explanation.mp3 生成（Gemini TTS 優先、GCP TTS フォールバック）

  並列実行する場合:
    Task 1: Documenter（_workflow/src/documenter_agent.py実行）
    Task 2: Launcher Creator（launch_app.command生成）

  ※ Audio GeneratorはDocumenter内で統合実行される

Task 1: Documenter（最重要 - 絶対に忘れない）
- prompt: _workflow/config/SUBAGENT_PROMPT_TEMPLATE.md の「14. Documenter」
- 必須実行コマンド:
  * テンプレート環境: python3 ./_workflow/src/documenter_agent.py
  * 専用環境: python3 ../_workflow/src/documenter_agent.py (worktree内から実行)
  * または: python3 ./_workflow/src/documenter_agent.py (エージェント環境ルートから実行)
- 検証項目:
  * about.html が生成されているか（日英切り替え式、デフォルト: 日本語）
  * 言語切り替えボタン（🇯🇵/🇺🇸）が右上に表示されているか
  * デフォルト表示が日本語になっているか
  * audio_script.txt が生成されているか
  * explanation.mp3 が生成されているか（Gemini TTS優先、GCPフォールバック）
  * 音声未生成の場合は理由がREADME.mdに記録されているか

Task 2: Launcher Creator
- prompt: _workflow/config/SUBAGENT_PROMPT_TEMPLATE.md の「15. Launcher Creator」
- 生成物: launch_app.command
- 実行権限付与: chmod +x launch_app.command

Task 3: Audio Generator（Gemini TTS 優先）
- 実行: _workflow/src/documenter_agent.py が自動実行（Documenterタスクに統合）
- 音声生成の優先順位:
  1. **Gemini 2.5 Flash Preview TTS**（推奨 - APIキーのみで利用可能）
  2. Google Cloud TTS（フォールバック - サービスアカウント必要）
- 生成物: explanation.mp3
- フォールバック: 両方失敗時は音声なしで継続（理由を記録）

📌 追加検証（Phase 5 完了時に必ず実施）
- 公開用ファイルリストをREADME.mdに記載し、about.htmlからexplanation.mp3が相対パス（例: ./explanation.mp3）で再生できることを確認
- index.html/about.htmlの主要導線がスマホ縦・横どちらでもクリック/タップ可能であることを簡易確認（デバッガ不要の目視・ブラウザサイズ変更でOK）
```

### 音声生成システム（Gemini TTS 優先）

**推奨: Gemini 2.5 Flash Preview TTS**
- APIキーのみで利用可能（サービスアカウント不要）
- SSMLを使わず自然言語から高品質な音声を生成
- 日本語に対応した高品質な音声

**セットアップ手順:**
```bash
# 1. 依存関係インストール
pip install google-genai pydub

# 2. APIキー設定（いずれかの方法）
# 方法A: 環境変数
export GEMINI_API_KEY='your-api-key'

# 方法B: ~/.config/ai-agents/profiles/default.env に追加
echo "GEMINI_API_KEY=your-api-key" >> ~/.config/ai-agents/profiles/default.env

# 3. ffmpegインストール（pydubが使用）
brew install ffmpeg  # macOS
```

**利用可能な音声:**
- Kore（日本語対応、男性） - デフォルト
- Aoede, Charon, Fenrir, Puck など

**フォールバック: Google Cloud TTS**
Gemini TTS が利用できない場合、自動的に Google Cloud TTS にフォールバックします。
- サービスアカウント認証が必要
- 詳細は `API_CREDENTIALS_SETUP.md` を参照

【成果物】
- explanation.mp3（Gemini TTS または GCP TTS で生成）
- 両方失敗時: 理由をREADME.mdに記録し、音声なしで継続

【エラーハンドリング】
- GEMINI_API_KEY 未設定 → GCP TTS にフォールバック
- GCP認証も未設定 → 音声生成スキップ（理由を記録）
```

### 6. GitHubポートフォリオ公開フェーズ（Phase 5完了後、自動実行必須）
```
🚨 Portfolio Appの場合、Phase 5完了直後に自動実行 - ユーザー確認不要
=================================
📌 チェックポイント: Phase 6 - GitHub自動公開
=================================

実行前確認:
1. PROJECT_INFO.yaml の development_type を確認
2. "Portfolio App" の場合のみ実行
3. "Client App" の場合はスキップ

実行コマンド:
python3 ./_workflow/src/simplified_github_publisher.py .

🔴 定型タスク（必ず実行）:
✅ リモートリポジトリ: https://github.com/sohei-t/ai-agent-portfolio
✅ アプリ名フォルダ作成（slug方式、日付除去）
✅ 同名フォルダは中身のみ更新（フォルダ名は固定）
✅ GitHub Pages自動有効化（gh API使用）
✅ README.md冒頭に以下を自動追加:
   - 🎮 ライブデモリンク
   - 📱 About.htmlリンク
   - 🔊 音声解説リンク（該当する場合）

確認項目:
✅ ai-agent-portfolio/{app-name}/ にpush完了
✅ GitHub Pages自動有効化成功（または手動案内表示）
✅ README.mdに定型リンク追加済み
✅ 公開URLを表示（ライブデモ/About/音声）
=================================

📌 公開後の確認
=================================
✅ ライブデモURL: https://{username}.github.io/ai-agent-portfolio/{app-name}/
✅ AboutページURL: https://{username}.github.io/ai-agent-portfolio/{app-name}/about.html
✅ 音声解説URL: https://{username}.github.io/ai-agent-portfolio/{app-name}/explanation.mp3
✅ README.md冒頭に上記リンクが記載されていることを確認
=================================

⚠️ Phase 6 完了後: 自動的にPhase 6.5の検証を実行
========================================
📌 Phase 6.5は必須フェーズです。Phase 6完了後、中断せずに継続してください。
```

## 🔍 Phase 6.5: GitHub公開後セキュリティ検証

### 🚨 概要
Phase 6で公開されたGitHubリポジトリに不要なファイルが含まれていないか、別のサブエージェントが独立して検証する重要なフェーズです。

### 実行タイミング
- Phase 6完了直後に**必ず実行**
- GitHub公開が成功した場合のみ実行
- Portfolio App・Client App両方で実行

### 検証手順

#### Step 1: 公開リポジトリの独立検証（Taskツール使用）
```bash
# 別のサブエージェントによる検証
Task: GitHub Repository Security Auditor
- subagent_type: "general-purpose"
- prompt: |
    あなたはGitHubリポジトリのセキュリティ監査担当者です。

    【タスク】
    1. 公開されたリポジトリをクローンまたはWeb上で確認
       - URL: https://github.com/sohei-t/ai-agent-portfolio/tree/main/{app-name}/

    2. 以下の観点で厳密にチェック:

       【絶対に含まれてはいけないファイル】
       ❌ 認証情報:
          - credentials/, secrets/, private/
          - *.key.json, *.pem, *.cert, *.key
          - .env, .env.*, env.* （.env.exampleは除く）
          - APIキー、パスワード、トークンを含むファイル

       ❌ テストコード:
          - tests/, test/, __tests__/, spec/
          - *.test.*, *.spec.*, test_*.py
          - pytest.ini, jest.config.js

       ❌ 開発ツール:
          - *agent*.py, *_agent.py
          - generate_*.py, generate_*.js
          - documenter_agent.py

       ❌ バックアップ・一時ファイル:
          - *.backup, *.bak, *.old
          - old/, backup/, temp/, tmp/
          - *~, *.swp

       ❌ 設定・ログ:
          - .gitignore, .gitattributes
          - .DS_Store, Thumbs.db
          - .vscode/, .idea/
          - *.log, logs/

       ❌ 依存関係:
          - node_modules/, venv/, __pycache__/
          - package-lock.json, yarn.lock

       ❌ 開発ドキュメント:
          - WBS*.json, DESIGN*.md
          - PROJECT_INFO.yaml, SPEC*.md
          - 内部仕様書、設計書

    3. 発見した問題をリスト化:
       - ファイルパス
       - なぜ公開すべきでないか
       - 深刻度（Critical/High/Medium/Low）

    4. 修正の必要性を判定:
       - Critical/High: 即座に削除が必要
       - Medium: 削除を推奨
       - Low: 次回更新時に削除

    【出力形式】
    ## 🔍 GitHub公開後セキュリティ検証結果

    ### ✅ 検証済みURL
    {確認したGitHubリポジトリURL}

    ### ❌ 発見された問題（{件数}件）

    #### Critical（即座に対応必要）
    - {ファイルパス}: {理由}

    #### High（早急に対応推奨）
    - {ファイルパス}: {理由}

    #### Medium（次回更新時に対応）
    - {ファイルパス}: {理由}

    ### 📋 推奨アクション
    1. {具体的な削除手順}
    2. {今後の予防策}

    ### 🎯 判定
    - [ ] セキュリティ上安全（問題なし）
    - [ ] 軽微な問題あり（次回対応で可）
    - [ ] 重大な問題あり（即座に対応必要）
```

#### Step 2: 問題が発見された場合の対応
```bash
# Critical/Highレベルの問題が発見された場合

# 1. 緊急削除スクリプトの作成
cat > emergency_cleanup.sh << 'EOF'
#!/bin/bash
# 緊急クリーンアップスクリプト

REPO_DIR="/tmp/emergency_cleanup_$$"
REPO_URL="https://github.com/sohei-t/ai-agent-portfolio.git"
APP_NAME="{app-name}"

# リポジトリをクローン
git clone $REPO_URL $REPO_DIR
cd $REPO_DIR

# 問題のあるファイルを削除
rm -rf $APP_NAME/.gitignore
rm -rf $APP_NAME/.DS_Store
rm -rf $APP_NAME/old/
rm -rf $APP_NAME/backup/
rm -rf $APP_NAME/*.bak
rm -rf $APP_NAME/tests/
rm -rf $APP_NAME/*agent*.py

# コミット＆プッシュ
git add -A
git commit -m "🔒 Security fix: Remove unnecessary files from $APP_NAME

- Removed backup files and folders
- Removed test files
- Removed development tools
- Removed system files (.DS_Store, .gitignore)

This is an automated security cleanup."
git push

# クリーンアップ
rm -rf $REPO_DIR
EOF

chmod +x emergency_cleanup.sh
./emergency_cleanup.sh
```

#### Step 3: 予防策の実装
```python
# _workflow/src/simplified_github_publisher.py の改善提案を生成
Task: Publisher Improvement Advisor
- subagent_type: "general-purpose"
- prompt: |
    Phase 6.5の検証結果を基に、_workflow/src/simplified_github_publisher.pyの
    clean_public()メソッドを改善する提案を作成してください。

    【追加すべき除外パターン】
    {検証で発見されたパターン}

    【改善案】
    1. より厳密なファイルフィルタリング
    2. ホワイトリスト方式の検討
    3. 公開前の最終確認プロンプト
```

### 成功基準
```yaml
verification_success:
  critical_issues: 0  # Criticalレベルの問題がゼロ
  high_issues: 0      # Highレベルの問題がゼロ
  medium_issues: "3件以下"  # Mediumは許容範囲
  low_issues: "無制限"       # Lowは記録のみ

  required_files:
    - index.html
    - README.md
    - assets/（必要な静的ファイルのみ）

  optional_files:
    - about.html
    - explanation.mp3
    - package.json（dependencies情報のみ）
```

### 検証完了後のアクション
```
=================================
📌 Phase 6.5 検証完了
=================================

✅ セキュリティ検証: 完了
✅ 不要ファイル: {0件 or 削除済み}
✅ 公開URL: 安全性確認済み

次のステップ:
- 問題なし → ワークフロー完了
- 問題あり → 即座に修正 → 再検証
=================================
```

### Phase 6.5 完了後

🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉
========================================
🎊 ワークフロー完了！Phase 0-6.5 すべて終了
========================================

✅ 新規アプリ開発が完了しました
✅ GitHubに公開されました
✅ セキュリティ検証も完了しました
✅ GitHub Pagesで公開されています

📝 今後、このアプリを修正する場合:
「CLAUDE.mdのPhase 7に従って、{app-name}を修正しGitHubに再公開してください」
と指示してください。

⚠️ 重要: 修正時は必ずPhase 7の手順を使用してください
　　　　（独自の方法でGitHubにpushしないこと）

========================================
🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉
```

## 🔄 Phase 7: 既存アプリの修正・再公開（Issue/PR管理対応）

### 🚨 最重要ルール
**このPhaseは修正時のみ使用。初期開発時（新規アプリ作成）には実行しない**

### 🎯 新機能: Issue/PR自動管理

修正時に GitHub Issue/PR を自動作成し、変更履歴を追跡可能にします。

```
ユーザー: 「todo-appのボタンの色を変更して」
    ↓
エージェント自動実行:
1. Issue作成: [todo-app] ボタンの色を変更 #123
2. 修正実施
3. PR作成: fix(todo-app): ボタンの色を変更 #124 (Fixes #123)
4. マージ → Issue自動クローズ
5. GitHub Pages更新
```

**メリット:**
- ✅ Issue/PR履歴が残る（Findy偏差値向上）
- ✅ 変更理由の追跡が可能
- ✅ コードレビュー履歴の蓄積
- ✅ ユーザーの操作は変更なし

### 実行条件（以下すべてを満たす場合のみ）
- ✅ すでにGitHubに公開済みのアプリが存在する
- ✅ そのアプリに修正・改善を加える
- ✅ 修正後、GitHubに再公開する

### 初期開発時の正しいフロー
```
新規アプリ作成時: Phase 0 → 1 → 2 → 3 → 4 → 5 → 6 で完了
Phase 7 は実行しない ← 重要！
```

### いつ使うか（修正時のみ）
- 公開済みアプリにバグがある
- 機能追加・改善したい
- デザインを変更したい
- パフォーマンス改善したい

### 📊 修正タイプと自動ラベル付け

```yaml
修正タイプ（自動判定）:
  ui:
    キーワード: デザイン, 色, レイアウト, スタイル, CSS, ボタン
    ラベル: app:{app-name}, type:ui
    再実行フェーズ: [3, 6]

  logic:
    キーワード: ロジック, 機能, バグ, エラー, 修正
    ラベル: app:{app-name}, type:fix
    再実行フェーズ: [3, 4, 6]

  docs:
    キーワード: ドキュメント, README, 説明
    ラベル: app:{app-name}, type:docs
    再実行フェーズ: [5, 6]

  security:
    キーワード: セキュリティ, 認証, パスワード
    ラベル: app:{app-name}, type:security
    再実行フェーズ: [3, 4, 6]

  full:
    キーワード: 全体, 大幅, リファクタ
    ラベル: app:{app-name}, type:refactor
    再実行フェーズ: [3, 4, 5, 6]
```

### 🎯 実行手順（Issue/PR管理版）

#### Step 1: 修正依頼（Issue自動作成）

```bash
# エージェントが自動実行（ユーザーは修正内容を伝えるだけ）
cd ~/Desktop/AI-Apps/{app-name}-agent/

# modification_workflow.py が以下を自動実行:
python3 ./_workflow/src/modification_workflow.py \
  --request "ボタンの色を青から緑に変更"

# 自動実行される処理:
# 1. アプリ名を自動検出（PROJECT_INFO.yaml または フォルダ名）
# 2. GitHub Issue作成: [todo-app] ボタンの色を変更 #123
# 3. ラベル自動付与: app:todo-app, type:ui
# 4. ブランチ名生成: fix/todo-app-123-button-color
```

#### Step 2: 修正実施

```bash
# エージェントがコードを修正
# （ユーザーの指示に従って該当ファイルを編集）

# 例: ボタンの色を変更
# project/public/index.html の該当箇所を修正
```

#### Step 3: 修正完了（PR作成 → マージ → 公開）

```bash
# エージェントが自動実行
python3 ./_workflow/src/modification_workflow.py --complete-fix

# 自動実行される処理:
# 1. project/public/ の変更をコミット
# 2. GitHub公開（_workflow/src/simplified_github_publisher.py）
# 3. PR作成: fix(todo-app): ボタンの色を変更 (Fixes #123)
# 4. PRマージ → Issue #123 自動クローズ
# 5. GitHub Actions 完了確認（deploy.yml → gh-pages 自動更新）
# 6. リリースタグ作成（release.yml → zip 自動生成）
```

### 📋 コマンド一覧

```bash
# 修正依頼（Issue自動作成）
python3 _workflow/src/modification_workflow.py --request "修正内容"

# アプリ名を明示的に指定
python3 _workflow/src/modification_workflow.py --request "修正内容" --app-name todo-app

# 修正実行ガイダンス表示
python3 _workflow/src/modification_workflow.py --execute

# 修正完了（PR作成 → マージ → 公開）
python3 _workflow/src/modification_workflow.py --complete-fix

# 再公開のみ（PR作成なし）
python3 _workflow/src/modification_workflow.py --republish

# 状態確認
python3 _workflow/src/modification_workflow.py --status

# ワークフロー完了
python3 _workflow/src/modification_workflow.py --complete
```

### ⚠️ 絶対に守ること
```yaml
禁止事項:
  ❌ 新しいリポジトリを作成しない
  ❌ 独自の方法でGitにpushしない
  ❌ project/public/ を経由せずに公開しない
  ❌ modification_workflow.py を使わずに修正しない

必須事項:
  ✅ 修正依頼は --request オプションで開始（Issue自動作成）
  ✅ 修正完了は --complete-fix で終了（PR自動作成・マージ）
  ✅ 同じslugで上書き更新（新しいフォルダを作らない）
```

### 🎯 Claude Codeへの正しい指示例

**❌ 曖昧な指示（避ける）:**
```
「todo-appを修正してGitHubに再公開して」
```

**✅ 明確な指示（推奨 - ユーザーは修正内容だけ伝える）:**
```
「todo-appのボタンの色を青から緑に変更してください」
```

エージェントが自動的に：
1. Issue作成
2. 修正実施
3. PR作成・マージ
4. GitHub公開

### 📋 自動化されること

Phase 7を指定すると、Claude Codeが以下を自動実行:
```
1. ✅ アプリ名を自動検出
2. ✅ GitHub Issue作成（[app-name] タイトル）
3. ✅ ラベル自動付与（app:{app-name}, type:{type}）
4. ✅ 修正実施
5. ✅ project/public/ 更新
6. ✅ GitHub公開（_workflow/src/simplified_github_publisher.py）
7. ✅ PR作成（Fixes #{issue} でリンク）
8. ✅ PRマージ → Issue自動クローズ
9. ✅ GitHub Actions 完了確認（deploy.yml → gh-pages 自動更新）
10. ✅ リリースタグ作成（release.yml → zip 自動生成）
11. ✅ 完了報告（Issue/PR/Releases URLを表示）
```

### 🎯 結果

**修正前:**
```
https://github.com/sohei-t/ai-agent-portfolio/tree/main/todo-app/
（バグあり）
```

**修正後:**
```
https://github.com/sohei-t/ai-agent-portfolio/tree/main/todo-app/
（バグ修正済み、同じURL）

GitHub履歴:
- Issue #123: [todo-app] ボタンの色を変更 (Closed)
- PR #124: fix(todo-app): ボタンの色を変更 (Merged)

GitHub Actions:
- deploy.yml: gh-pages 自動更新 → GitHub Pages 反映
- release.yml: todo-app-v1.0.1 → zip 自動生成
- Releases: https://github.com/sohei-t/ai-agent-portfolio/releases
```

### 📊 GitHub履歴の例

**Issue一覧（アプリ別フィルタ可能）:**
```
#125 [calculator] 計算結果の表示バグ修正    app:calculator type:fix
#123 [todo-app] ボタンの色を変更            app:todo-app type:ui
#121 [weather-app] API接続エラー修正        app:weather-app type:fix
```

**PR一覧:**
```
#126 fix(calculator): 計算結果の表示バグ修正 (Fixes #125)
#124 fix(todo-app): ボタンの色を変更 (Fixes #123)
#122 fix(weather-app): API接続エラー修正 (Fixes #121)
```

## 📝 サブエージェントへの標準プロンプト

Taskツール実行時、必ず以下の内容を含める：

```
あなたは{エージェント名}です。

【作業環境】
- 作業ディレクトリ: 各フェーズに応じたworktree（phase1-*, phase2-*等）
- このディレクトリ内でのみファイル操作を行う

【品質基準】
- 作成済みテスト: 100%合格必須
- 実カバレッジ目標: 80-90%
- クリティカルパス: 100%必須
- エラーフリーで動作すること

【改善ループ】
- フェーズ3: 作成済みテストは100%合格まで修正（回数制限なし）
- フェーズ4: カバレッジ80-90%を目指して最大3回改善

【NEW】API利用判定（API_USAGE_POLICY.md参照）:
  画像生成が必要な場合:
    ⚠️ use the gcp skill を明示的に宣言
    1. gcp-skill/IMAGEN_API.md を参照
    2. Vertex AI Imagen セットアップ実行
    3. 画像生成（英語プロンプト）
    4. 失敗時: SVG/Canvas代替を自動実装
    5. コスト・結果をREADME.mdに記録

  音声生成が必要な場合（Phase 5のみ）:
    _workflow/src/documenter_agent.py が自動実行（以下の優先順位）:
    1. Gemini TTS（GEMINI_API_KEY設定時）← 推奨
    2. GCP TTS（フォールバック）
    3. 両方失敗時: 音声なしで継続（理由を記録）

【タスク】
{具体的なタスク内容}

【完了条件】
- テスト合格

【コンテキスト継承（必須で明記）】
- 参照ファイル: {依存する成果物のパス}
- 前フェーズの成果: {具体的な内容}

【完了報告フォーマット（必須）】
✅ 生成ファイル: {パスのリスト}
✅ テスト結果: {合格率 or 実行有無}
✅ 次フェーズへの引き継ぎ事項: {具体的内容}

【エラー時の対応】
- 自動リトライ: 3回まで（軽微なエラー）
- リトライ失敗時: 簡易版/代替案で実装し、理由を報告
```

## 📦 Phase 5.5: DELIVERY整理（自動実行）

### 概要
Phase 5完了後、`project/public/` の内容を整理し、GitHub公開に備える。

### 実行タイミング
- Phase 5（完成処理）完了直後に自動実行
- 手動実行は不要（_workflow/src/documenter_agent.py内で統合済み）

### 実行内容
```bash
# Phase 5完了後、以下が自動実行される:

# 0. Reactプロジェクトの場合: ビルド → project/public/ への配置
#    npm run build
#    cp -r dist/* project/public/
#    ※ dist/ を直接 project/public/ にせず、中身だけをコピー

# 1. project/public/ 構成確認
ls -la project/public/
# 必須: index.html, about.html, README.md, assets/
# オプション: explanation.mp3

# 2. 不要ファイルの除去（clean_public()相当）
# - tests/, __tests__/ などテスト関連
# - *agent*.py などの開発ツール
# - .env, credentials/ などの機密情報

# 3. パス検証（path_validator.py）
# - 絶対パス → 相対パスに変換
# - file:// プロトコル検出
# - ../の過度な使用を警告
# - Reactビルド出力の base path が "./" であることを確認
```

### 検証項目
```yaml
validation_checklist:
  必須ファイル:
    - project/public/index.html
    - project/public/about.html
    - project/public/README.md
    - project/public/assets/

  オプションファイル:
    - project/public/explanation.mp3

  パス検証:
    - 絶対パス（/で始まる）が相対パスに変換されていること
    - file:// プロトコルが使用されていないこと
    - 相対パスが正しく機能すること
```

### 完了条件
- ✅ project/public/ に必須ファイルが揃っている
- ✅ パス検証が完了している
- ✅ 不要ファイルが除去されている

### 次のステップ
- Portfolio App: 自動的にPhase 6（GitHub公開）へ進行
- Client App: ここで完了（Phase 6はスキップ）

## 🚀 Phase 6: GitHubポートフォリオ公開

### 概要
Portfolio用プロジェクトをGitHubに公開し、技術力をアピールする。
**重要**: `project/public/` の内容を一時ディレクトリ経由でGitHubにpush（slug方式・再利用可能）。同じアプリ名のフォルダは中身のみ更新する。

### 🎯 公開ポリシー（最重要）
**基本原則**: 「そのコードをローカルにコピーすれば、アプリが実行できる最低限のファイル」+ 「解説ドキュメント（README.md, about.html）」のみを公開。

**✅ 公開対象（実行に必要な最小限）:**
- index.html, about.html （公開ページ）
- assets/ （画像、CSS、JS等の静的ファイル）
- dist/ または build/ （ビルド済み成果物、必要な場合のみ）
- README.md （使い方・技術説明）
- explanation.mp3 （音声解説、オプション）
- package.json （依存関係情報、実行に必要な場合のみ）

**🚫 ドットファイル/フォルダの除外ルール（最優先）:**
ポートフォリオ公開では、**すべてのドットファイル/フォルダを除外**する。
理由: コード閲覧がメインのため、開発用設定ファイルは不要。迷ったら除外が安全。

| 絶対に公開しない（セキュリティリスク） | 理由 |
|----------------------------------------|------|
| .env, .env.* | 環境変数・シークレット |
| .firebase/, .firebaserc | デプロイキャッシュ・プロジェクト紐付け |
| .npmrc（認証付き） | npm認証トークン |
| .netrc | ネットワーク認証情報 |
| .htpasswd | 認証情報 |

| 本来は公開可能だが、ポートフォリオでは除外 | 理由 |
|--------------------------------------------|------|
| .gitignore | クローンした人向けだが、閲覧には不要 |
| .editorconfig, .prettierrc | コードスタイル統一（閲覧には不要） |
| .github/ | GitHub Actions等（ポートフォリオには不要） |
| .nvmrc | Node.jsバージョン指定（閲覧には不要） |

**⚠️ 推奨ルール:**
- ポートフォリオ公開ではドットファイルは**全て除外**
- 迷ったら除外する方が安全
- `_workflow/src/simplified_github_publisher.py` が自動で全ドットファイルを除外

**❌ その他の自動除外（開発プロセス・テストコード・認証情報）:**
- tests/, test/, __tests__/, spec/, specs/ （テストフォルダ）
- *.test.js, *.spec.ts, *.test.ts, *.spec.js, test_*.py （テストファイル）
- *agent*.py, *_agent.py, documenter_agent.py （開発ツール）
- generate_*.js, generate_*.py, audio_generator*.py （生成ツール）
- credentials/, secrets/, private/ （認証情報フォルダ）
- *.key.json, *.pem, *.cert, *.key, *.pfx （認証ファイル）
- env.*, *.env （環境変数ファイル）
- WBS*.json, DESIGN*.md, PROJECT_INFO.yaml, SPEC*.md （開発用ドキュメント）
- docs/, design/, planning/, documentation/ （内部ドキュメントフォルダ）
- node_modules/, venv/, env/, __pycache__/ （依存関係フォルダ）
- package-lock.json, yarn.lock, Pipfile.lock （ロックファイル）
- launch_app.command, *.command, *.sh, *.bat （実行スクリプト）
- pytest.ini, jest.config.js, karma.conf.js （設定ファイル）
- Thumbs.db, desktop.ini （OS生成ファイル）
- *~ （エディタ一時ファイル）
- *.log, *.out, logs/, log/ （ログファイル）
- *.backup, *.bak, *.old, backup/, old/, temp/, tmp/, cache/ （バックアップ）
- coverage/, htmlcov/ （カバレッジ）
- *.map （ソースマップ、必要な場合は個別判断）

**実装**: `_workflow/src/simplified_github_publisher.py` の `clean_public()` が自動で除外処理を実行
- ドットファイル/フォルダを最優先で除外（`.*` パターン）
- その後、上記リストのパターンを除外

### 実行条件
- PROJECT_INFO.yaml の development_type が "Portfolio App" の場合のみ
- Client用プロジェクトの場合はスキップ
- 統合ポートフォリオの場合は ai-agent-portfolio（mainブランチ）配下に `<app-name>/` を追加・更新する

### 実行前の必須確認
```
📌 Phase 6 実行前チェック
=================================
1. CLAUDE.mdを読み直す
2. PHASE_6_PUBLISHING_FLOW.md を確認 ← 重要！
3. worktreeがマージ済みか確認
4. project/public/ フォルダが生成済みか確認
5. 現在地が専用環境のmainブランチか確認
   pwd → ~/Desktop/AI-Apps/{app-name}-agent/
6. project/public/ が固定フォーマットで揃っているか再確認
=================================
```

### 実行手順

#### 6-0. Worktreeのマージ（削除しない）
```bash
# worktreeの作業を完了してmainにマージ
cd ~/Desktop/AI-Apps/{app-name}-agent/
git merge feat/{app-name}

# ⚠️ 重要: Worktreeは削除しない（将来の修正用に維持）
# git worktree remove は実行しない
echo "✅ Worktree維持: ./worktrees/mission-{app-name}"

# ブランチも維持
echo "✅ Branch維持: feat/{app-name}"

【Worktreeを維持する理由】
- 将来の修正や追加開発に即応できる
- ブランチ履歴を保持しGit管理を一貫させる
- 再構築コストを削減する
※ ディスク逼迫や完全終了時のみ、手動判断で削除を検討
```

#### 6-1. GitHub公開実行

**統合ポートフォリオ方式**（推奨）
```bash
# 専用環境のmainブランチで実行
cd ~/Desktop/AI-Apps/{app-name}-agent/

# _workflow/src/simplified_github_publisher.py が以下を自動実行:
# 1. project/public/ の内容を読み取り
# 2. 不要ファイルをクリーニング（tests/, *agent*.py, credentials/等を除外）
# 3. ai-agent-portfolioを一時ディレクトリにclone
# 4. {slug}/ フォルダを更新
# 5. mainブランチにpush（既存の場合はフォルダ丸ごと置き換え）
# 6. GitHub Actions 完了確認（deploy.yml → gh-pages 自動更新）← v9.0
# 7. リリースタグ作成（release.yml → zip 自動生成）← v9.0
# 8. 一時ディレクトリを削除

# --auto オプションで完全自動実行（対話なし）
python3 ./_workflow/src/simplified_github_publisher.py . --auto

# または対話モードで確認しながら実行
# python3 ./_workflow/src/simplified_github_publisher.py .

# 結果:
# - GitHub: https://github.com/sohei-t/ai-agent-portfolio/tree/main/{slug}/
```

**--auto オプションについて:**
- `--auto` または `-a`: 完全自動モード（対話なし、セキュリティチェックで問題があれば自動クリーンアップ）
- オプションなし: 対話モード（セキュリティチェック結果を確認後に公開）

**重要**:
- slug は日付なし（例: `todo-app-agent` → `todo-app`）
- 同じアプリ名の場合、フォルダ丸ごと削除→再作成で更新
- バージョン管理はGit履歴で実施

#### 6-2. GitHub Actions 完了確認 + リリースタグ作成（自動実行）
```
✅ GitHub Actions が gh-pages デプロイとリリース zip 作成を自動実行します

処理フロー:
1. main push → deploy.yml が自動起動 → gh-pages ブランチに同期 → GitHub Pages 更新
2. タグ push → release.yml が自動起動 → zip 作成 → Releases ページに公開

エージェントの役割（_workflow/src/simplified_github_publisher.py が自動実行）:
- deploy.yml の完了を gh run list で確認（最大90秒待機）
- リリースタグ（{slug}-v1.0.0）を作成 & push
- release.yml がトリガーされ zip が自動生成

確認方法:
- GitHub Pages: https://{username}.github.io/{repo-name}/{slug}/
- Releases: https://github.com/{username}/{repo-name}/releases
- Actions: gh run list --repo {username}/{repo-name} --limit 3
- 404の場合: 数分待ってから再確認（GitHub Pagesのビルドに時間がかかる場合あり）
```

#### 6-3. GitHub Pages初期設定（初回のみ）
```bash
# GitHub Pagesがまだ有効化されていない場合（初回のみ）
# gh-pagesブランチをソースとして設定
gh api repos/{owner}/$REPO_NAME/pages \
  --method POST \
  --field source='{"branch":"gh-pages","path":"/"}'

# または GitHub UI から設定:
# Settings → Pages → Source: gh-pages branch
```

#### 6-4. README.mdの更新（ルート用）
```markdown
# {App Name}

AI-generated full-stack application with comprehensive documentation.

## 🚀 Quick Start

1. **View Project**: Open `{app-name}/index.html`
2. **About**: Open `{app-name}/about.html`（`./explanation.mp3` が再生できることを確認）
3. **Docs**: Check `{app-name}/README.md`（公開用概要）
4. **Local Launch**: Double-click `launch_app.command`（任意）

## 📦 project/public/ Folder

The `project/public/` folder contains all essential files for publishing:
- `index.html` - Public entry point
- `about.html` - About page with embedded `explanation.mp3`
- `assets/` - All static assets (images/audio/JS/CSS)
- `README.md` - Public overview
- `explanation.mp3` - Audio walkthrough
- `dist/` - Built assets if needed (kept relative; node_modules/testコード/プロンプト類は含めない)

## 🛠 Technical Stack

{自動検出した技術スタックを記載}

## 📊 Portfolio

This project demonstrates:
- Full-stack development capabilities
- Test-driven development (TDD approach with comprehensive tests)
- Comprehensive documentation (README.md, about.html, explanation.mp3)
- AI-assisted development workflow

---

Generated with [Claude Code](https://github.com/anthropics/claude-code) and [この専用環境](https://github.com/{username}/この専用環境)
```

#### 6-5. 公開URL表示
```
========================================
🎉 GitHubポートフォリオ公開完了！
========================================

📦 リポジトリURL:
https://github.com/{username}/{repo-name}

📊 公開確認:
https://github.com/{username}/{repo-name}/tree/main/{app-name}

🌐 GitHub Pages（有効化した場合）:
https://{username}.github.io/{repo-name}/{app-name}/

✨ ポートフォリオの特徴:
- 実行可能なアプリケーション: index.html から即座に動作
- ドキュメント: about.html + explanation.mp3 で技術解説
- 品質保証: TDD approach with comprehensive tests

========================================
```

### タスク実行用プロンプト
```
あなたはGitHub公開担当者です。

【重要】実行場所の確認
- worktree作業完了後、mainにマージしてから実行
- 作業ディレクトリ: ~/Desktop/AI-Apps/{date}-{app-name}-agent/ （mainブランチ）

【必須確認】
1. PHASE_6_PUBLISHING_FLOW.md を読む
2. worktreeのマージ確認（すでにマージ済みか確認）
3. PROJECT_INFO.yamlを確認（Portfolio Appの場合のみ続行）

【公開方式の選択】
以下から選択（両方も可）:

A. 統合ポートフォリオ（複数アプリ管理）
   ```bash
   python3 ./_workflow/src/simplified_github_publisher.py .
   ```
   結果: ai-agent-portfolio/{app-name}/ （日付なしslug）

B. 個別リポジトリ（アプリ専用）
   ```bash
   python3 ./_workflow/src/simplified_github_publisher.py .
   ```
   結果: portfolio-todo-app リポジトリ

【slug管理の鉄則】
- 日付プレフィックス（20241210-）は自動除去
- 同じアプリ名 → 同じslug/リポジトリを更新（フォルダ名は固定、内容のみ差し替え）
- バージョン違いはGit履歴で管理

【注意事項】
- worktreeではなく、専用環境のmainブランチから実行
- .env等の機密ファイルは.gitignoreで除外
- project/public/ フォルダのみをpush（自動クリーニング）
- Client用プロジェクトはpushしない

【成果物】
- GitHubリポジトリURL
- GitHub Pages URL（設定した場合）
- slug形式での管理確認
```

========================================
```

## 📝 サブエージェントへの標準完了条件

【完了条件】
- テスト合格
- 動作確認済み
- コミット完了（メッセージ: "feat: {機能名} implemented by {エージェント名}"）

## 🛡️ エラーハンドリング

### 自動リカバリシステム
```yaml
error_recovery:
  level_1_retry:
    - ネットワークエラー → 3回自動リトライ
    - タイムアウト → exponential backoff
    - 一時的なロック → 待機後リトライ

  level_2_fallback:
    - テスト失敗 → 簡略版実装
    - ツール不在 → 代替ツール使用
    - リソース不足 → 機能削減

  level_3_rollback:
    - クリティカルエラー → 前のチェックポイントに戻る
    - セキュリティ問題 → 即座停止＆通知
    - データ破損 → バックアップから復元

詳細: ERROR_HANDLING_STRATEGY.md を参照
```

## ✅ 実行前チェックリスト

□ `WORKFLOW_AUTOMATION_V6.md` を読んだ
□ `WORKFLOW_CHECKPOINT_SYSTEM.md` を読んだ（重要）
□ `FRONTEND_DESIGN_SKILL_GUIDE.md` を読んだ（必須）
□ `WBS_CRITICAL_PATH_TEMPLATE.json` を確認
□ `ERROR_HANDLING_STRATEGY.md` を理解
□ `_workflow/config/agent_config.yaml` を読んだ
□ `_workflow/config/WBS_TEMPLATE.json` を読んだ
□ worktree が作成されている
□ Taskツールで並列実行する準備ができている
□ **frontend-design スキルを UI/HTML生成時に必ず使用する**
□ クリティカルパスを優先実行する
□ エラー時は自動リカバリを試みる
□ フェーズ5で _workflow/src/documenter_agent.py 実行を忘れない

## 🚫 禁止事項

- この専用環境 ディレクトリでの直接開発
- テスト未実行でのマージ
- 品質基準を満たさないコミット
- **階層別コンテンツのフォルダ分離禁止**: 入門・初級・中級・上級などレベル別コンテンツを生成する際、階層ごとにサブフォルダを作成してはならない。レベルの識別はファイル名のみで行うこと
  ```
  ✅ 正しい例（フラット構造 + ファイル名で識別）:
    project/public/
    ├── intro-basics.html
    ├── beginner-variables.html
    ├── intermediate-functions.html
    └── advanced-patterns.html

  ❌ 禁止例（階層別フォルダ）:
    project/public/
    ├── intro/
    │   └── basics.html
    ├── beginner/
    │   └── variables.html
    ├── intermediate/
    │   └── functions.html
    └── advanced/
        └── patterns.html
  ```

## 💡 トラブルシューティング

ワークフローが実行されない場合：
1. `python _workflow/src/workflow_orchestrator.py creative_webapp {名前}` を実行
2. Taskツールで並列実行（1メッセージで複数Task）
3. サブエージェントプロンプトに品質基準を明記
- 公開用ファイルリストをREADME.mdに記載し、about.htmlからexplanation.mp3が相対パス（例: ./explanation.mp3）で再生できることを確認
- index.html/about.htmlの主要導線がスマホ縦・横どちらでもクリック/タップ可能であることを簡易確認（デバッガ不要の目視・ブラウザサイズ変更でOK）
```

### Phase 5 自動検証（実行例）
```bash
validate_phase5() {
  required_files=(
    "project/public/index.html"
    "project/public/about.html"
    "project/public/README.md"
    "project/public/assets/"
  )
  for file in "${required_files[@]}"; do
    [ -e "$file" ] || echo "❌ Missing: $file"
  done
  [ -e "project/public/explanation.mp3" ] && echo "✅ Audio present" || echo "⚠️ Audio skipped"
}
```

---

## AI Orchestrator 進捗レポート規約

### PROGRESS.yaml の管理

プロジェクトルートに `PROGRESS.yaml` が配置されている。このファイルはワークフロー全体を通じて、進捗状況を記録するためのチェックシートである。外部の AI Orchestrator ダッシュボード（localhost:3456）がこのファイルを定期的に読み取り、進捗を視覚化する。

### YAML 構造

```yaml
project:
  name: "アプリ名"
  agent_type: "この専用環境"
  status: "in_progress"    # idle | in_progress | completed | failed | paused
  started_at: "ISO8601"
  updated_at: "ISO8601"

progress:
  overall_percent: 35       # 0-100
  current_phase: "phase2-implementation"

phases:
  - name: "Phase 0: Initialization"
    status: "completed"     # pending | in_progress | completed | failed | skipped | paused
    steps:
      - name: "Git worktree creation"
        done: true          # true | false
  # ...

errors: []                  # エラーメッセージの配列
```

### 更新タイミング（必須）

以下のタイミングで **必ず** PROGRESS.yaml を更新すること:

1. **フェーズ開始時**:
   - 該当フェーズの `status` → `"in_progress"`
   - `progress.current_phase` を更新（例: `"phase2-implementation"`）
   - `project.status` → `"in_progress"`（初回のみ）
   - `project.updated_at` に現在時刻を記録

2. **ステップ完了時**:
   - 該当ステップの `done` → `true`
   - `progress.overall_percent` を再計算（完了ステップ数 / 総ステップ数 × 100）

3. **フェーズ完了時**:
   - 該当フェーズの `status` → `"completed"`
   - `progress.overall_percent` を再計算

4. **エラー発生時**:
   - `errors` 配列にエラーメッセージを追加
   - 該当フェーズの `status` → `"failed"`

5. **全体完了時**:
   - `project.status` → `"completed"`
   - `progress.overall_percent` → `100`

### progress.overall_percent の計算方法

```
overall_percent = (全フェーズの done: true のステップ合計 / 全フェーズの総ステップ数) × 100
```

### 厳守事項

- PROGRESS.yaml の構造（キー名、フェーズ数、ステップ数）を変更しないこと
- `project.updated_at` は更新の度に現在時刻で上書きすること
- YAML として valid な形式を維持すること
- ステップの追加・削除はしないこと

## 📍 専用環境での注意事項

**このディレクトリは専用のアプリ開発環境です**
- アプリ名: picture-merge-app-v2
- 環境パス: /Users/sohei/Desktop/AI-Apps/picture-merge-app-v2-agent

### 開発完了後の処理

アプリが完成し、すべてのテストが合格したら：

1. **リリース版作成**
   ```bash
   bash _workflow/scripts/release.sh
   ```

2. **GitHubポートフォリオに公開**
   ```bash
   bash _workflow/scripts/publish_to_portfolio.sh
   ```

### ディレクトリ構造
```
picture-merge-app-v2-agent/
├── CLAUDE.md                      # ワークフローガイド
├── PROJECT_INFO.yaml              # プロジェクト情報
├── project/                       # アプリ本体
│   └── public/                    # GitHub公開用
├── worktrees/                     # Phase別開発環境（9個）
└── _workflow/                     # ワークフロー関連（全集約）
    ├── src/                       # 実行スクリプト
    ├── docs/                      # ドキュメント
    ├── config/                    # 設定ファイル
    ├── scripts/                   # シェルスクリプト
    └── credentials/               # API認証
```
