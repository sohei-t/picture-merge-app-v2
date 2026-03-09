#!/usr/bin/env python3
"""
GitHub Portfolio Publisher - Template/Example
DELIVERYフォルダを sohei-t/ai-agent-portfolio に公開
"""

import os
import sys
from pathlib import Path

def publish_to_portfolio(update=False):
    """
    DELIVERYフォルダをGitHubポートフォリオに公開

    Args:
        update: True の場合は更新、False の場合は新規
    """
    # プロジェクトルート取得
    project_root = Path.cwd()

    # スクリプトパス
    delivery_organizer = project_root / "src" / "delivery_organizer.py"
    github_publisher = project_root / "src" / "github_publisher_v8.py"

    # 1. DELIVERYフォルダ作成
    print("📦 DELIVERYフォルダ作成中...")
    os.system(f"python3 {delivery_organizer}")

    # 2. GitHub公開
    print("📤 GitHubに公開中...")
    update_flag = "--update" if update else ""
    os.system(f"python3 {github_publisher} {update_flag}")

    print("✅ 公開完了！")

def update_after_fix():
    """コード修正後の更新公開"""

    # 1. テスト実行
    print("🧪 テスト実行中...")
    if os.path.exists("package.json"):
        result = os.system("npm test")
    elif os.path.exists("test_app.py"):
        result = os.system("python3 -m pytest")
    else:
        print("⚠️ テストファイルが見つかりません")
        result = 0

    if result != 0:
        print("❌ テスト失敗。修正してください")
        return False

    # 2. 公開（更新モード）
    publish_to_portfolio(update=True)
    return True

def verify_delivery():
    """DELIVERYフォルダの検証"""
    delivery_path = Path.cwd() / "DELIVERY"

    if not delivery_path.exists():
        print("❌ DELIVERYフォルダが見つかりません")
        return False

    # 必須ファイルチェック
    required_files = ["index.html", "README.md", "about.html"]
    missing = []

    for file in required_files:
        if not (delivery_path / file).exists():
            missing.append(file)

    if missing:
        print(f"⚠️ 必須ファイルが不足: {', '.join(missing)}")
        return False

    print("✅ DELIVERY検証OK")
    return True

# 使用例
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="GitHub Portfolio Publisher")
    parser.add_argument("--update", action="store_true", help="更新モード")
    parser.add_argument("--verify", action="store_true", help="検証のみ")
    args = parser.parse_args()

    if args.verify:
        verify_delivery()
    elif args.update:
        update_after_fix()
    else:
        publish_to_portfolio(update=False)