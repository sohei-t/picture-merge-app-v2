#!/bin/bash
# =============================================================
# Picture Merge App v2 - Launcher
# =============================================================
# ダブルクリックでフロントエンド＋バックエンドを起動し、
# ブラウザで自動的にアプリを開きます。
# Ctrl+C で両サーバーを停止します。
# =============================================================

set -e

# スクリプトのあるディレクトリに移動
cd "$(dirname "$0")"
PROJECT_DIR="$(pwd)"

echo "============================================================="
echo "  Picture Merge App v2"
echo "============================================================="
echo ""

# --------------------------------------------------
# 前提条件チェック
# --------------------------------------------------

# Python 確認
if ! command -v python3 &>/dev/null; then
  echo "❌ Python3 が見つかりません。"
  echo "   Homebrew: brew install python3"
  echo "   公式サイト: https://www.python.org/downloads/"
  read -rp "Enter を押して終了..."
  exit 1
fi

# Node.js 確認
if ! command -v node &>/dev/null; then
  echo "❌ Node.js が見つかりません。"
  echo "   Homebrew: brew install node"
  echo "   公式サイト: https://nodejs.org/"
  read -rp "Enter を押して終了..."
  exit 1
fi

# npm 確認
if ! command -v npm &>/dev/null; then
  echo "❌ npm が見つかりません。Node.js と一緒にインストールされます。"
  read -rp "Enter を押して終了..."
  exit 1
fi

echo "✅ Python3: $(python3 --version 2>&1)"
echo "✅ Node.js:  $(node --version 2>&1)"
echo "✅ npm:      $(npm --version 2>&1)"
echo ""

# --------------------------------------------------
# バックグラウンドプロセスのクリーンアップ
# --------------------------------------------------
BACKEND_PID=""
FRONTEND_PID=""

cleanup() {
  echo ""
  echo "🛑 サーバーを停止しています..."
  if [ -n "$BACKEND_PID" ] && kill -0 "$BACKEND_PID" 2>/dev/null; then
    kill "$BACKEND_PID" 2>/dev/null
    wait "$BACKEND_PID" 2>/dev/null || true
    echo "   バックエンドサーバー停止"
  fi
  if [ -n "$FRONTEND_PID" ] && kill -0 "$FRONTEND_PID" 2>/dev/null; then
    kill "$FRONTEND_PID" 2>/dev/null
    wait "$FRONTEND_PID" 2>/dev/null || true
    echo "   フロントエンドサーバー停止"
  fi
  echo "👋 終了しました"
  exit 0
}

trap cleanup INT TERM EXIT

# --------------------------------------------------
# バックエンド: Python venv + 依存関係
# --------------------------------------------------
echo "📦 バックエンド準備中..."

VENV_DIR="$PROJECT_DIR/backend/.venv"

if [ ! -d "$VENV_DIR" ]; then
  echo "   仮想環境を作成しています（初回のみ、数分かかる場合があります）..."
  python3 -m venv "$VENV_DIR"
fi

# venv を有効化
source "$VENV_DIR/bin/activate"

# 依存関係インストール（pip の出力で未インストールかどうか判定）
if [ ! -f "$VENV_DIR/.deps_installed" ]; then
  echo "   依存関係をインストールしています（初回のみ）..."
  pip install --upgrade pip -q
  pip install -r "$PROJECT_DIR/backend/requirements.txt" -q
  touch "$VENV_DIR/.deps_installed"
  echo "   ✅ バックエンド依存関係インストール完了"
else
  echo "   ✅ バックエンド依存関係は既にインストール済み"
fi

# --------------------------------------------------
# フロントエンド: npm install
# --------------------------------------------------
echo "📦 フロントエンド準備中..."

if [ ! -d "$PROJECT_DIR/frontend/node_modules" ]; then
  echo "   npm install を実行しています（初回のみ、数分かかる場合があります）..."
  cd "$PROJECT_DIR/frontend"
  npm install
  cd "$PROJECT_DIR"
  echo "   ✅ フロントエンド依存関係インストール完了"
else
  echo "   ✅ フロントエンド依存関係は既にインストール済み"
fi

echo ""
echo "============================================================="
echo "  🚀 サーバーを起動します"
echo "============================================================="
echo ""

# --------------------------------------------------
# バックエンドサーバー起動
# --------------------------------------------------
echo "🔧 バックエンドサーバー起動中 (http://localhost:8000) ..."
cd "$PROJECT_DIR/backend"
"$VENV_DIR/bin/uvicorn" app.main:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!
cd "$PROJECT_DIR"

# バックエンドの起動を少し待つ
sleep 2

# --------------------------------------------------
# フロントエンドサーバー起動
# --------------------------------------------------
echo "🎨 フロントエンドサーバー起動中 (http://localhost:5173) ..."
cd "$PROJECT_DIR/frontend"
npm run dev &
FRONTEND_PID=$!
cd "$PROJECT_DIR"

# フロントエンドの起動を待つ
sleep 3

# --------------------------------------------------
# ブラウザを開く
# --------------------------------------------------
echo ""
echo "🌐 ブラウザを開いています..."
open "http://localhost:5173"

echo ""
echo "============================================================="
echo "  ✅ アプリが起動しました！"
echo ""
echo "  フロントエンド: http://localhost:5173"
echo "  バックエンドAPI: http://localhost:8000"
echo "  APIドキュメント: http://localhost:8000/docs"
echo ""
echo "  終了するには Ctrl+C を押してください"
echo "============================================================="
echo ""

# 両方のプロセスが動いている間待機
wait
