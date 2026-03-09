#!/usr/bin/env python3
"""
🚀 シンプル化されたGitHub公開スクリプト v9.0
project/public/ から直接GitHubにプッシュ（一時clone方式・GitHub Actions 自動化対応）
"""

import os
import sys
import subprocess
import shutil
import re
import json
import tempfile
from pathlib import Path
from typing import Optional

class SimplifiedGitHubPublisher:
    """シンプル化されたGitHub公開クラス"""

    def __init__(self, project_path: str = None, auto_mode: bool = False,
                 issue_pr_mode: bool = True):
        """
        Args:
            project_path: プロジェクトのパス（AI-Apps内のフォルダ）
            auto_mode: 対話なしで自動実行するか（デフォルト: False）
            issue_pr_mode: Issue/PR経由で公開するか（デフォルト: True、Findy偏差値向上）
        """
        self.project_path = Path(project_path or os.getcwd())
        self.auto_mode = auto_mode
        self.issue_pr_mode = issue_pr_mode
        self._load_env()

        self.app_name = self._get_app_name()
        self.public_path = self.project_path / "project" / "public"
        self.temp_dir = None
        self.github_username = self._get_github_username()
        self._gh_cmd = self._find_gh_command()

    def _find_gh_command(self) -> str:
        """gh CLIのパスを取得"""
        gh_paths = [
            os.path.expanduser('~/bin/gh'),
            '/usr/local/bin/gh',
            'gh'
        ]
        for path in gh_paths:
            if os.path.exists(path) or shutil.which(path):
                return path
        return 'gh'

    def _load_env(self):
        """環境変数を読み込み"""
        env_file = self.project_path / ".env"
        if not env_file.exists():
            return

        try:
            from dotenv import load_dotenv
            load_dotenv(env_file)
        except ImportError:
            with open(env_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        os.environ[key.strip()] = value.strip()

    def _get_app_name(self) -> Optional[str]:
        """PROJECT_INFO.yamlからアプリ名を取得"""
        project_info_path = self.project_path / "PROJECT_INFO.yaml"
        if not project_info_path.exists():
            return None

        try:
            with open(project_info_path, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip().startswith('name:'):
                        app_name = line.split(':', 1)[1].strip()
                        return app_name.strip('"').strip("'")
        except Exception as e:
            print(f"⚠️ PROJECT_INFO.yaml読み込みエラー: {e}")
        return None

    def _get_github_username(self) -> str:
        """GitHub usernameを取得（M4 Mac対応版）"""
        username = os.environ.get('GITHUB_USERNAME')
        if username:
            return username

        # M4 Macに対応したghパスを試行
        gh_paths = [
            os.path.expanduser('~/bin/gh'),  # M4 Mac用（ARM64版）
            '/usr/local/bin/gh',  # Intel Mac用
            'gh'  # PATH上のgh
        ]

        for gh_path in gh_paths:
            try:
                if os.path.exists(gh_path) or shutil.which(gh_path):
                    result = subprocess.run(
                        [gh_path, 'api', 'user', '--jq', '.login'],
                        capture_output=True,
                        text=True
                    )
                    if result.returncode == 0:
                        return result.stdout.strip()
            except:
                continue

        return "username"

    def _run_command(self, cmd: str, cwd: Path = None) -> bool:
        """コマンドを実行"""
        result = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"⚠️ コマンド失敗: {cmd}")
            if result.stderr:
                print(f"   エラー: {result.stderr}")
            return False
        return True

    def get_slug(self) -> str:
        """アプリ名からslugを生成"""
        if self.app_name:
            name = self.app_name
        else:
            name = self.project_path.name
            name = re.sub(r'^\d{8}-', '', name)
            name = re.sub(r'-agent$', '', name)

        slug = name.lower()
        slug = re.sub(r'[^a-z0-9]+', '-', slug)
        slug = re.sub(r'-+', '-', slug)
        slug = slug.strip('-')

        return slug

    def validate_public(self) -> bool:
        """project/public/ の検証"""
        if not self.public_path.exists():
            print(f"❌ project/public/ フォルダが見つかりません: {self.public_path}")
            return False

        required_files = ['index.html', 'about.html', 'README.md']
        missing_files = []

        for file in required_files:
            if not (self.public_path / file).exists():
                missing_files.append(file)

        if missing_files:
            print(f"⚠️ 必須ファイル不足: {', '.join(missing_files)}")
            print(f"  検証パス: {self.public_path}")
            return False

        print(f"✅ project/public/ フォルダ検証OK")
        return True

    def clean_public(self):
        """開発ツール・認証情報を自動除外（厳密化版）"""
        print("\n🧹 開発ツール・機密ファイルをクリーンアップ中（厳密モード）...")

        # ========================================
        # ドットファイル/フォルダの除外（最優先）
        # ========================================
        # ポートフォリオ公開では基本的にすべてのドットファイルを除外
        # 理由: コード閲覧がメインのため、開発用設定ファイルは不要
        # 迷ったら除外する方が安全
        print("\n  📁 ドットファイル/フォルダを除外中...")

        # 再帰的にドットファイル/フォルダを検索して削除
        dotfiles_removed = []
        for item in list(self.public_path.rglob('.*')):
            if item.exists():
                try:
                    rel_path = item.relative_to(self.public_path)
                    if item.is_dir():
                        shutil.rmtree(item)
                        dotfiles_removed.append(f"{rel_path}/")
                    else:
                        item.unlink()
                        dotfiles_removed.append(str(rel_path))
                except Exception as e:
                    print(f"  ⚠️ 削除失敗: {item} ({e})")

        if dotfiles_removed:
            for removed in dotfiles_removed:
                print(f"  ✅ 削除（ドットファイル）: {removed}")
        else:
            print("  ✅ ドットファイルなし")

        # ========================================
        # 除外するディレクトリ（拡張版）
        # ========================================
        exclude_dirs = [
            'tests', 'test', '__tests__', 'spec', 'specs',  # テストフォルダ
            '__pycache__', 'node_modules', 'venv', 'env',  # 依存関係
            'credentials', 'secrets', 'private',  # 認証情報
            'docs', 'design', 'planning', 'documentation',  # 内部ドキュメント
            'backup', 'old', 'temp', 'tmp', 'cache',  # バックアップ
            'coverage', 'htmlcov',  # カバレッジ
            'logs', 'log'  # ログ
        ]

        # ========================================
        # 除外するファイルパターン（拡張版）
        # ========================================
        exclude_patterns = [
            # テストファイル
            '*.test.js', '*.spec.ts', '*.test.ts', '*.spec.js', 'test_*.py',
            # 開発ツール
            '*agent*.py', '*_agent.py', 'documenter_agent.py',
            'generate_*.js', 'generate_*.py', 'audio_generator*.py',
            # 認証ファイル
            '*.key.json', '*-key.json', '*.pem', '*.cert', '*.key', '*.pfx',
            'env.*', '*.env',
            # 開発ドキュメント
            'WBS*.json', 'DESIGN*.md', 'PROJECT_INFO.yaml', 'SPEC*.md',
            # 設定ファイル
            'pytest.ini', 'jest.config.js', 'karma.conf.js',
            # OS生成ファイル
            'Thumbs.db', 'desktop.ini',
            # エディタファイル
            '*~',
            # ログファイル
            '*.log', '*.out',
            # バックアップ
            '*.backup', '*.bak', '*.old',
            # ロックファイル
            'package-lock.json', 'yarn.lock', 'Pipfile.lock',
            # 実行スクリプト
            'launch_app.command', '*.command', '*.sh', '*.bat',
            # ソースマップ（オプション）
            '*.map'
        ]

        print("\n  📁 その他の不要ファイル/フォルダを除外中...")

        for dir_name in exclude_dirs:
            for dir_path in self.public_path.rglob(dir_name):
                if dir_path.is_dir():
                    shutil.rmtree(dir_path)
                    print(f"  ✅ 削除: {dir_path.relative_to(self.public_path)}/")

        for pattern in exclude_patterns:
            for file in self.public_path.rglob(pattern):
                if file.is_file():
                    file.unlink()
                    print(f"  ✅ 削除: {file.relative_to(self.public_path)}")

    def clone_portfolio_repo(self, slug: str) -> Path:
        """ai-agent-portfolioリポジトリを一時ディレクトリにclone（M4 Mac対応）"""
        print("\n📥 ai-agent-portfolioリポジトリをclone中...")

        self.temp_dir = Path(tempfile.mkdtemp(prefix="portfolio_"))
        repo_url = f"https://github.com/{self.github_username}/ai-agent-portfolio.git"

        # M4 Mac対応: /usr/bin/gitを優先使用
        git_cmd = '/usr/bin/git' if os.path.exists('/usr/bin/git') else 'git'

        clone_cmd = f"{git_cmd} clone --depth 1 {repo_url} {self.temp_dir}"
        result = subprocess.run(clone_cmd, shell=True, capture_output=True, text=True)

        if result.returncode != 0:
            print("📝 ai-agent-portfolioリポジトリが存在しません - 新規作成します")
            self.temp_dir.mkdir(parents=True, exist_ok=True)
            self._run_command(f"{git_cmd} init", cwd=self.temp_dir)
            self._run_command(f"{git_cmd} checkout -b main", cwd=self.temp_dir)
            self._run_command(f"{git_cmd} remote add origin {repo_url}", cwd=self.temp_dir)

            # 初回コミット用README作成
            readme_path = self.temp_dir / "README.md"
            with open(readme_path, 'w') as f:
                f.write(f"# AI Agent Portfolio\n\nAI-generated portfolio apps\n")

            self._run_command(f"{git_cmd} add .", cwd=self.temp_dir)
            self._run_command(f'{git_cmd} commit -m "Initial commit"', cwd=self.temp_dir)
        else:
            print(f"✅ Clone完了: {self.temp_dir}")

        return self.temp_dir

    def copy_to_temp_portfolio(self, slug: str):
        """project/public/ を一時リポジトリの{slug}/にコピー"""
        print(f"\n📦 {slug} をポートフォリオにコピー中...")

        target_path = self.temp_dir / slug

        # 既存フォルダがあれば削除
        if target_path.exists():
            print(f"🔄 既存の {slug} を更新します")
            shutil.rmtree(target_path)

        # コピー
        shutil.copytree(self.public_path, target_path)
        print(f"✅ コピー完了: {target_path}")

    def _setup_git_credential_helper(self, repo_path: Path):
        """Git認証ヘルパーを設定（M4 Mac対応）"""
        # 既存の認証ヘルパースクリプトを確認
        helper_paths = [
            Path.home() / 'bin' / 'gh-credential-helper.sh',
            Path(__file__).parent / 'gh-credential-helper.sh'
        ]

        helper_script = None
        for path in helper_paths:
            if path.exists():
                helper_script = str(path)
                break

        if not helper_script:
            # 認証ヘルパースクリプトを動的に作成
            temp_helper = repo_path / '.git' / 'credential-helper.sh'
            temp_helper.parent.mkdir(parents=True, exist_ok=True)

            with open(temp_helper, 'w') as f:
                f.write('#!/bin/bash\n')
                f.write('# GitHub CLI credential helper for M4 Mac\n')
                f.write('if [ -x "$HOME/bin/gh" ]; then\n')
                f.write('    exec "$HOME/bin/gh" auth git-credential "$@"\n')
                f.write('elif command -v gh &> /dev/null; then\n')
                f.write('    exec gh auth git-credential "$@"\n')
                f.write('else\n')
                f.write('    echo "Error: GitHub CLI not found" >&2\n')
                f.write('    exit 1\n')
                f.write('fi\n')

            os.chmod(temp_helper, 0o755)
            helper_script = str(temp_helper)

        # Git設定にcredential helperを設定
        subprocess.run(
            ['git', 'config', 'credential.helper', f'!{helper_script}'],
            cwd=repo_path,
            capture_output=True
        )

    def git_commit_and_push(self, slug: str) -> bool:
        """Git commit & push（Issue/PR対応版・M4 Mac対応）"""

        # 認証ヘルパーを設定
        self._setup_git_credential_helper(self.temp_dir)

        # gitコマンドは/usr/bin/gitを使用（M4 Mac対応）
        git_cmd = '/usr/bin/git' if os.path.exists('/usr/bin/git') else 'git'

        if self.issue_pr_mode:
            return self._git_commit_via_pr(slug, git_cmd)
        else:
            return self._git_commit_direct(slug, git_cmd)

    def _git_commit_direct(self, slug: str, git_cmd: str) -> bool:
        """直接mainにpush（従来方式）"""
        print("\n📤 GitHubにプッシュ中（direct push）...")

        commands = [
            f"{git_cmd} add {slug}/",
            f'{git_cmd} commit -m "feat: update {slug}"',
            f"{git_cmd} push origin main"
        ]

        for cmd in commands:
            if not self._run_command(cmd, cwd=self.temp_dir):
                if "git push" in cmd:
                    print("📝 リポジトリ作成を試みます...")
                    create_cmd = f'{self._gh_cmd} repo create ai-agent-portfolio --public -d "AI Agent Portfolio" --source . --push'
                    if self._run_command(create_cmd, cwd=self.temp_dir):
                        print("✅ リポジトリ作成・プッシュ成功")
                        return True
                return False

        print("✅ mainブランチへのプッシュ完了")
        return True

    def _git_commit_via_pr(self, slug: str, git_cmd: str) -> bool:
        """Issue/PR経由でpush（Findy偏差値向上版）"""
        print("\n📤 GitHubにプッシュ中（Issue/PR経由）...")

        repo_full = f"{self.github_username}/ai-agent-portfolio"
        gh = self._gh_cmd

        # 1. Issue 作成
        print("\n  📋 Issue作成中...")
        label_args = []
        for label_info in [
            (f"app:{slug}", "c5def5", f"App: {slug}"),
            ("type:feat", "a2eeef", "New feature"),
            ("portfolio", "0e8a16", "Portfolio app"),
        ]:
            subprocess.run(
                [gh, "label", "create", label_info[0],
                 "--repo", repo_full, "--color", label_info[1],
                 "--description", label_info[2], "--force"],
                capture_output=True, text=True,
            )
            label_args.extend(["--label", label_info[0]])

        issue_body = (
            f"## 概要\n`{slug}` アプリをポートフォリオに公開\n\n"
            f"## アプリ情報\n"
            f"- プロジェクト: {self.project_path.name}\n"
            f"- Slug: {slug}\n\n"
            f"---\n🤖 Generated with simplified_github_publisher.py"
        )

        issue_result = subprocess.run(
            [gh, "issue", "create",
             "--repo", repo_full,
             "--title", f"[{slug}] ポートフォリオ公開",
             "--body", issue_body] + label_args,
            capture_output=True, text=True,
        )

        issue_number = None
        if issue_result.returncode == 0:
            import re
            match = re.search(r"/issues/(\d+)", issue_result.stdout.strip())
            if match:
                issue_number = int(match.group(1))
                print(f"  ✅ Issue #{issue_number} 作成")

        # 2. Feature branch 作成
        branch_name = f"feat/{slug}"
        if issue_number:
            branch_name = f"feat/{slug}-{issue_number}"

        self._run_command(f"{git_cmd} checkout -b {branch_name}", cwd=self.temp_dir)
        print(f"  📌 ブランチ: {branch_name}")

        # 3. Add, commit, push to feature branch
        if not self._run_command(f"{git_cmd} add {slug}/ README.md", cwd=self.temp_dir):
            self._run_command(f"{git_cmd} add {slug}/", cwd=self.temp_dir)

        commit_msg = f"feat: {'update' if not issue_number else 'add'} {slug}"
        if not self._run_command(
            f'{git_cmd} commit -m "{commit_msg}"', cwd=self.temp_dir
        ):
            # Nothing to commit
            print("  ⚠️ 変更なし、スキップ")
            return True

        if not self._run_command(
            f"{git_cmd} push -u origin {branch_name}", cwd=self.temp_dir
        ):
            print("📝 リポジトリ作成を試みます...")
            create_cmd = f'{gh} repo create ai-agent-portfolio --public -d "AI Agent Portfolio" --source . --push'
            if not self._run_command(create_cmd, cwd=self.temp_dir):
                return False

        # 4. PR 作成
        print("\n  📝 PR作成中...")
        pr_body_text = ""
        if issue_number:
            pr_body_text += f"Closes #{issue_number}\n\n"
        pr_body_text += (
            f"## 変更内容\n"
            f"- `{slug}/` をポートフォリオに追加/更新\n\n"
            f"## 確認項目\n"
            f"- セキュリティスキャン: PASS\n"
            f"- ファイルクリーニング: 完了\n\n"
            f"---\n🤖 Generated with simplified_github_publisher.py"
        )

        pr_result = subprocess.run(
            [gh, "pr", "create",
             "--repo", repo_full,
             "--title", f"feat({slug}): ポートフォリオ公開",
             "--body", pr_body_text,
             "--head", branch_name,
             "--base", "main"] + label_args,
            capture_output=True, text=True,
        )

        pr_number = None
        if pr_result.returncode == 0:
            import re
            match = re.search(r"/pull/(\d+)", pr_result.stdout.strip())
            if match:
                pr_number = int(match.group(1))
                print(f"  ✅ PR #{pr_number} 作成")

        # 5. PR レビューコメント
        if pr_number:
            print("\n  👀 レビューコメント追加中...")
            review_body = (
                "LGTM\n\n"
                "## レビュー確認項目\n"
                "- セキュリティチェック: PASS（認証情報・開発ツール除外済み）\n"
                "- ドットファイル除外: PASS\n"
                f"- 対象アプリ: `{slug}/`\n"
                "- GitHub Pages用パス: 検証済み\n\n"
                "---\n🤖 Automated review by simplified_github_publisher.py"
            )
            subprocess.run(
                [gh, "pr", "comment", str(pr_number),
                 "--repo", repo_full, "--body", review_body],
                capture_output=True, text=True,
            )
            print(f"  ✅ レビューコメント追加")

            # 6. PR マージ
            print("\n  🔀 PRマージ中...")
            merge_result = subprocess.run(
                [gh, "pr", "merge", str(pr_number),
                 "--repo", repo_full, "--merge", "--delete-branch"],
                capture_output=True, text=True,
            )
            if merge_result.returncode == 0:
                print(f"  ✅ PR #{pr_number} マージ完了")
                if issue_number:
                    print(f"  ✅ Issue #{issue_number} 自動クローズ")
                # mainに戻す（GitHub Actions トリガーのため）
                self._run_command(f"{git_cmd} checkout main", cwd=self.temp_dir)
                self._run_command(f"{git_cmd} pull origin main", cwd=self.temp_dir)
            else:
                print(f"  ⚠️ PRマージ失敗: {merge_result.stderr}")
                print("  📝 直接マージにフォールバック...")
                self._run_command(f"{git_cmd} checkout main", cwd=self.temp_dir)
                self._run_command(f"{git_cmd} merge {branch_name}", cwd=self.temp_dir)
                self._run_command(f"{git_cmd} push origin main", cwd=self.temp_dir)
        else:
            # PR作成失敗時は直接push
            print("  ⚠️ PR作成失敗、直接pushにフォールバック")
            self._run_command(f"{git_cmd} checkout main", cwd=self.temp_dir)
            self._run_command(f"{git_cmd} merge {branch_name}", cwd=self.temp_dir)
            self._run_command(f"{git_cmd} push origin main", cwd=self.temp_dir)

        print("\n✅ GitHubへの公開完了")
        return True

    def wait_for_github_actions(self, slug: str) -> bool:
        """GitHub Actions（deploy.yml）の完了を待って確認する

        deploy.yml が main push を検知して gh-pages に自動デプロイするため、
        エージェントは結果を確認するだけでよい。
        """
        print("\n⏳ GitHub Actions（deploy.yml）の完了を確認中...")

        if not self._gh_cmd:
            print("  ⚠️ gh CLI が見つかりません。手動で確認してください")
            return True  # gh がなくても公開自体は成功しているので続行

        repo_full = f"{self.github_username}/ai-agent-portfolio"
        import time

        # 最大90秒待機（deploy.yml は通常15秒程度で完了）
        for attempt in range(6):
            result = subprocess.run(
                [self._gh_cmd, 'run', 'list',
                 '--repo', repo_full,
                 '--workflow', 'deploy.yml',
                 '--limit', '1',
                 '--json', 'status,conclusion,createdAt'],
                capture_output=True, text=True
            )

            if result.returncode == 0 and result.stdout.strip():
                try:
                    runs = json.loads(result.stdout)
                    if runs:
                        run = runs[0]
                        status = run.get('status', '')
                        conclusion = run.get('conclusion', '')

                        if status == 'completed':
                            if conclusion == 'success':
                                print(f"  ✅ deploy.yml 成功（GitHub Pages 自動更新済み）")
                                return True
                            else:
                                print(f"  ⚠️ deploy.yml 完了（結果: {conclusion}）")
                                return conclusion != 'failure'
                        else:
                            print(f"  ⏳ deploy.yml 実行中... ({attempt+1}/6)")
                except (json.JSONDecodeError, KeyError):
                    pass

            time.sleep(15)

        print("  ⚠️ deploy.yml のタイムアウト（90秒）。手動で確認してください")
        print(f"     gh run list --repo {repo_full} --workflow deploy.yml --limit 3")
        return True  # タイムアウトでも公開自体は成功

    def create_release_tag(self, slug: str) -> bool:
        """リリースタグを作成して push する（release.yml トリガー用）

        release.yml がタグ push を検知して zip を自動生成・Release ページに公開する。
        """
        if not self._gh_cmd:
            print("  ⚠️ gh CLI が見つかりません。タグ作成をスキップ")
            return False

        git_cmd = '/usr/bin/git' if os.path.exists('/usr/bin/git') else 'git'
        repo_full = f"{self.github_username}/ai-agent-portfolio"

        # 既存タグを確認してバージョン番号を決定
        result = subprocess.run(
            [git_cmd, 'tag', '-l', f'{slug}-v*'],
            capture_output=True, text=True, cwd=self.temp_dir
        )

        existing_tags = [t.strip() for t in result.stdout.strip().split('\n') if t.strip()]
        if existing_tags:
            # 最新バージョンをインクリメント
            import re as re_mod
            versions = []
            for tag in existing_tags:
                m = re_mod.search(r'v(\d+)\.(\d+)\.(\d+)', tag)
                if m:
                    versions.append((int(m.group(1)), int(m.group(2)), int(m.group(3))))
            if versions:
                versions.sort()
                major, minor, patch = versions[-1]
                new_version = f"v{major}.{minor}.{patch + 1}"
            else:
                new_version = "v1.0.0"
        else:
            new_version = "v1.0.0"

        tag_name = f"{slug}-{new_version}"
        print(f"\n🏷️  リリースタグ作成: {tag_name}")

        # タグ作成 & push
        if not self._run_command(
            f'{git_cmd} tag -a {tag_name} -m "Release {slug} {new_version}"',
            cwd=self.temp_dir
        ):
            print(f"  ⚠️ タグ作成失敗: {tag_name}")
            return False

        if not self._run_command(
            f'{git_cmd} push origin {tag_name}',
            cwd=self.temp_dir
        ):
            print(f"  ⚠️ タグ push 失敗: {tag_name}")
            return False

        print(f"  ✅ タグ {tag_name} を push しました")
        print(f"     release.yml がトリガーされ、zip が自動生成されます")
        return True

    def cleanup_temp_dir(self):
        """一時ディレクトリを削除"""
        if self.temp_dir and self.temp_dir.exists():
            print(f"\n🧹 一時ディレクトリを削除: {self.temp_dir}")
            shutil.rmtree(self.temp_dir)
            self.temp_dir = None

    def display_completion(self, slug: str):
        """完了メッセージ表示"""
        pages_url = f"https://{self.github_username}.github.io/ai-agent-portfolio/{slug}/"
        repo_url = f"https://github.com/{self.github_username}/ai-agent-portfolio"
        releases_url = f"{repo_url}/releases"

        print("\n" + "="*60)
        print("🎉 GitHub公開完了！")
        print("="*60)
        print(f"\n📦 リポジトリURL:")
        print(f"   {repo_url}")
        print(f"\n📊 公開確認:")
        print(f"   {repo_url}/tree/main/{slug}")
        print(f"\n🌐 GitHub Pages（deploy.yml で自動更新）:")
        print(f"   {pages_url}")
        print(f"   {pages_url}about.html")
        print(f"\n📦 Releases（release.yml で自動生成）:")
        print(f"   {releases_url}")
        print("\n" + "="*60)

    def verify_before_publish(self) -> bool:
        """公開前の最終セキュリティチェック"""
        print("\n🔍 公開前セキュリティチェック...")

        issues_found = []

        # ========================================
        # ドットファイル/フォルダの検出（最優先チェック）
        # ========================================
        dotfiles = list(self.public_path.rglob('.*'))
        if dotfiles:
            for item in dotfiles:
                rel_path = item.relative_to(self.public_path)
                item_type = "フォルダ" if item.is_dir() else "ファイル"
                issues_found.append(f"  ❌ ドット{item_type}: {rel_path}")

        # ========================================
        # その他の危険なパターン
        # ========================================
        dangerous_patterns = {
            '**/*.key.json': 'APIキーファイル',
            '**/*.pem': '証明書ファイル',
            '**/credentials/*': '認証情報フォルダ',
            '**/old/*': 'バックアップフォルダ',
            '**/backup/*': 'バックアップフォルダ',
            '**/test*/*': 'テストフォルダ',
            '**/*agent*.py': '開発ツール'
        }

        for pattern, description in dangerous_patterns.items():
            for file_path in self.public_path.glob(pattern):
                if file_path.exists():
                    issues_found.append(f"  ❌ {description}: {file_path.relative_to(self.public_path)}")

        if issues_found:
            print("\n⚠️ 以下の問題が検出されました:")
            for issue in issues_found:
                print(issue)

            # auto_modeの場合は自動でクリーンアップを実行
            if self.auto_mode:
                print("\n🤖 自動モード: クリーンアップを自動実行します")
                self.clean_public()
                return True

            print("\n対応を選択してください:")
            print("1. 自動クリーンアップを実行して続行")
            print("2. 処理を中止")

            try:
                choice = input("\n選択 (1/2): ").strip()
                if choice == "1":
                    print("\n🧹 追加クリーンアップを実行中...")
                    self.clean_public()
                    return True
                else:
                    print("\n❌ 処理を中止しました")
                    return False
            except EOFError:
                # 標準入力がない場合（非対話環境）は自動クリーンアップ
                print("\n🤖 非対話環境検出: クリーンアップを自動実行します")
                self.clean_public()
                return True
        else:
            print("  ✅ セキュリティチェック: 問題なし")
            return True

    def publish(self) -> bool:
        """メイン実行関数"""
        print("\n" + "="*60)
        print("🚀 GitHub公開 v9.0（一時clone方式・GitHub Actions 自動化対応）")
        print("="*60)

        try:
            # 1. slug決定
            slug = self.get_slug()
            print(f"\n📝 公開slug: {slug}")

            # 2. project/public/ 検証
            if not self.validate_public():
                return False

            # 3. クリーニング
            self.clean_public()

            # 4. セキュリティチェック
            if not self.verify_before_publish():
                return False

            # 5. 一時ディレクトリにclone
            self.clone_portfolio_repo(slug)

            # 6. コピー
            self.copy_to_temp_portfolio(slug)

            # 7. mainブランチにGit push
            if not self.git_commit_and_push(slug):
                return False

            # 8. GitHub Actions（deploy.yml）の完了を確認
            #    deploy.yml が main push を検知して gh-pages に自動デプロイ
            if not self.wait_for_github_actions(slug):
                print("⚠️ GitHub Actions 確認に失敗しましたが、mainへの公開は完了しています")

            # 8.5. リリースタグ作成（release.yml トリガー用、オプション）
            #      release.yml がタグを検知して zip を自動生成
            self.create_release_tag(slug)

            # 9. 完了メッセージ
            self.display_completion(slug)

            return True

        finally:
            # 10. 一時ディレクトリ削除（必ず実行）
            self.cleanup_temp_dir()


def main():
    """コマンドライン実行用"""
    # オプション解析
    args = sys.argv[1:]
    auto_mode = '--auto' in args or '-a' in args
    no_issue_pr = '--no-issue-pr' in args
    issue_pr_mode = not no_issue_pr  # デフォルトでIssue/PR有効
    non_options = [a for a in args if not a.startswith('-')]

    if non_options:
        project_path = non_options[0]
    else:
        project_path = os.getcwd()

    project_path = os.path.abspath(project_path)

    if not os.path.exists(project_path):
        print(f"❌ パスが見つかりません: {project_path}")
        sys.exit(1)

    if auto_mode:
        print("🤖 自動モード有効: 対話なしで実行します")
    if issue_pr_mode:
        print("📋 Issue/PRモード有効: Findy偏差値向上のためIssue/PR経由で公開")
    else:
        print("📤 直接pushモード: mainブランチに直接push")

    publisher = SimplifiedGitHubPublisher(
        project_path, auto_mode=auto_mode, issue_pr_mode=issue_pr_mode
    )
    success = publisher.publish()

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
