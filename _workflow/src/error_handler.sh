#!/bin/bash

# エラーハンドリング共通関数

# エラー時の処理
handle_error() {
    local exit_code=$?
    local line_no=$1
    local script_name=$(basename $0)

    echo -e "\033[0;31m❌ エラーが発生しました！\033[0m"
    echo -e "スクリプト: $script_name"
    echo -e "行番号: $line_no"
    echo -e "終了コード: $exit_code"

    # ログファイルに記録
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] ERROR in $script_name at line $line_no (exit: $exit_code)" >> error.log

    exit $exit_code
}

# トラップ設定
set_error_trap() {
    set -eE
    trap 'handle_error $LINENO' ERR
}

# リトライ機能
retry_command() {
    local max_attempts=${1:-3}
    local delay=${2:-5}
    local command="${@:3}"
    local attempt=0

    while [ $attempt -lt $max_attempts ]; do
        attempt=$((attempt + 1))
        echo "実行中 (試行 $attempt/$max_attempts): $command"

        if eval $command; then
            return 0
        fi

        if [ $attempt -lt $max_attempts ]; then
            echo "失敗。${delay}秒後に再試行..."
            sleep $delay
        fi
    done

    echo "最大試行回数に達しました。失敗。"
    return 1
}

# プログレス表示
show_progress() {
    local current=$1
    local total=$2
    local width=50
    local percent=$((current * 100 / total))
    local filled=$((width * current / total))

    printf "\r["
    printf "%${filled}s" | tr ' ' '='
    printf "%$((width - filled))s" | tr ' ' ' '
    printf "] %3d%% (%d/%d)" $percent $current $total

    if [ $current -eq $total ]; then
        echo ""
    fi
}
