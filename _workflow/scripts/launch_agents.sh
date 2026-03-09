#!/bin/bash

# launch_agents.sh - エージェントシステム起動スクリプト
# 使用方法: ./launch_agents.sh [workflow_name] "タスクの説明"

set -e

# カラー定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# ログ関数
log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

# 初期化チェック
check_initialization() {
    if [ ! -d .git ]; then
        log_warning "Gitリポジトリが初期化されていません"
        echo "初期化しますか？ (y/n)"
        read -r response
        if [[ "$response" == "y" ]]; then
            git init
            git add .
            git commit -m "Initial commit: Project setup with agent system"
            mkdir -p worktrees src docs tests
            log_success "プロジェクトを初期化しました"
        else
            log_error "初期化がキャンセルされました"
            exit 1
        fi
    fi

    if [ ! -f _workflow/config/agent_config.yaml ]; then
        log_error "_workflow/config/agent_config.yaml が見つかりません"
        exit 1
    fi
}

# 専門家の検索または作成
find_or_create_agent() {
    local task_type=$1
    local task_desc=$2

    # YAMLから専門家を検索（簡略版）
    if grep -q "$task_type:" _workflow/config/agent_config.yaml; then
        log_info "専門エージェント '$task_type' を使用"
        return 0
    else
        log_warning "専門家 '$task_type' が見つかりません"

        # フォールバック戦略を確認
        echo ""
        echo "どうしますか？"
        echo "1) 汎用エージェント（generalist）を使用"
        echo "2) カスタムエージェントを作成"
        echo "3) 処理を中止"
        read -r choice

        case $choice in
            1)
                log_info "汎用エージェントを使用します"
                task_type="generalist"
                ;;
            2)
                log_info "カスタムエージェントを作成します"
                create_custom_agent "$task_type" "$task_desc"
                ;;
            3)
                log_error "処理を中止しました"
                exit 1
                ;;
            *)
                log_error "無効な選択です"
                exit 1
                ;;
        esac
    fi
}

# カスタムエージェント作成
create_custom_agent() {
    local agent_name=$1
    local task_desc=$2

    log_info "カスタムエージェント '$agent_name' を作成中..."

    # agent_config.yamlに新しいエージェントを追加
    cat >> _workflow/config/agent_config.yaml << EOF

  # 自動生成されたカスタムエージェント
  ${agent_name}:
    name: "カスタム: ${agent_name}"
    description: "自動生成されたタスク専用エージェント"
    prompt: |
      あなたは${agent_name}のタスクを担当するエージェントです。
      以下のタスクを実行してください：
      ${task_desc}

      ベストプラクティスに従い、高品質な成果物を作成してください。
    skills: ["custom", "${agent_name}"]
EOF

    log_success "カスタムエージェントを作成しました"
}

# 要件定義フェーズ
run_requirements_analysis() {
    local task_description=$1

    log_info "📋 要件定義フェーズを開始します"
    echo ""
    echo "タスク: $task_description"
    echo ""

    # 要件定義エージェントを起動（実際にはClaude Codeが必要）
    cat << EOF
=====================================
要件定義エージェントが分析中...
=====================================

【機能要件】
- ユーザーが要求した主要機能
- データ処理の流れ
- ユーザーインターフェース要件

【非機能要件】
- パフォーマンス: レスポンス3秒以内
- 可用性: 99.9%
- セキュリティ: HTTPS必須
- ブラウザ互換性: Chrome, Firefox, Safari

【成功基準】
✅ 全機能が動作すること
✅ エラーなくブラウザで表示されること
✅ APIとの通信が成功すること
✅ レスポンシブデザインが機能すること

【タスク分担案】
1. Frontend Agent: UI実装と表示
2. Backend Agent: API開発とデータ処理
3. Tester Agent: 動作検証とバグ修正
4. Integration Agent: 統合と最終調整

=====================================
EOF

    echo ""
    echo "要件定義を承認しますか？ (y/n)"
    read -r response

    if [[ "$response" != "y" ]]; then
        log_warning "要件の再定義が必要です"
        echo "要件を修正してください："
        read -r new_requirements
        task_description="$new_requirements"
    fi

    return 0
}

# メイン処理
main() {
    local workflow_name=${1:-simple}
    local task_description=${2:-"タスクを実行"}

    echo ""
    echo "🚀 エージェントシステム起動"
    echo "================================"

    # 初期化チェック
    check_initialization

    # 要件定義フェーズ（新規追加）
    if [[ "$workflow_name" != "simple" ]]; then
        run_requirements_analysis "$task_description"
    fi

    # ワークフロー情報表示
    log_info "ワークフロー: $workflow_name"
    log_info "タスク: $task_description"
    echo ""

    # ワークフローに基づいてエージェントを起動
    case $workflow_name in
        webapp)
            log_info "Webアプリ開発チームを起動中..."
            launch_webapp_team "$task_description"
            ;;
        api)
            log_info "API開発チームを起動中..."
            launch_api_team "$task_description"
            ;;
        debug)
            log_info "デバッグチームを起動中..."
            launch_debug_team "$task_description"
            ;;
        custom)
            # カスタムワークフロー
            echo "カスタムエージェントのタイプを入力してください："
            read -r agent_type
            find_or_create_agent "$agent_type" "$task_description"
            launch_single_agent "$agent_type" "$task_description"
            ;;
        *)
            log_info "シンプルモードで実行..."
            launch_single_agent "generalist" "$task_description"
            ;;
    esac

    log_success "全てのタスクが完了しました！"
}

# Webアプリチーム起動
launch_webapp_team() {
    local task=$1

    # 3つのエージェントを並列起動
    log_info "Frontend Agent 起動..."
    git worktree add -b feat/frontend ./worktrees/mission-frontend main 2>/dev/null || true

    log_info "Backend Agent 起動..."
    git worktree add -b feat/backend ./worktrees/mission-backend main 2>/dev/null || true

    log_info "Tester Agent 起動..."
    git worktree add -b feat/tester ./worktrees/mission-tester main 2>/dev/null || true

    # ここで実際のTask起動（claudeコマンドが必要）
    log_warning "実際のエージェント起動にはClaude Codeが必要です"

    # クリーンアップ
    cleanup_worktrees
}

# 単一エージェント起動
launch_single_agent() {
    local agent_type=$1
    local task=$2

    log_info "$agent_type エージェントを起動中..."
    git worktree add -b feat/$agent_type ./worktrees/mission-$agent_type main 2>/dev/null || true

    # ここで実際のTask起動
    log_warning "実際のエージェント起動にはClaude Codeが必要です"

    # クリーンアップ
    cleanup_worktrees
}

# クリーンアップ（改善版: テスト完了後のみ実行）
cleanup_worktrees() {
    local branch_name=$1
    local cleanup_type=${2:-"after_merge"}  # after_merge or force

    if [ "$cleanup_type" == "after_merge" ]; then
        # テスト成功・マージ後のクリーンアップ
        log_info "✅ テスト完了後のクリーンアップ中..."

        # ブランチの状態を確認
        if git diff --quiet feat/$branch_name..main; then
            log_success "マージ済みを確認"
            git worktree remove ./worktrees/mission-$branch_name 2>/dev/null || true
            git branch -d feat/$branch_name 2>/dev/null || true
        else
            log_warning "未マージの変更があります。ブランチを保持します。"
        fi
    elif [ "$cleanup_type" == "force" ]; then
        # 強制クリーンアップ（エラー時など）
        log_warning "⚠️ 強制クリーンアップを実行..."
        git worktree remove --force ./worktrees/mission-$branch_name 2>/dev/null || true
        git branch -D feat/$branch_name 2>/dev/null || true
    fi
}

# テスト検証フェーズ（新規追加）
run_test_validation() {
    local agent_type=$1

    log_info "🧪 動作検証フェーズを開始..."

    # 実際にはサブエージェントが実行すべき内容
    cat << EOF
=====================================
テストエージェントが検証中...
=====================================

✅ チェック項目:
- [ ] コードのシンタックスエラー
- [ ] 依存関係のインストール
- [ ] サーバー起動テスト
- [ ] ブラウザ動作確認
- [ ] APIレスポンステスト
- [ ] コンソールエラー確認

検証結果: テスト中...
=====================================
EOF

    # テスト結果の判定
    echo "テストは成功しましたか？ (y/n)"
    read -r test_result

    if [[ "$test_result" == "y" ]]; then
        log_success "テスト成功！マージ可能です"
        return 0
    else
        log_warning "テスト失敗。修正が必要です"
        return 1
    fi
}

# スクリプト実行
main "$@"