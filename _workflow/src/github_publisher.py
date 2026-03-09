#!/usr/bin/env python3
"""
GitHub公開スクリプト
DELIVERYフォルダをポートフォリオリポジトリに公開
"""

import os
import subprocess
import shutil
import json
from pathlib import Path
from typing import Optional, Tuple, List
from dataclasses import dataclass
from datetime import datetime

from portfolio_config import get_config, PortfolioConfig


@dataclass
class PublishResult:
    """公開結果"""
    success: bool
    app_name: str
    app_url: str
    commit_hash: str
    message: str
    files_added: int
    files_modified: int
    files_deleted: int


class GitHubPublisher:
    """GitHub公開パブリッシャー"""

    def __init__(self, config: PortfolioConfig = None):
        self.config = config or get_config()
        self.repo_local_path = Path.home() / "Desktop" / "GitHub" / self.config.github_repo

    def ensure_repo_cloned(self) -> bool:
        """リポジトリがクローンされていることを確認"""
        if self.repo_local_path.exists() and (self.repo_local_path / ".git").exists():
            print(f"  リポジトリ存在確認: ✅ {self.repo_local_path}")
            return True

        print(f"  リポジトリをクローン中...")
        self.repo_local_path.parent.mkdir(parents=True, exist_ok=True)

        result = subprocess.run(
            ["git", "clone", self.config.repo_clone_url, str(self.repo_local_path)],
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            print(f"  ❌ クローン失敗: {result.stderr}")
            return False

        print(f"  ✅ クローン完了: {self.repo_local_path}")
        return True

    def pull_latest(self) -> bool:
        """最新の変更をプル"""
        print(f"  最新の変更をプル中...")

        result = subprocess.run(
            ["git", "pull", "origin", "main"],
            cwd=self.repo_local_path,
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            # rebaseを試みる
            result = subprocess.run(
                ["git", "pull", "--rebase", "origin", "main"],
                cwd=self.repo_local_path,
                capture_output=True,
                text=True,
            )
            if result.returncode != 0:
                print(f"  ⚠️ プル失敗（続行可能）: {result.stderr[:100]}")
                return True  # 続行を許可

        print(f"  ✅ プル完了")
        return True

    def copy_delivery_to_repo(
        self,
        delivery_path: str,
        app_name: str,
    ) -> Tuple[int, int, int]:
        """
        DELIVERYフォルダの内容をリポジトリにコピー

        Returns:
            (added, modified, deleted): ファイル数
        """
        delivery = Path(delivery_path)
        app_dest = self.repo_local_path / "apps" / app_name

        # 既存のアプリフォルダがあれば削除
        if app_dest.exists():
            shutil.rmtree(app_dest)

        # コピー
        app_dest.mkdir(parents=True, exist_ok=True)

        copied = 0
        for src_file in delivery.rglob("*"):
            if not src_file.is_file():
                continue

            # マニフェストは除外
            if src_file.name == ".delivery_manifest.json":
                continue

            rel_path = src_file.relative_to(delivery)
            dest_file = app_dest / rel_path
            dest_file.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src_file, dest_file)
            copied += 1

        print(f"  ✅ {copied} ファイルをコピーしました")

        # git status で変更を確認
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=self.repo_local_path,
            capture_output=True,
            text=True,
        )

        added = modified = deleted = 0
        for line in result.stdout.strip().split("\n"):
            if not line:
                continue
            status = line[:2]
            if "A" in status or "?" in status:
                added += 1
            elif "M" in status:
                modified += 1
            elif "D" in status:
                deleted += 1

        return added, modified, deleted

    def get_diff_summary(self) -> str:
        """差分のサマリーを取得"""
        result = subprocess.run(
            ["git", "diff", "--stat", "HEAD"],
            cwd=self.repo_local_path,
            capture_output=True,
            text=True,
        )
        return result.stdout

    def get_staged_files(self) -> List[str]:
        """ステージされたファイル一覧を取得"""
        result = subprocess.run(
            ["git", "diff", "--cached", "--name-only"],
            cwd=self.repo_local_path,
            capture_output=True,
            text=True,
        )
        return [f for f in result.stdout.strip().split("\n") if f]

    def stage_changes(self, app_name: str) -> bool:
        """変更をステージング"""
        app_path = f"apps/{app_name}"

        # アプリフォルダのみをステージ
        result = subprocess.run(
            ["git", "add", app_path],
            cwd=self.repo_local_path,
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            print(f"  ❌ ステージング失敗: {result.stderr}")
            return False

        print(f"  ✅ 変更をステージしました")
        return True

    def create_commit(self, app_name: str, is_update: bool = False) -> Optional[str]:
        """コミットを作成"""
        action = "Update" if is_update else "Add"
        message = f"{action} {app_name} to portfolio\n\nPublished via AI Agent Workflow"

        result = subprocess.run(
            ["git", "commit", "-m", message],
            cwd=self.repo_local_path,
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            if "nothing to commit" in result.stdout or "nothing to commit" in result.stderr:
                print(f"  ℹ️ 変更がありません（コミット不要）")
                return None
            print(f"  ❌ コミット失敗: {result.stderr}")
            return None

        # コミットハッシュを取得
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=self.repo_local_path,
            capture_output=True,
            text=True,
        )

        commit_hash = result.stdout.strip()[:8]
        print(f"  ✅ コミット作成: {commit_hash}")
        return commit_hash

    def push_to_remote(self) -> bool:
        """リモートにプッシュ"""
        print(f"  プッシュ中...")

        result = subprocess.run(
            ["git", "push", "origin", "main"],
            cwd=self.repo_local_path,
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            print(f"  ❌ プッシュ失敗: {result.stderr}")
            return False

        print(f"  ✅ プッシュ完了")
        return True

    def publish(
        self,
        delivery_path: str,
        app_name: str,
        dry_run: bool = False,
        skip_push: bool = False,
    ) -> PublishResult:
        """
        DELIVERYフォルダを公開

        Args:
            delivery_path: DELIVERYフォルダのパス
            app_name: アプリ名
            dry_run: True の場合、実際のプッシュは行わない
            skip_push: True の場合、コミットまで行いプッシュはスキップ
        """
        print("\n" + "=" * 60)
        print("  GitHub公開")
        print("=" * 60)

        app_url = self.config.get_app_url(app_name)

        # 1. リポジトリ準備
        if not self.ensure_repo_cloned():
            return PublishResult(
                success=False,
                app_name=app_name,
                app_url=app_url,
                commit_hash="",
                message="リポジトリのクローンに失敗しました",
                files_added=0,
                files_modified=0,
                files_deleted=0,
            )

        # 2. 最新をプル
        self.pull_latest()

        # 3. ファイルをコピー
        print(f"\n  ファイルをコピー中...")
        added, modified, deleted = self.copy_delivery_to_repo(delivery_path, app_name)
        print(f"    追加: {added}, 変更: {modified}, 削除: {deleted}")

        # 4. ステージング
        if not self.stage_changes(app_name):
            return PublishResult(
                success=False,
                app_name=app_name,
                app_url=app_url,
                commit_hash="",
                message="ステージングに失敗しました",
                files_added=added,
                files_modified=modified,
                files_deleted=deleted,
            )

        # 5. 差分サマリー表示
        staged_files = self.get_staged_files()
        print(f"\n  【公開されるファイル: {len(staged_files)} 件】")
        for f in staged_files[:20]:
            print(f"    - {f}")
        if len(staged_files) > 20:
            print(f"    ... 他 {len(staged_files) - 20} ファイル")

        if dry_run:
            print(f"\n  🔍 ドライラン: 実際の公開は行いません")
            return PublishResult(
                success=True,
                app_name=app_name,
                app_url=app_url,
                commit_hash="(dry-run)",
                message="ドライラン完了",
                files_added=added,
                files_modified=modified,
                files_deleted=deleted,
            )

        # 6. コミット作成
        is_update = (self.repo_local_path / "apps" / app_name).exists()
        commit_hash = self.create_commit(app_name, is_update)

        if commit_hash is None:
            return PublishResult(
                success=True,
                app_name=app_name,
                app_url=app_url,
                commit_hash="(no changes)",
                message="変更がありませんでした",
                files_added=added,
                files_modified=modified,
                files_deleted=deleted,
            )

        if skip_push:
            print(f"\n  ⏸️ プッシュはスキップされました（--skip-push）")
            return PublishResult(
                success=True,
                app_name=app_name,
                app_url=app_url,
                commit_hash=commit_hash,
                message="コミット作成完了（プッシュ待ち）",
                files_added=added,
                files_modified=modified,
                files_deleted=deleted,
            )

        # 7. プッシュ
        if not self.push_to_remote():
            return PublishResult(
                success=False,
                app_name=app_name,
                app_url=app_url,
                commit_hash=commit_hash,
                message="プッシュに失敗しました",
                files_added=added,
                files_modified=modified,
                files_deleted=deleted,
            )

        print("\n" + "=" * 60)
        print("  ✅ 公開完了!")
        print("=" * 60)
        print(f"\n  アプリURL: {app_url}")
        print(f"  コミット: {commit_hash}")
        print("=" * 60 + "\n")

        return PublishResult(
            success=True,
            app_name=app_name,
            app_url=app_url,
            commit_hash=commit_hash,
            message="公開成功",
            files_added=added,
            files_modified=modified,
            files_deleted=deleted,
        )

    def execute_push(self) -> bool:
        """保留中のコミットをプッシュ"""
        return self.push_to_remote()


def publish_delivery(
    delivery_path: str,
    app_name: str,
    dry_run: bool = False,
    skip_push: bool = False,
) -> PublishResult:
    """
    DELIVERYフォルダを公開（便利関数）
    """
    publisher = GitHubPublisher()
    return publisher.publish(
        delivery_path=delivery_path,
        app_name=app_name,
        dry_run=dry_run,
        skip_push=skip_push,
    )


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="GitHub公開")
    parser.add_argument("delivery_path", help="DELIVERYフォルダのパス")
    parser.add_argument("app_name", help="アプリ名")
    parser.add_argument("--dry-run", action="store_true", help="ドライラン（実際の公開なし）")
    parser.add_argument("--skip-push", action="store_true", help="コミットまで行いプッシュはスキップ")
    args = parser.parse_args()

    result = publish_delivery(
        delivery_path=args.delivery_path,
        app_name=args.app_name,
        dry_run=args.dry_run,
        skip_push=args.skip_push,
    )

    if result.success:
        print(f"✅ {result.message}")
        print(f"   URL: {result.app_url}")
    else:
        print(f"❌ {result.message}")
        exit(1)
