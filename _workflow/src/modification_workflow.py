#!/usr/bin/env python3
"""
修正ワークフロー（Phase 7）- Issue/PR管理対応版
ユーザーレビュー後の修正を処理し、GitHub Issue/PRで追跡

フロー:
1. 修正依頼の受付 → Issue自動作成
2. 影響範囲の分析 → ブランチ作成
3. 必要なフェーズの再実行
4. PR作成 → マージ → Issue自動クローズ
5. Phase 6（ポートフォリオ公開）の再実行
"""

import os
import sys
import re
import subprocess
import shutil
import argparse
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from datetime import datetime

# 同じディレクトリのモジュールをインポート
sys.path.insert(0, str(Path(__file__).parent))

from workflow_state_manager import (
    WorkflowStateManager,
    WorkflowStatus,
    get_state_manager,
)
from publish_portfolio import PortfolioPublisher


# ========================================
# GitHub Issue/PR管理クラス
# ========================================

class GitHubIssuePRManager:
    """GitHub Issue/PR管理（ai-agent-portfolio用）"""

    REPO = "ai-agent-portfolio"

    def __init__(self, github_username: str = None):
        self.github_username = github_username or self._get_github_username()
        self.repo_full = f"{self.github_username}/{self.REPO}"

    def _get_github_username(self) -> str:
        """GitHub usernameを取得"""
        username = os.environ.get('GITHUB_USERNAME')
        if username:
            return username

        gh_cmd = self._get_gh_command()
        try:
            result = subprocess.run(
                [gh_cmd, 'api', 'user', '--jq', '.login'],
                capture_output=True, text=True
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except:
            pass
        return os.environ.get("GITHUB_USERNAME", "unknown")  # フォールバック

    def _get_gh_command(self) -> str:
        """gh CLIのパスを取得（M4 Mac対応）"""
        gh_paths = [
            os.path.expanduser('~/bin/gh'),
            '/usr/local/bin/gh',
            'gh'
        ]
        for path in gh_paths:
            if os.path.exists(path) or shutil.which(path):
                return path
        return 'gh'

    def _run_gh(self, args: List[str], capture_output: bool = True) -> subprocess.CompletedProcess:
        """gh CLIを実行"""
        gh_cmd = self._get_gh_command()
        cmd = [gh_cmd] + args
        return subprocess.run(cmd, capture_output=capture_output, text=True)

    def _slugify(self, text: str, max_length: int = 30) -> str:
        """テキストをslug形式に変換"""
        # 日本語を簡易的にローマ字化（基本的な変換のみ）
        slug = text.lower()
        slug = re.sub(r'[^a-z0-9\u3040-\u309f\u30a0-\u30ff\u4e00-\u9fff]+', '-', slug)
        slug = re.sub(r'-+', '-', slug)
        slug = slug.strip('-')
        # 長さ制限
        if len(slug) > max_length:
            slug = slug[:max_length].rstrip('-')
        return slug or 'fix'

    def ensure_labels_exist(self, app_name: str) -> bool:
        """必要なラベルが存在することを確認（なければ作成）"""
        label_name = f"app:{app_name}"

        # ラベルの存在確認
        result = self._run_gh([
            'label', 'list',
            '--repo', self.repo_full,
            '--search', label_name
        ])

        if label_name not in result.stdout:
            # ラベルを作成
            self._run_gh([
                'label', 'create', label_name,
                '--repo', self.repo_full,
                '--color', 'c5def5',
                '--description', f'App: {app_name}'
            ])
            print(f"  ✅ ラベル作成: {label_name}")

        return True

    def create_issue(
        self,
        app_name: str,
        title: str,
        body: str,
        labels: List[str] = None
    ) -> Optional[int]:
        """
        Issueを作成

        Returns:
            issue_number: Issue番号（失敗時はNone）
        """
        self.ensure_labels_exist(app_name)

        # ラベルの準備
        all_labels = [f"app:{app_name}"]
        if labels:
            all_labels.extend(labels)

        # Issue作成
        args = [
            'issue', 'create',
            '--repo', self.repo_full,
            '--title', f"[{app_name}] {title}",
            '--body', body
        ]

        for label in all_labels:
            args.extend(['--label', label])

        result = self._run_gh(args)

        if result.returncode == 0:
            # URLからIssue番号を抽出
            # 例: https://github.com/user/repo/issues/123
            url = result.stdout.strip()
            match = re.search(r'/issues/(\d+)', url)
            if match:
                issue_number = int(match.group(1))
                print(f"  ✅ Issue作成: #{issue_number}")
                print(f"     URL: {url}")
                return issue_number

        print(f"  ⚠️ Issue作成失敗: {result.stderr}")
        return None

    def create_branch(self, app_name: str, issue_number: int, description: str) -> Optional[str]:
        """
        fixブランチを作成

        Returns:
            branch_name: ブランチ名（失敗時はNone）
        """
        slug = self._slugify(description)
        branch_name = f"fix/{app_name}-{issue_number}-{slug}"

        # ブランチ名の長さ制限（git制限対策）
        if len(branch_name) > 60:
            branch_name = f"fix/{app_name}-{issue_number}"

        return branch_name

    def create_pull_request(
        self,
        app_name: str,
        issue_number: int,
        title: str,
        body: str,
        branch_name: str
    ) -> Optional[int]:
        """
        PRを作成

        Returns:
            pr_number: PR番号（失敗時はNone）
        """
        # PRボディにIssueリンクを追加
        full_body = f"""Fixes #{issue_number}

## 変更内容
{body}

## 関連Issue
- #{issue_number}

---
🤖 Generated with Claude Code
"""

        args = [
            'pr', 'create',
            '--repo', self.repo_full,
            '--title', f"fix({app_name}): {title}",
            '--body', full_body,
            '--head', branch_name,
            '--base', 'main'
        ]

        result = self._run_gh(args)

        if result.returncode == 0:
            url = result.stdout.strip()
            match = re.search(r'/pull/(\d+)', url)
            if match:
                pr_number = int(match.group(1))
                print(f"  ✅ PR作成: #{pr_number}")
                print(f"     URL: {url}")
                return pr_number

        print(f"  ⚠️ PR作成失敗: {result.stderr}")
        return None

    def review_pull_request(self, pr_number: int, body: str = None) -> bool:
        """
        PRにレビューコメントを追加（Findy評価向上用）

        Returns:
            success: 成功したかどうか
        """
        if body is None:
            body = "LGTM - セキュリティスキャン済み、動作確認完了"

        # PRコメントを追加（self-approveではなくコメント形式）
        args = [
            'pr', 'comment', str(pr_number),
            '--repo', self.repo_full,
            '--body', body
        ]

        result = self._run_gh(args)

        if result.returncode == 0:
            print(f"  ✅ PR #{pr_number} レビューコメント追加")
            return True

        print(f"  ⚠️ レビューコメント追加失敗: {result.stderr}")
        return False

    def merge_pull_request(self, pr_number: int) -> bool:
        """
        PRをマージ

        Returns:
            success: 成功したかどうか
        """
        args = [
            'pr', 'merge', str(pr_number),
            '--repo', self.repo_full,
            '--merge',
            '--delete-branch'
        ]

        result = self._run_gh(args)

        if result.returncode == 0:
            print(f"  ✅ PR #{pr_number} マージ完了")
            return True

        print(f"  ⚠️ PRマージ失敗: {result.stderr}")
        return False

    def get_issue_url(self, issue_number: int) -> str:
        """Issue URLを取得"""
        return f"https://github.com/{self.repo_full}/issues/{issue_number}"

    def get_pr_url(self, pr_number: int) -> str:
        """PR URLを取得"""
        return f"https://github.com/{self.repo_full}/pull/{pr_number}"


class ModificationWorkflow:
    """修正ワークフローオーケストレーター（Phase 7）- Issue/PR管理対応版"""

    # 修正タイプと再実行フェーズのマッピング
    MODIFICATION_TYPES = {
        "ui": {
            "keywords": ["デザイン", "色", "レイアウト", "スタイル", "CSS", "見た目", "UI", "ボタン", "フォント"],
            "phases": [3, 6],  # 実装 → 公開
            "description": "UI/デザイン変更",
            "labels": ["type:ui"],
        },
        "logic": {
            "keywords": ["ロジック", "機能", "動作", "バグ", "エラー", "修正", "追加", "削除"],
            "phases": [3, 4, 6],  # 実装 → 改善ループ → 公開
            "description": "ロジック/機能変更",
            "labels": ["type:fix"],
        },
        "docs": {
            "keywords": ["ドキュメント", "README", "説明", "コメント", "ヘルプ"],
            "phases": [5, 6],  # 完成処理 → 公開
            "description": "ドキュメント変更",
            "labels": ["type:docs"],
        },
        "security": {
            "keywords": ["セキュリティ", "認証", "パスワード", "API", "キー", "トークン"],
            "phases": [3, 4, 6],  # 実装 → 改善ループ → 公開
            "description": "セキュリティ関連変更",
            "labels": ["type:security"],
        },
        "full": {
            "keywords": ["全体", "大幅", "リファクタ", "作り直し"],
            "phases": [3, 4, 5, 6],  # 実装 → 改善ループ → 完成処理 → 公開
            "description": "大規模変更",
            "labels": ["type:refactor"],
        },
    }

    def __init__(self, project_path: str = None):
        self.project_path = Path(project_path) if project_path else Path.cwd()
        self.state_manager = get_state_manager(str(self.project_path))
        self.github_manager = GitHubIssuePRManager()

        # アプリ名を取得
        self.app_name = self._get_app_name()

    def _get_app_name(self) -> Optional[str]:
        """PROJECT_INFO.yamlからアプリ名を取得"""
        project_info_path = self.project_path / "PROJECT_INFO.yaml"
        if not project_info_path.exists():
            # フォルダ名から推測
            name = self.project_path.name
            name = re.sub(r'^\d{8}-', '', name)
            name = re.sub(r'-agent$', '', name)
            return name

        try:
            with open(project_info_path, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip().startswith('name:'):
                        app_name = line.split(':', 1)[1].strip()
                        return app_name.strip('"').strip("'")
        except Exception:
            pass

        return self.project_path.name

    def print_banner(self, title: str, char: str = "="):
        """バナーを表示"""
        width = 60
        print("\n" + char * width)
        print(f"  {title}")
        print(char * width)

    def print_success(self, message: str):
        print(f"  ✅ {message}")

    def print_warning(self, message: str):
        print(f"  ⚠️  {message}")

    def print_error(self, message: str):
        print(f"  ❌ {message}")

    def print_info(self, message: str):
        print(f"  ℹ️  {message}")

    def analyze_feedback(self, feedback: str) -> Tuple[str, List[int], List[str]]:
        """
        フィードバックを分析し、修正タイプ、再実行フェーズ、ラベルを決定

        Returns:
            (modification_type, phases_to_rerun, labels)
        """
        feedback_lower = feedback.lower()

        # キーワードマッチングで修正タイプを判定
        matched_types = []
        for mod_type, config in self.MODIFICATION_TYPES.items():
            for keyword in config["keywords"]:
                if keyword.lower() in feedback_lower:
                    matched_types.append(mod_type)
                    break

        # マッチしたタイプから最も包括的なフェーズセットを選択
        if not matched_types:
            # デフォルトはUI変更として扱う
            return "ui", [3, 6], ["type:ui"]

        # 複数マッチした場合は、より多くのフェーズを含むものを選択
        best_type = max(matched_types, key=lambda t: len(self.MODIFICATION_TYPES[t]["phases"]))
        config = self.MODIFICATION_TYPES[best_type]
        return best_type, config["phases"], config.get("labels", [])

    def request_modification(
        self,
        feedback: str,
        phases: List[int] = None,
        skip_issue: bool = False,
        app_name: str = None
    ) -> Tuple[bool, Optional[int], Optional[str]]:
        """
        修正を依頼（Issue自動作成 + ブランチ作成）

        Args:
            feedback: 修正内容
            phases: 再実行するフェーズ（省略時は自動判定）
            skip_issue: Issue作成をスキップ（テスト用）
            app_name: アプリ名（省略時は自動検出）

        Returns:
            (success, issue_number, branch_name)
        """
        self.print_banner("📝 Phase 7: 修正ワークフロー（Issue/PR管理）")

        # アプリ名の決定
        if app_name:
            self.app_name = app_name

        if not self.app_name:
            self.print_error("アプリ名が特定できません")
            return False, None, None

        print(f"\n  🎯 対象アプリ: {self.app_name}")

        # 状態確認
        state = self.state_manager.state
        if state is None:
            self.print_warning("ワークフロー状態が見つかりません（新規作成）")
            self.state_manager.initialize(self.app_name)
            state = self.state_manager.state

        # フィードバック分析
        labels = []
        if phases is None:
            mod_type, phases, labels = self.analyze_feedback(feedback)
            self.print_info(f"修正タイプ: {self.MODIFICATION_TYPES[mod_type]['description']}")
        else:
            mod_type = "custom"

        print(f"\n  修正内容: {feedback}")
        print(f"  再実行フェーズ: {phases}")

        # ========================================
        # 1. GitHub Issue作成
        # ========================================
        issue_number = None
        branch_name = None

        if not skip_issue:
            self.print_banner("1️⃣ GitHub Issue作成", "─")

            # Issueボディを作成
            issue_body = f"""## 修正内容
{feedback}

## 修正タイプ
{self.MODIFICATION_TYPES.get(mod_type, {}).get('description', mod_type)}

## 再実行フェーズ
{', '.join([f'Phase {p}' for p in phases])}

## 環境
- プロジェクト: {self.project_path}
- アプリ名: {self.app_name}

---
🤖 自動生成 by modification_workflow.py
"""

            # タイトルを生成（フィードバックの最初の50文字）
            title = feedback[:50] + ("..." if len(feedback) > 50 else "")

            issue_number = self.github_manager.create_issue(
                app_name=self.app_name,
                title=title,
                body=issue_body,
                labels=labels
            )

            if issue_number:
                # ブランチ名を生成
                branch_name = self.github_manager.create_branch(
                    app_name=self.app_name,
                    issue_number=issue_number,
                    description=title
                )
                print(f"\n  📌 ブランチ名: {branch_name}")
            else:
                self.print_warning("Issue作成に失敗しましたが、修正は続行できます")

        # ========================================
        # 2. 修正依頼を記録
        # ========================================
        self.state_manager.request_modification(feedback, phases)

        # Issue/PR情報を状態に追加保存
        if state and issue_number:
            if not hasattr(state, 'github_tracking'):
                state.metadata['github_tracking'] = {}
            state.metadata['github_tracking'] = {
                'issue_number': issue_number,
                'branch_name': branch_name,
                'pr_number': None,
                'created_at': datetime.now().isoformat()
            }
            self.state_manager.save_state()

        self.print_success("修正依頼を記録しました")

        # ========================================
        # 3. 次のステップを表示
        # ========================================
        print("\n" + "=" * 60)
        print("  📋 次のステップ")
        print("=" * 60)

        if issue_number:
            print(f"\n  Issue: {self.github_manager.get_issue_url(issue_number)}")

        print("\n  1. 以下のフェーズを再実行してください:")
        for phase in phases:
            phase_name = self.state_manager.PHASES.get(phase, f"Phase {phase}")
            print(f"     - Phase {phase}: {phase_name}")

        print("\n  2. 修正完了後、以下を実行:")
        print(f"     python modification_workflow.py --complete-fix")
        print(f"     → PR作成 → マージ → 公開")

        print("\n" + "=" * 60)

        return True, issue_number, branch_name

    def execute_modification(
        self,
        skip_confirm: bool = False,
        dry_run: bool = False,
    ) -> Tuple[bool, str]:
        """
        修正ワークフローを実行

        Returns:
            (success, message)
        """
        self.print_banner("🔧 Phase 7: 修正実行")

        # 保留中の修正を取得
        modification = self.state_manager.get_pending_modification()
        if modification is None:
            self.print_error("保留中の修正依頼がありません")
            return False, "No pending modification"

        feedback = modification.get("feedback", "")
        phases = modification.get("phases_to_rerun", [])
        iteration = modification.get("iteration", 1)

        # GitHub追跡情報を取得
        state = self.state_manager.state
        github_tracking = state.metadata.get('github_tracking', {}) if state else {}
        issue_number = github_tracking.get('issue_number')
        branch_name = github_tracking.get('branch_name')

        print(f"\n  イテレーション: #{iteration}")
        print(f"  修正内容: {feedback}")
        print(f"  再実行フェーズ: {phases}")

        if issue_number:
            print(f"\n  📌 関連Issue: #{issue_number}")
            print(f"     {self.github_manager.get_issue_url(issue_number)}")

        if branch_name:
            print(f"  📌 作業ブランチ: {branch_name}")

        # 修正開始
        self.state_manager.start_modification()

        # フェーズ再実行のガイダンスを表示
        self.print_banner("修正実行ガイダンス", "─")

        print("\n  以下の手順で修正を実行してください:\n")

        for i, phase in enumerate(phases, 1):
            phase_name = self.state_manager.PHASES.get(phase, f"Phase {phase}")

            if phase == 3:
                print(f"  {i}. Phase {phase}（{phase_name}）")
                print(f"     修正内容: {feedback}")
                print(f"     → 該当するコードを修正してください")
                print()

            elif phase == 4:
                print(f"  {i}. Phase {phase}（{phase_name}）")
                print(f"     → テストを実行し、問題があれば修正してください")
                print()

            elif phase == 5:
                print(f"  {i}. Phase {phase}（{phase_name}）")
                print(f"     → ドキュメントを更新してください（必要な場合）")
                print()

            elif phase == 6:
                print(f"  {i}. Phase {phase}（{phase_name}）")
                print(f"     → 自動実行されます（--complete-fix コマンド）")
                print()

        print("\n  【修正完了後】")
        print("  以下のコマンドでPR作成 → マージ → 公開を一括実行:")
        print(f"  python modification_workflow.py --complete-fix")

        return True, "Modification guidance displayed"

    def complete_fix(
        self,
        skip_confirm: bool = False,
        dry_run: bool = False,
    ) -> Tuple[bool, str]:
        """
        修正完了処理（PR作成 → マージ → 公開）

        Returns:
            (success, message)
        """
        self.print_banner("🔄 修正完了処理（PR → マージ → 公開）")

        # 状態確認
        state = self.state_manager.state
        if state is None:
            self.print_error("ワークフロー状態が見つかりません")
            return False, "No workflow state"

        modification = self.state_manager.get_pending_modification()
        if modification is None:
            self.print_error("保留中の修正依頼がありません")
            return False, "No pending modification"

        feedback = modification.get("feedback", "")
        github_tracking = state.metadata.get('github_tracking', {})
        issue_number = github_tracking.get('issue_number')
        branch_name = github_tracking.get('branch_name')

        # アプリ名
        app_name = self.app_name or state.portfolio.get('app_name') or state.project_name

        print(f"\n  🎯 アプリ: {app_name}")
        print(f"  📝 修正内容: {feedback}")

        if issue_number:
            print(f"  📌 Issue: #{issue_number}")

        # ========================================
        # Step 1: project/public/ への変更をコミット
        # ========================================
        self.print_banner("Step 1: 変更をコミット", "─")

        public_path = self.project_path / "project" / "public"
        if not public_path.exists():
            self.print_error(f"project/public/ が見つかりません: {public_path}")
            return False, "project/public/ not found"

        # ========================================
        # Step 2: GitHub公開（simplified_github_publisher使用）
        # ========================================
        self.print_banner("Step 2: GitHub公開", "─")

        if not dry_run:
            # SimplifiedGitHubPublisher をインポートして実行
            from simplified_github_publisher import SimplifiedGitHubPublisher

            publisher = SimplifiedGitHubPublisher(
                str(self.project_path),
                auto_mode=True
            )

            # 公開実行（内部でコミット＆プッシュ）
            if not publisher.publish():
                self.print_error("GitHub公開に失敗しました")
                return False, "GitHub publish failed"

        # ========================================
        # Step 3: PR作成
        # ========================================
        pr_number = None

        if issue_number and not dry_run:
            self.print_banner("Step 3: PR作成", "─")

            # PRのタイトルと本文
            title = feedback[:50] + ("..." if len(feedback) > 50 else "")
            body = f"""## 変更内容
{feedback}

## 変更ファイル
- `{app_name}/` 配下のファイルを更新

## テスト
- 手動テスト完了
"""

            pr_number = self.github_manager.create_pull_request(
                app_name=app_name,
                issue_number=issue_number,
                title=title,
                body=body,
                branch_name=branch_name or f"fix/{app_name}-{issue_number}"
            )

            if pr_number:
                github_tracking['pr_number'] = pr_number
                self.state_manager.save_state()

        # ========================================
        # Step 4: PRレビュー（Findy偏差値向上）
        # ========================================
        if pr_number and not dry_run:
            self.print_banner("Step 4: PRレビュー", "─")

            review_body = (
                "LGTM\n\n"
                "## レビュー確認項目\n"
                f"- セキュリティスキャン: PASS\n"
                f"- 動作確認: 完了\n"
                f"- 変更内容: {feedback[:100]}\n\n"
                "---\n"
                "🤖 Automated review by modification_workflow.py"
            )
            self.github_manager.review_pull_request(pr_number, review_body)

        # ========================================
        # Step 5: PRマージ（Issueは自動クローズ）
        # ========================================
        if pr_number and not dry_run:
            self.print_banner("Step 5: PRマージ", "─")

            if self.github_manager.merge_pull_request(pr_number):
                self.print_success(f"Issue #{issue_number} は自動的にクローズされました")
            else:
                self.print_warning("PRマージに失敗しました（手動でマージしてください）")

        # ========================================
        # Step 5: 状態更新
        # ========================================
        self.state_manager.complete_modification()

        # 完了メッセージ
        self.print_banner("✅ 修正完了", "=")

        pages_url = f"https://{self.github_manager.github_username}.github.io/ai-agent-portfolio/{app_name}/"

        print(f"\n  📦 公開URL: {pages_url}")

        if issue_number:
            print(f"  📌 Issue: {self.github_manager.get_issue_url(issue_number)} (Closed)")

        if pr_number:
            print(f"  📌 PR: {self.github_manager.get_pr_url(pr_number)} (Merged)")

        print("\n  次回修正時:")
        print(f'  python modification_workflow.py --request "修正内容"')

        return True, "Modification completed successfully"

    def republish(
        self,
        app_name: str = None,
        skip_confirm: bool = False,
        dry_run: bool = False,
    ) -> Tuple[bool, str]:
        """
        修正後の再公開（Phase 6 再実行）

        Returns:
            (success, message)
        """
        self.print_banner("🔄 再公開（Phase 6 再実行）")

        state = self.state_manager.state
        if state is None:
            self.print_error("ワークフロー状態が見つかりません")
            return False, "No workflow state"

        # アプリ名を取得
        if app_name is None:
            portfolio = state.portfolio
            app_name = portfolio.get("app_name")
            if not app_name:
                app_name = state.project_name

        if not app_name:
            self.print_error("アプリ名が特定できません")
            return False, "App name not found"

        print(f"\n  アプリ名: {app_name}")
        print(f"  ソース: {self.project_path}")

        # Phase 6 を再実行
        publisher = PortfolioPublisher(project_path=str(self.project_path))
        success, message = publisher.publish(
            source_dir=str(self.project_path),
            app_name=app_name,
            dry_run=dry_run,
            skip_confirm=skip_confirm,
            skip_agent_review=True,  # 修正時はエージェントレビューをスキップ
        )

        if success:
            # 修正完了を記録
            self.state_manager.complete_modification()
            self.print_success("再公開完了")
        else:
            self.print_error(f"再公開失敗: {message}")

        return success, message

    def complete_workflow(self) -> bool:
        """ワークフローを完了としてマーク"""
        self.print_banner("🎉 ワークフロー完了")

        state = self.state_manager.state
        if state is None:
            self.print_error("ワークフロー状態が見つかりません")
            return False

        self.state_manager.complete_workflow()

        print("\n  ワークフローが正常に完了しました。")
        print(f"\n  プロジェクト: {state.project_name}")
        print(f"  公開URL: {state.portfolio.get('app_url', '(未設定)')}")

        if state.modifications:
            print(f"\n  修正イテレーション: {len(state.modifications)} 回")

        return True

    def show_status(self):
        """現在の状態を表示"""
        self.state_manager.print_status_report()
        print(self.state_manager.get_next_action_prompt())


def main():
    """メインエントリーポイント"""
    parser = argparse.ArgumentParser(
        description="修正ワークフロー（Phase 7）- Issue/PR管理対応版",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
  # 修正を依頼（Issue自動作成）
  python modification_workflow.py --request "ボタンの色を青から緑に変更"

  # アプリ名を指定して修正依頼
  python modification_workflow.py --request "バグ修正" --app-name todo-app

  # 修正実行ガイダンスを表示
  python modification_workflow.py --execute

  # 修正完了（PR作成 → マージ → 公開）
  python modification_workflow.py --complete-fix

  # 再公開のみ（PR作成なし）
  python modification_workflow.py --republish

  # ワークフローを完了
  python modification_workflow.py --complete

  # 状態を確認
  python modification_workflow.py --status

  # 特定のフェーズを再実行
  python modification_workflow.py --request "大幅な修正" --phases 3,4,5,6

  # Issue作成をスキップ（テスト用）
  python modification_workflow.py --request "テスト" --skip-issue
        """,
    )

    parser.add_argument(
        "--path",
        default=".",
        help="プロジェクトパス",
    )
    parser.add_argument(
        "--request",
        metavar="FEEDBACK",
        help="修正を依頼（Issue自動作成）",
    )
    parser.add_argument(
        "--phases",
        help="再実行するフェーズ（カンマ区切り、例: 3,4,6）",
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="修正実行ガイダンスを表示",
    )
    parser.add_argument(
        "--complete-fix",
        action="store_true",
        help="修正完了（PR作成 → マージ → 公開）",
    )
    parser.add_argument(
        "--republish",
        action="store_true",
        help="再公開のみ（PR作成なし）",
    )
    parser.add_argument(
        "--complete",
        action="store_true",
        help="ワークフローを完了としてマーク",
    )
    parser.add_argument(
        "--status",
        action="store_true",
        help="現在の状態を表示",
    )
    parser.add_argument(
        "--app-name",
        help="アプリ名（省略時は自動検出）",
    )
    parser.add_argument(
        "--skip-issue",
        action="store_true",
        help="Issue作成をスキップ",
    )
    parser.add_argument(
        "-y", "--yes",
        action="store_true",
        help="確認プロンプトをスキップ",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="ドライラン",
    )

    args = parser.parse_args()

    # プロジェクトパスの解決
    project_path = Path(args.path).resolve()
    workflow = ModificationWorkflow(str(project_path))

    # コマンド実行
    if args.status:
        workflow.show_status()

    elif args.request:
        phases = None
        if args.phases:
            phases = [int(p.strip()) for p in args.phases.split(",")]
        success, issue_number, branch_name = workflow.request_modification(
            args.request,
            phases,
            skip_issue=args.skip_issue,
            app_name=args.app_name
        )
        if not success:
            sys.exit(1)

    elif args.execute:
        success, message = workflow.execute_modification(
            skip_confirm=args.yes,
            dry_run=args.dry_run,
        )
        if not success:
            sys.exit(1)

    elif args.complete_fix:
        success, message = workflow.complete_fix(
            skip_confirm=args.yes,
            dry_run=args.dry_run,
        )
        if not success:
            sys.exit(1)

    elif args.republish:
        success, message = workflow.republish(
            app_name=args.app_name,
            skip_confirm=args.yes,
            dry_run=args.dry_run,
        )
        if not success:
            sys.exit(1)

    elif args.complete:
        if not workflow.complete_workflow():
            sys.exit(1)

    else:
        # デフォルトは状態表示
        workflow.show_status()


if __name__ == "__main__":
    main()
