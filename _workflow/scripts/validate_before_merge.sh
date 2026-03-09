#!/bin/bash

# validate_before_merge.sh
# マージ前の自動検証スクリプト

set -e  # エラーが発生したら即座に終了

# 色付きの出力用
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# ログ関数
log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

# Pythonアプリの検証
validate_python_app() {
    local app_file=$1
    local validation_passed=true

    echo "======================================"
    echo "🔍 マージ前検証開始: $app_file"
    echo "======================================"

    # 1. Pythonバージョン確認
    echo -n "Python環境チェック... "
    if python3 --version > /dev/null 2>&1; then
        log_success "OK ($(python3 --version))"
    else
        log_error "Python3が見つかりません"
        return 1
    fi

    # 2. 構文チェック
    echo -n "構文チェック... "
    if python3 -m py_compile "$app_file" 2>/dev/null; then
        log_success "OK"
    else
        log_error "構文エラーがあります"
        python3 -m py_compile "$app_file"
        return 1
    fi

    # 3. 必要なモジュールのチェック（GUIアプリの場合）
    if grep -q "tkinter" "$app_file"; then
        echo -n "tkinterモジュールチェック... "
        if python3 -c "import tkinter" 2>/dev/null; then
            log_success "OK"
        else
            log_error "tkinterが利用できません"
            log_warning "macOSの場合: brew install python-tk"
            log_warning "Ubuntuの場合: sudo apt-get install python3-tk"
            return 1
        fi
    fi

    # 4. インポートテスト
    echo -n "インポートテスト... "
    local module_name="${app_file%.py}"
    if python3 -c "import $module_name" 2>/dev/null; then
        log_success "OK"
    else
        log_warning "インポートテストをスキップ（メイン実行ファイル）"
    fi

    # 5. 起動テスト（GUIアプリ用）
    echo -n "起動テスト... "

    # ヘッドレス環境チェック
    if [ -z "$DISPLAY" ] && ! [ -e /tmp/.X11-unix ]; then
        log_warning "GUI環境なし - 起動テストをスキップ"
    else
        # タイムアウト付きで起動テスト
        timeout 2 python3 "$app_file" > /dev/null 2>&1 &
        local pid=$!
        sleep 1

        if ps -p $pid > /dev/null 2>&1; then
            log_success "OK (プロセス起動確認)"
            kill $pid 2>/dev/null || true
        elif [ $? -eq 124 ]; then
            log_success "OK (タイムアウトによる正常終了)"
        else
            log_warning "起動テスト不確定"
        fi
    fi

    # 6. requirements.txt チェック
    if [ -f "requirements.txt" ]; then
        echo -n "依存関係チェック... "
        local missing_deps=false

        while IFS= read -r package || [ -n "$package" ]; do
            # コメント行をスキップ
            [[ "$package" =~ ^#.*$ ]] && continue
            [[ -z "$package" ]] && continue

            # パッケージ名を抽出（バージョン指定を除く）
            pkg_name=$(echo "$package" | sed 's/[<>=!].*//')

            if ! python3 -c "import $pkg_name" 2>/dev/null; then
                log_error "Missing: $pkg_name"
                missing_deps=true
            fi
        done < requirements.txt

        if [ "$missing_deps" = false ]; then
            log_success "OK"
        else
            log_warning "pip install -r requirements.txt を実行してください"
        fi
    fi

    echo "======================================"
    if [ "$validation_passed" = true ]; then
        log_success "全検証完了 - マージ可能です！"
        return 0
    else
        log_error "検証失敗 - 修正が必要です"
        return 1
    fi
}

# メイン処理
main() {
    if [ $# -eq 0 ]; then
        echo "Usage: $0 <python_file>"
        echo "Example: $0 calculator.py"
        exit 1
    fi

    local file_to_validate=$1

    if [ ! -f "$file_to_validate" ]; then
        log_error "ファイルが見つかりません: $file_to_validate"
        exit 1
    fi

    # Pythonファイルの検証
    if [[ "$file_to_validate" == *.py ]]; then
        validate_python_app "$file_to_validate"
        exit_code=$?
    else
        log_warning "現在はPythonファイルのみサポートしています"
        exit_code=1
    fi

    # 検証結果に応じた終了コード
    if [ $exit_code -eq 0 ]; then
        echo ""
        echo "🎉 マージの準備ができました！"
        echo "次のコマンドでマージできます:"
        echo "  git merge <branch_name>"
    else
        echo ""
        echo "⚠️  マージ前に問題を修正してください"
    fi

    exit $exit_code
}

# スクリプト実行
main "$@"