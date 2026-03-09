# 🔄 外部API連携プロジェクト専用ワークフロー

## 📋 概要

外部API（Vertex AI、LINE、OpenAI等）を使用するプロジェクトでは、
通常のワークフローに加えて、人間の承認と作業が必要な特別なフェーズが追加されます。

## 🎯 新しいワークフロー

### Phase -1: 事前承認フェーズ（新規追加）

```yaml
pre_approval_phase:
  duration: "5-10分"
  type: "対話型"

  step_1_requirements_gathering:
    ai_asks:
      - "どのようなシステムを構築しますか？"
      - "使用したい外部APIは？"
      - "想定ユーザー数は？"
      - "月額予算の上限は？"

  step_2_feasibility_analysis:
    ai_analyzes:
      - 技術的実現可能性
      - コスト見積もり
      - 必要な権限/API
      - セキュリティリスク

  step_3_proposal_generation:
    ai_creates:
      - PROPOSAL.md（提案書）
      - COST_ESTIMATE.md（コスト見積もり）
      - HUMAN_TASKS.md（人間のタスクリスト）
      - ARCHITECTURE.md（システム設計）

  step_4_approval_checkpoint:
    format: |
      ========================================
      📋 実装計画の承認
      ========================================

      【システム概要】
      - タイプ: {system_type}
      - 主要機能: {features}
      - 外部API: {apis}

      【コスト見積もり】
      - 初期費用: $0
      - 月額運用: ${monthly_cost}
      - 従量課金: {usage_based}

      【必要な作業（人間）】
      1. {human_task_1} (10分)
      2. {human_task_2} (10分)
      3. {human_task_3} (5分)
      推定作業時間: 合計30分

      【AIが自動生成するもの】
      ✅ 完全なソースコード
      ✅ インフラ設定（IaC）
      ✅ デプロイスクリプト
      ✅ ドキュメント

      この計画で進めてよろしいですか？(y/n)
      ========================================

    user_response:
      yes: "Phase 0へ進む"
      no: "要件を再確認"
      modify: "部分的に修正して再提案"
```

### Phase 0: 環境準備（拡張版）

```yaml
environment_setup:
  parallel_tasks:
    ai_preparations:
      - プロジェクト構造生成
      - 依存関係定義
      - .env.example作成
      - セキュリティ設定テンプレート

    human_preparations:
      guided_by: "SETUP_GUIDE.md"
      tasks:
        - "[ ] GCPプロジェクト作成"
        - "[ ] 必要なAPIを有効化"
        - "[ ] サービスアカウント作成"
        - "[ ] APIキー取得"
        - "[ ] .envファイルに設定"

  synchronization_point:
    ai_validates:
      - 環境変数の存在確認（値は見ない）
      - API接続テスト（モック使用）
      - 権限チェックスクリプト実行
```

### Phase 1-5: 通常の開発フロー（API対応版）

```yaml
development_with_apis:
  phase_1_requirements:
    additional:
      - API仕様の詳細分析
      - レート制限の考慮
      - エラーハンドリング戦略

  phase_2_implementation:
    api_specific:
      - APIクライアントラッパー作成
      - リトライロジック実装
      - キャッシング層の実装
      - モック/スタブの準備

  phase_3_testing:
    api_testing:
      - モックAPIでの単体テスト
      - 統合テスト（制限付き実API）
      - レート制限のテスト
      - エラーハンドリングテスト

  phase_4_quality:
    api_optimization:
      - API呼び出し最適化
      - バッチ処理の実装
      - キャッシュ戦略の改善
      - コスト分析と最適化

  phase_5_documentation:
    additional_docs:
      - API_SETUP.md
      - DEPLOYMENT_GUIDE.md
      - COST_MANAGEMENT.md
      - MONITORING_GUIDE.md
```

### Phase 6: デプロイ準備（新規追加）

```yaml
deployment_preparation:
  duration: "10-15分"

  ai_generates:
    infrastructure_code:
      - Dockerfile
      - docker-compose.yml
      - kubernetes/manifests.yaml
      - terraform/*.tf

    deployment_scripts:
      - deploy_to_gcp.sh
      - deploy_to_gas.sh
      - rollback.sh
      - health_check.sh

    ci_cd_configs:
      - .github/workflows/deploy.yml
      - cloudbuild.yaml
      - .gitlab-ci.yml

  deployment_checklist:
    format: |
      ========================================
      🚀 デプロイ前チェックリスト
      ========================================

      【環境変数設定】
      □ 本番用APIキー設定
      □ データベース接続情報
      □ 認証情報

      【インフラ準備】
      □ Cloud Runサービス作成
      □ Cloud SQLインスタンス（必要な場合）
      □ Cloud Storageバケット

      【セキュリティ】
      □ ファイアウォールルール
      □ IAM権限設定
      □ Secret Manager設定

      【モニタリング】
      □ Cloud Logging有効化
      □ アラート設定
      □ 予算アラート

      準備完了したら 'ready' と入力:
      ========================================

  final_confirmation:
    ai_provides:
      - ワンクリックデプロイコマンド
      - ロールバック手順
      - 動作確認手順
```

## 🤖 エージェント間の連携

### API統合専門エージェント（新規）

```yaml
api_integration_agent:
  responsibilities:
    - API仕様の理解と実装
    - 認証フローの実装
    - エラーハンドリング
    - レート制限対策

  outputs:
    - api_client.py/js
    - auth_handler.py/js
    - rate_limiter.py/js
    - api_mock.py/js
```

### インフラエージェント（新規）

```yaml
infrastructure_agent:
  responsibilities:
    - IaCコード生成
    - デプロイメント設定
    - スケーリング設定
    - モニタリング設定

  outputs:
    - terraform/
    - kubernetes/
    - monitoring/
    - scripts/
```

## 📊 承認ポイントと人間の介入

### 承認が必要なポイント

```yaml
approval_points:
  pre_development:
    - システム設計の承認
    - コスト見積もりの承認
    - 使用API/サービスの承認

  during_development:
    - 追加API/機能の承認
    - コスト増加の承認

  pre_deployment:
    - 本番環境へのデプロイ承認
    - セキュリティ設定の確認

human_interventions:
  mandatory:
    - APIキーの設定
    - 課金設定
    - 本番デプロイの実行

  optional:
    - アーキテクチャのレビュー
    - コードレビュー
    - パフォーマンステスト
```

## 💬 対話例

### 初期対話

```markdown
AI: 外部API連携システムを構築しますね。いくつか確認させてください。

1. 構築したいシステムのタイプは？
USER: Vertex AIを使ったRAG検索システム

AI: 理解しました。RAG検索システムですね。追加で確認です：

2. 想定される月間クエリ数は？
USER: 10,000クエリ程度

3. 月額予算の上限は？
USER: $200まで

AI: ありがとうございます。以下の構成を提案します：

【システム構成】
- Frontend: Next.js (Vercel無料枠)
- Backend: FastAPI (Cloud Run)
- Vector DB: Vertex AI Matching Engine
- Storage: Cloud Storage

【月額コスト見積もり】
- Cloud Run: $20-30
- Vertex AI: $100-150
- Storage: $10
- 合計: $130-190（予算内）

【あなたに必要な作業（30分）】
1. GCPプロジェクト作成（10分）
2. Vertex AI API有効化（5分）
3. サービスアカウント作成（10分）
4. 環境変数設定（5分）

この計画で進めてよろしいですか？(y/n)
```

### デプロイ前の最終確認

```markdown
AI: 開発が完了しました！デプロイの準備をします。

【生成完了したもの】
✅ Backendコード (FastAPI)
✅ Frontendコード (Next.js)
✅ Dockerfile & docker-compose
✅ デプロイスクリプト
✅ ドキュメント

【デプロイ前チェック】
以下を確認してください：

1. 環境変数設定
   cat .env.example を参考に .env を作成してください

2. GCP設定
   - Project ID: 設定済み？ [y/n]
   - Vertex AI: 有効化済み？ [y/n]
   - Service Account: 作成済み？ [y/n]

3. デプロイ実行
   すべて準備できたら、以下を実行：
   ./deploy_to_gcp.sh

問題なければ 'ready' と入力してください:
```

## 🎯 UX改善ポイント

### 1. プログレッシブディスクロージャー

```yaml
information_disclosure:
  level_1_basic:
    - "何を作りたいですか？"
    - 簡単な選択肢提示

  level_2_details:
    - 選択に基づいた詳細質問
    - 必要な情報のみ収集

  level_3_advanced:
    - オプション設定
    - カスタマイズ
```

### 2. エラー予防

```yaml
error_prevention:
  validation_scripts:
    - check_prerequisites.sh
    - validate_env.sh
    - test_api_connection.sh

  guided_setup:
    - ステップバイステップガイド
    - ビジュアル確認
    - 自動診断ツール
```

### 3. コスト透明性

```yaml
cost_transparency:
  real_time_estimation:
    - 設定変更時の即座の反映
    - 月額/年額の切り替え表示

  cost_breakdown:
    - 各サービスの内訳
    - 使用量ベースの予測
    - 節約オプションの提示
```

## ✅ メリット

1. **透明性**: 何にコストがかかるか、人間が何をすべきか明確
2. **安全性**: APIキーなど機密情報は人間が管理
3. **効率性**: コード生成は完全自動、設定のみ人間
4. **柔軟性**: 段階的な承認で、途中変更も可能
5. **学習機会**: 生成されたコードから学べる

これにより、外部API連携の複雑なシステムも、安全かつ効率的に構築できます！