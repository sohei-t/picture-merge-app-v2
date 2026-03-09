#!/usr/bin/env python3
"""
起動スクリプト自動生成ツール
アプリケーションの種類を検出し、最適な起動スクリプトを生成
"""

import os
import json
from pathlib import Path
from typing import Dict, Optional, List

class LauncherGenerator:
    """
    1クリック起動用スクリプトの自動生成
    """

    def __init__(self, app_path: str):
        self.app_path = Path(app_path)
        self.app_type = self.detect_app_type()

    def detect_app_type(self) -> str:
        """
        アプリケーションの種類を自動検出
        """
        # Node.js/npm
        if (self.app_path / "package.json").exists():
            package_json = json.loads((self.app_path / "package.json").read_text())

            # React/Next.js/Vue
            deps = package_json.get("dependencies", {})
            dev_deps = package_json.get("devDependencies", {})
            all_deps = {**deps, **dev_deps}

            if "react" in all_deps or "react-dom" in all_deps:
                return "react"
            elif "next" in all_deps:
                return "nextjs"
            elif "vue" in all_deps:
                return "vue"
            else:
                return "nodejs"

        # Python
        elif (self.app_path / "requirements.txt").exists() or (self.app_path / "app.py").exists():
            # Flask/FastAPI検出
            if (self.app_path / "requirements.txt").exists():
                requirements = (self.app_path / "requirements.txt").read_text()
                if "flask" in requirements.lower():
                    return "flask"
                elif "fastapi" in requirements.lower():
                    return "fastapi"
            return "python"

        # 静的サイト
        elif (self.app_path / "index.html").exists():
            return "static"

        return "unknown"

    def generate_launcher(self, output_path: Optional[str] = None) -> str:
        """
        起動スクリプトを生成
        """
        if output_path is None:
            output_path = self.app_path / "launch_app.command"

        script_content = self.get_launcher_template()

        # スクリプトを保存
        output_file = Path(output_path)
        output_file.write_text(script_content)
        output_file.chmod(0o755)  # 実行権限を付与

        return str(output_file)

    def get_launcher_template(self) -> str:
        """
        アプリタイプに応じた起動スクリプトテンプレートを返す
        """
        base_template = '''#!/bin/bash
# Auto-generated launcher script
# App Type: {app_type}

set -e

# カラー定義
GREEN='\\033[0;32m'
YELLOW='\\033[1;33m'
BLUE='\\033[0;34m'
RED='\\033[0;31m'
NC='\\033[0m'

# スクリプトのディレクトリに移動
cd "$(dirname "$0")"

echo -e "${{BLUE}}🚀 アプリケーション起動中...${{NC}}"
echo ""

# ポート検出関数
find_free_port() {{
    local start_port=${{1:-3000}}
    local end_port=${{2:-9999}}

    for port in $(seq $start_port $end_port); do
        if ! lsof -i:$port >/dev/null 2>&1; then
            echo $port
            return 0
        fi
    done

    echo -e "${{RED}}❌ 空きポートが見つかりません${{NC}}"
    exit 1
}}

# クリーンアップ処理
cleanup() {{
    echo ""
    echo -e "${{YELLOW}}🔄 クリーンアップ中...${{NC}}"

    # 子プロセスを終了
    if [ ! -z "$APP_PID" ]; then
        kill $APP_PID 2>/dev/null || true
    fi

    echo -e "${{GREEN}}✅ 終了しました${{NC}}"
}}

# 終了時のクリーンアップを設定
trap cleanup EXIT

'''

        # アプリタイプごとの起動コマンド
        if self.app_type in ["react", "vue", "nodejs"]:
            specific_part = '''# Node.js依存関係のインストール
if [ ! -d "node_modules" ]; then
    echo -e "${YELLOW}📦 依存関係をインストール中...${NC}"
    npm install
fi

# 空きポートを検出
PORT=$(find_free_port 3000)
export PORT

echo -e "${GREEN}✅ ポート $PORT を使用します${NC}"

# アプリケーション起動
echo -e "${BLUE}🌐 アプリケーションを起動中...${NC}"
npm start &
APP_PID=$!

# ブラウザを開く
sleep 3
echo -e "${GREEN}🌐 ブラウザを開いています...${NC}"
open "http://localhost:$PORT"

# プロセスを待機
echo ""
echo -e "${YELLOW}終了するには Ctrl+C を押してください${NC}"
wait $APP_PID
'''

        elif self.app_type == "flask":
            specific_part = '''# Python依存関係のインストール
if [ -f "requirements.txt" ]; then
    echo -e "${YELLOW}📦 依存関係をインストール中...${NC}"
    pip install -r requirements.txt
fi

# 空きポートを検出
PORT=$(find_free_port 5000)

echo -e "${GREEN}✅ ポート $PORT を使用します${NC}"

# Flask アプリケーション起動
echo -e "${BLUE}🌐 Flask アプリケーションを起動中...${NC}"
export FLASK_APP=app.py
export FLASK_ENV=development
flask run --port=$PORT &
APP_PID=$!

# ブラウザを開く
sleep 3
echo -e "${GREEN}🌐 ブラウザを開いています...${NC}"
open "http://localhost:$PORT"

# プロセスを待機
echo ""
echo -e "${YELLOW}終了するには Ctrl+C を押してください${NC}"
wait $APP_PID
'''

        elif self.app_type == "fastapi":
            specific_part = '''# Python依存関係のインストール
if [ -f "requirements.txt" ]; then
    echo -e "${YELLOW}📦 依存関係をインストール中...${NC}"
    pip install -r requirements.txt
fi

# 空きポートを検出
PORT=$(find_free_port 8000)

echo -e "${GREEN}✅ ポート $PORT を使用します${NC}"

# FastAPI アプリケーション起動
echo -e "${BLUE}🌐 FastAPI アプリケーションを起動中...${NC}"
uvicorn app:app --reload --port $PORT &
APP_PID=$!

# ブラウザを開く
sleep 3
echo -e "${GREEN}🌐 ブラウザを開いています...${NC}"
open "http://localhost:$PORT"

# プロセスを待機
echo ""
echo -e "${YELLOW}終了するには Ctrl+C を押してください${NC}"
wait $APP_PID
'''

        elif self.app_type == "static":
            specific_part = '''# 空きポートを検出
PORT=$(find_free_port 8000)

echo -e "${GREEN}✅ ポート $PORT を使用します${NC}"

# 静的サーバー起動
echo -e "${BLUE}🌐 静的サーバーを起動中...${NC}"
python3 -m http.server $PORT &
APP_PID=$!

# ブラウザを開く
sleep 2
echo -e "${GREEN}🌐 ブラウザを開いています...${NC}"
open "http://localhost:$PORT"

# プロセスを待機
echo ""
echo -e "${YELLOW}終了するには Ctrl+C を押してください${NC}"
wait $APP_PID
'''

        else:
            specific_part = '''echo -e "${RED}❌ アプリケーションタイプを検出できませんでした${NC}"
echo "手動で起動してください"
exit 1
'''

        return base_template.format(app_type=self.app_type) + specific_part


def main():
    """
    コマンドライン実行用
    """
    import argparse

    parser = argparse.ArgumentParser(description='起動スクリプト自動生成')
    parser.add_argument('app_path', help='アプリケーションのパス')
    parser.add_argument('--output', '-o', help='出力先パス', default=None)

    args = parser.parse_args()

    generator = LauncherGenerator(args.app_path)
    output_file = generator.generate_launcher(args.output)

    print(f"✅ 起動スクリプトを生成しました: {output_file}")
    print(f"   アプリタイプ: {generator.app_type}")
    print(f"\n実行方法:")
    print(f"   1. Finderでダブルクリック")
    print(f"   2. または: {output_file}")


if __name__ == "__main__":
    main()