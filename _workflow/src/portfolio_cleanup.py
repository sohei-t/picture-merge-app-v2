#!/usr/bin/env python3
"""
GitHubポートフォリオ クリーンアップスクリプト
既存のリポジトリから不要なファイルを除去
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path
from typing import List, Set

class PortfolioCleanup:
    """ポートフォリオクリーンアップクラス"""

    def __init__(self, portfolio_repo: str = None):
        """
        Args:
            portfolio_repo: ポートフォリオリポジトリのパス
        """
        self.portfolio_repo = portfolio_repo or os.path.expanduser("~/Desktop/GitHub/ai-agent-portfolio")

        # 削除すべきファイル/ディレクトリのパターン
        self.remove_patterns = {
            # ディレクトリ
            '__pycache__',
            'node_modules',
            '.git',
            'venv',
            'env',
            '.vscode',
            '.idea',

            # エージェント関連ファイル（完全一致）
            'claude_agent_executor.py',
            'workflow_orchestrator.py',
            'launcher_generator.py',
            'portfolio_publisher.py',
            'requirements_gatherer.py',
            'documentation_generator.py',
            'improvement_loop_controller.py',
            'progress_reporter.py',
            'tts_generator.py',
            'tts_smart_generator.py',
            'pdf_converter.js',
            'client_document_generator.py',
            'enhanced_client_document_generator.py',
            'portfolio_doc_generator.py',
            'error_handler.sh',

            # ビルドファイル
            '*.pyc',
            '*.pyo',
            '*.pyd',
            '.DS_Store',
            'Thumbs.db',

            # 環境ファイル
            '.env',
            '.env.local',
            '*.env'
        }

    def scan_directory(self, path: Path) -> List[Path]:
        """ディレクトリをスキャンして削除対象を検出"""
        to_remove = []

        for item in path.rglob('*'):
            # ファイル名取得
            name = item.name

            # 完全一致チェック
            if name in self.remove_patterns:
                to_remove.append(item)
                continue

            # パターンマッチチェック
            for pattern in self.remove_patterns:
                if '*' in pattern:
                    # ワイルドカードパターン
                    import fnmatch
                    if fnmatch.fnmatch(name, pattern):
                        to_remove.append(item)
                        break
                elif pattern in name.lower():
                    # 部分一致（エージェント関連）
                    if 'agent' in pattern or 'orchestrator' in pattern:
                        to_remove.append(item)
                        break

        return to_remove

    def cleanup_app(self, app_name: str, dry_run: bool = True):
        """特定アプリをクリーンアップ"""
        app_path = Path(self.portfolio_repo) / 'apps' / app_name

        if not app_path.exists():
            print(f"❌ アプリが見つかりません: {app_name}")
            return

        print(f"\n🧹 {app_name} のクリーンアップ開始...")
        print(f"📁 パス: {app_path}")

        # 削除対象をスキャン
        to_remove = self.scan_directory(app_path)

        if not to_remove:
            print("✅ クリーンアップ不要（削除対象なし）")
            return

        # 削除対象を表示
        print(f"\n📝 削除対象（{len(to_remove)}件）:")
        for item in sorted(to_remove):
            rel_path = item.relative_to(app_path)
            if item.is_dir():
                print(f"  📁 {rel_path}/")
            else:
                print(f"  📄 {rel_path}")

        if dry_run:
            print("\n⚠️ ドライランモード - 実際には削除されません")
            print("実行するには --execute オプションを追加してください")
        else:
            # 実際に削除
            confirm = input("\n本当に削除しますか? (yes/no): ")
            if confirm.lower() == 'yes':
                for item in to_remove:
                    try:
                        if item.is_dir():
                            shutil.rmtree(item)
                            print(f"  ✅ 削除: {item.name}/")
                        else:
                            item.unlink()
                            print(f"  ✅ 削除: {item.name}")
                    except Exception as e:
                        print(f"  ❌ 削除失敗: {item.name} - {e}")

                print("\n✅ クリーンアップ完了")
            else:
                print("❌ キャンセルしました")

    def cleanup_all(self, dry_run: bool = True):
        """全アプリをクリーンアップ"""
        apps_dir = Path(self.portfolio_repo) / 'apps'

        if not apps_dir.exists():
            print("❌ appsディレクトリが見つかりません")
            return

        # 全アプリをリスト
        apps = [d.name for d in apps_dir.iterdir() if d.is_dir()]

        if not apps:
            print("ℹ️ アプリが見つかりません")
            return

        print(f"\n📱 {len(apps)}個のアプリが見つかりました:")
        for app in apps:
            print(f"  - {app}")

        print("\n" + "="*50)

        # 各アプリをクリーンアップ
        for app in apps:
            self.cleanup_app(app, dry_run)
            print("\n" + "="*50)

    def generate_gitignore(self):
        """適切な.gitignoreファイルを生成"""
        gitignore_content = """# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
ENV/
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Node.js
node_modules/
npm-debug.log*
yarn-debug.log*
yarn-error.log*
.pnpm-debug.log*

# Environment files
.env
.env.local
.env.production.local
.env.development.local
.env.test.local
*.env

# IDE
.vscode/
.idea/
*.swp
*.swo
*~
.DS_Store
Thumbs.db

# Logs
logs/
*.log

# Testing
coverage/
.coverage
htmlcov/
.pytest_cache/
.tox/

# Build outputs
dist/
build/
*.min.js
*.min.css

# Agent/Development files (SHOULD NOT BE IN PORTFOLIO)
*agent*.py
*orchestrator*.py
*launcher_generator*.py
*portfolio_publisher*.py
*requirements_gatherer*.py
*documentation_generator*.py
*improvement_loop*.py
*progress_reporter*.py
*tts_generator*.py
*pdf_converter*.py
*client_document*.py
error_handler.sh
workflow_*.py
claude_*.py

# Temporary files
*.tmp
*.temp
.cache/
"""

        gitignore_path = Path(self.portfolio_repo) / '.gitignore'
        with open(gitignore_path, 'w') as f:
            f.write(gitignore_content)

        print(f"✅ .gitignore を生成しました: {gitignore_path}")

def main():
    """コマンドライン実行用"""
    import argparse

    parser = argparse.ArgumentParser(description='GitHubポートフォリオのクリーンアップ')
    parser.add_argument('app_name', nargs='?', help='クリーンアップするアプリ名（省略時は全アプリ）')
    parser.add_argument('--execute', action='store_true', help='実際に削除を実行')
    parser.add_argument('--repo', help='ポートフォリオリポジトリのパス')
    parser.add_argument('--gitignore', action='store_true', help='.gitignoreを生成')

    args = parser.parse_args()

    cleaner = PortfolioCleanup(args.repo)

    if args.gitignore:
        cleaner.generate_gitignore()
        return

    dry_run = not args.execute

    if args.app_name:
        cleaner.cleanup_app(args.app_name, dry_run)
    else:
        cleaner.cleanup_all(dry_run)


if __name__ == "__main__":
    main()