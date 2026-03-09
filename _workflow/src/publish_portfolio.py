#!/usr/bin/env python3
"""
ポートフォリオ公開メインスクリプト（Phase 6）
ワークフロー状態管理と統合、エージェントによるハイブリッドセキュリティチェック対応

フェーズ:
1. DELIVERY準備（スクリプト）
2. セキュリティチェック第1弾（スクリプト）
3. エージェントセキュリティレビュー（ハイブリッド）
4. Git操作（コミットまで）
5. ユーザー確認後プッシュ
6. 状態更新・レビュー待ち移行
"""

import os
import sys
import json
import argparse
from pathlib import Path
from typing import Optional, Tuple, List
from datetime import datetime

# 同じディレクトリのモジュールをインポート
sys.path.insert(0, str(Path(__file__).parent))

from portfolio_config import get_config, PortfolioConfig
from security_checker import SecurityChecker, print_report, Severity
from delivery_organizer import DeliveryOrganizer
from github_publisher import GitHubPublisher, PublishResult
from workflow_state_manager import WorkflowStateManager, get_state_manager


class PortfolioPublisher:
    """ポートフォリオ公開オーケストレーター（Phase 6）"""

    def __init__(self, config: PortfolioConfig = None, project_path: str = None):
        self.config = config or get_config()
        self.security_checker = SecurityChecker(self.config)
        self.delivery_organizer = DeliveryOrganizer(self.config)
        self.github_publisher = GitHubPublisher(self.config)

        # 状態管理
        self.project_path = Path(project_path) if project_path else Path.cwd()
        self.state_manager = get_state_manager(str(self.project_path))

    def print_banner(self, title: str, char: str = "="):
        """バナーを表示"""
        width = 60
        print("\n" + char * width)
        print(f"  {title}")
        print(char * width)

    def print_phase(self, phase_num: int, title: str):
        """フェーズヘッダーを表示"""
        print(f"\n{'─' * 60}")
        print(f"  【Phase 6-{phase_num}】 {title}")
        print(f"{'─' * 60}")

    def print_success(self, message: str):
        print(f"  ✅ {message}")

    def print_warning(self, message: str):
        print(f"  ⚠️  {message}")

    def print_error(self, message: str):
        print(f"  ❌ {message}")

    def print_info(self, message: str):
        print(f"  ℹ️  {message}")

    def confirm_action(self, prompt: str, default: bool = False) -> bool:
        """ユーザー確認を取得"""
        suffix = " [Y/n]: " if default else " [y/N]: "
        try:
            response = input(f"\n  {prompt}{suffix}").strip().lower()
            if not response:
                return default
            return response in ("y", "yes", "はい")
        except (EOFError, KeyboardInterrupt):
            print("\n  操作がキャンセルされました。")
            return False

    def generate_agent_review_prompt(self, files: List[str], delivery_path: str) -> str:
        """エージェントセキュリティレビュー用のプロンプトを生成"""
        files_list = "\n".join([f"  - {f}" for f in files[:50]])
        if len(files) > 50:
            files_list += f"\n  ... 他 {len(files) - 50} ファイル"

        return f"""
## エージェントセキュリティレビュー（Phase 6-3）

以下のファイルがGitHubに公開されます。セキュリティ観点でレビューしてください。

### 公開対象ファイル
{files_list}

### チェック項目
1. **APIキー・トークン**: 各種サービスのAPIキーが含まれていないか
2. **認証情報**: パスワード、秘密鍵、証明書が含まれていないか
3. **内部情報**: 社内URL、IPアドレス、ユーザー名パスが含まれていないか
4. **個人情報**: メールアドレス、電話番号等が含まれていないか
5. **デバッグ情報**: console.log、デバッグコード、テストデータが残っていないか

### 判定
- **SAFE**: 公開して問題なし
- **UNSAFE**: 公開を中止すべき問題あり（理由を明記）
- **REVIEW_NEEDED**: 人間の確認が必要（懸念点を明記）

### 出力形式
```
判定: [SAFE/UNSAFE/REVIEW_NEEDED]
理由: [判定理由]
懸念点: [あれば列挙]
```

DELIVERYフォルダのパス: {delivery_path}
"""

    def publish(
        self,
        source_dir: str,
        app_name: str,
        dry_run: bool = False,
        skip_confirm: bool = False,
        skip_agent_review: bool = False,
        verbose: bool = False,
    ) -> Tuple[bool, str]:
        """
        ポートフォリオを公開（Phase 6）

        Args:
            source_dir: ソースディレクトリ
            app_name: アプリ名
            dry_run: ドライランモード
            skip_confirm: 確認をスキップ
            skip_agent_review: エージェントレビューをスキップ
            verbose: 詳細表示

        Returns:
            (success, message): 結果
        """
        # ワークフロー状態を更新
        state = self.state_manager.get_or_create(app_name)
        self.state_manager.start_phase(6, agents=["portfolio_publisher"])

        self.print_banner("🚀 Phase 6: ポートフォリオ公開ワークフロー")
        print(f"\n  ソース: {source_dir}")
        print(f"  アプリ名: {app_name}")
        print(f"  リポジトリ: {self.config.github_repo}")
        print(f"  公開URL: {self.config.get_app_url(app_name)}")

        if dry_run:
            print(f"\n  🔍 ドライランモード: 実際の公開は行いません")

        # ========================================
        # Phase 6-1: DELIVERY準備
        # ========================================
        self.print_phase(1, "DELIVERY準備")

        try:
            manifest = self.delivery_organizer.prepare_delivery(
                source_dir=source_dir,
                app_name=app_name,
            )
        except Exception as e:
            self.state_manager.fail_phase(6, str(e))
            self.print_error(f"DELIVERY準備に失敗しました: {e}")
            return False, str(e)

        if not manifest.files:
            self.state_manager.fail_phase(6, "No files to publish")
            self.print_error("公開対象のファイルがありません")
            return False, "No files to publish"

        delivery_path = Path(source_dir) / "DELIVERY"
        self.print_success(f"{len(manifest.files)} ファイルを収集しました")

        # ========================================
        # Phase 6-2: セキュリティチェック（スクリプト）
        # ========================================
        self.print_phase(2, "セキュリティチェック（スクリプト）")

        security_report = self.security_checker.scan_directory(str(delivery_path))
        print_report(security_report, verbose)

        if security_report.has_critical:
            self.state_manager.fail_phase(6, "Security check failed: CRITICAL issues found")
            self.print_error("CRITICAL（重大）な問題が検出されました")
            self.print_error("公開を中止します。問題を解決してから再実行してください。")
            return False, "Security check failed: CRITICAL issues found"

        if security_report.has_high:
            self.print_warning("HIGH（高リスク）な問題が検出されました")
            if not skip_confirm:
                if not self.confirm_action("続行しますか？（推奨: No）"):
                    self.state_manager.fail_phase(6, "User cancelled due to HIGH security issues")
                    return False, "User cancelled due to HIGH security issues"

        script_security_passed = security_report.is_safe
        if script_security_passed:
            self.print_success("スクリプトセキュリティチェック通過")
        else:
            self.print_warning(f"{len(security_report.issues)} 件の問題を検出（MEDIUM/LOW）")

        # ========================================
        # Phase 6-3: エージェントセキュリティレビュー
        # ========================================
        self.print_phase(3, "エージェントセキュリティレビュー")

        agent_review_passed = True
        if skip_agent_review:
            self.print_info("エージェントレビューをスキップしました")
        else:
            # エージェントレビュー用プロンプトを生成
            agent_prompt = self.generate_agent_review_prompt(manifest.files, str(delivery_path))

            print("\n  【エージェントレビュー指示】")
            print("  以下の内容でエージェントにセキュリティレビューを依頼してください:")
            print("  " + "-" * 50)
            print(agent_prompt)
            print("  " + "-" * 50)

            # 自動実行の場合はスキップ、対話モードでは確認
            if not skip_confirm:
                print("\n  エージェントによるレビューが完了したら、結果を入力してください。")
                result = input("  レビュー結果 (SAFE/UNSAFE/REVIEW_NEEDED): ").strip().upper()

                if result == "UNSAFE":
                    self.state_manager.fail_phase(6, "Agent review: UNSAFE")
                    self.print_error("エージェントがUNSAFEと判定しました。公開を中止します。")
                    return False, "Agent review: UNSAFE"
                elif result == "REVIEW_NEEDED":
                    self.print_warning("エージェントがREVIEW_NEEDEDと判定しました。")
                    if not self.confirm_action("続行しますか？"):
                        self.state_manager.fail_phase(6, "User cancelled after REVIEW_NEEDED")
                        return False, "User cancelled after REVIEW_NEEDED"
                    agent_review_passed = True
                else:
                    agent_review_passed = True
                    self.print_success("エージェントセキュリティレビュー通過")
            else:
                self.print_info("対話モードでない場合、エージェントレビューは手動で実施してください")
                agent_review_passed = True

        # ========================================
        # Phase 6-4: Git操作（コミットまで）
        # ========================================
        self.print_phase(4, "Git操作")

        publish_result = self.github_publisher.publish(
            delivery_path=str(delivery_path),
            app_name=app_name,
            dry_run=dry_run,
            skip_push=True,  # Phase 6-5までプッシュしない
        )

        if not publish_result.success:
            self.state_manager.fail_phase(6, publish_result.message)
            self.print_error(f"Git操作に失敗しました: {publish_result.message}")
            return False, publish_result.message

        self.print_success(f"コミット作成完了: {publish_result.commit_hash}")
        self.print_info(f"追加: {publish_result.files_added}, 変更: {publish_result.files_modified}, 削除: {publish_result.files_deleted}")

        # ========================================
        # Phase 6-5: プッシュ
        # ========================================
        self.print_phase(5, "GitHub公開")

        if dry_run:
            self.print_info("ドライランモードのためプッシュをスキップします")
            self.state_manager.complete_phase(6, {"dry_run": True})
            return True, "Dry run completed successfully"

        if publish_result.commit_hash == "(no changes)":
            self.print_info("変更がないためプッシュは不要です")
            self.state_manager.complete_phase(6, {"no_changes": True})
            return True, "No changes to publish"

        if not skip_confirm:
            print("\n  ⚠️  この操作は取り消せません。")
            print(f"  リポジトリ '{self.config.github_repo}' に公開されます。")
            if not self.confirm_action("プッシュしてよろしいですか？"):
                self.print_info("プッシュをキャンセルしました")
                self.print_info("後でプッシュするには: git push origin main")
                return True, "Commit created but push cancelled"

        # プッシュ実行
        if not self.github_publisher.push_to_remote():
            self.state_manager.fail_phase(6, "Push failed")
            self.print_error("プッシュに失敗しました")
            return False, "Push failed"

        # ========================================
        # Phase 6-6: 状態更新・レビュー待ち
        # ========================================
        self.print_phase(6, "公開完了・レビュー待ち移行")

        # ポートフォリオ公開を記録
        self.state_manager.record_portfolio_publish(
            app_name=app_name,
            app_url=publish_result.app_url,
            commit_hash=publish_result.commit_hash,
            security_check_passed=script_security_passed,
            agent_review_passed=agent_review_passed,
        )

        # Phase 6 完了
        self.state_manager.complete_phase(6, {
            "app_name": app_name,
            "app_url": publish_result.app_url,
            "commit_hash": publish_result.commit_hash,
        })

        self.print_banner("📋 公開完了 - ユーザーレビュー待ち", "═")

        print(f"\n  🎉 GitHub公開成功!")
        print(f"\n  リポジトリ: {self.config.repo_url}")
        print(f"  アプリURL: {publish_result.app_url}")
        print(f"  コミット: {publish_result.commit_hash}")

        print("\n  【次のステップ】")
        print(f"  1. 公開されたアプリを確認: {publish_result.app_url}")
        print(f"  2. 問題があれば修正を依頼（Phase 7が実行されます）")
        print(f"  3. 問題なければ「完了」と伝えてください")

        print("\n  【修正依頼の例】")
        print('  「修正依頼: ボタンの色を青から緑に変更してください」')

        self.print_banner("Phase 6 完了", "═")

        # 状態レポートを表示
        self.state_manager.print_status_report()

        return True, "Published successfully - awaiting user review"


def main():
    """メインエントリーポイント"""
    parser = argparse.ArgumentParser(
        description="ポートフォリオ公開ワークフロー（Phase 6）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
  # 基本的な使用
  python publish_portfolio.py /path/to/app my-app

  # ドライラン（実際の公開なし）
  python publish_portfolio.py /path/to/app my-app --dry-run

  # 確認なしで実行（CI/CD用）
  python publish_portfolio.py /path/to/app my-app --yes

  # エージェントレビューをスキップ
  python publish_portfolio.py /path/to/app my-app --skip-agent-review

  # 詳細表示
  python publish_portfolio.py /path/to/app my-app -v
        """,
    )

    parser.add_argument(
        "source",
        help="ソースディレクトリ（アプリのルート）",
    )
    parser.add_argument(
        "app_name",
        nargs="?",
        help="アプリ名（省略時はフォルダ名を使用）",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="ドライラン（実際の公開は行わない）",
    )
    parser.add_argument(
        "-y", "--yes",
        action="store_true",
        help="確認プロンプトをスキップ",
    )
    parser.add_argument(
        "--skip-agent-review",
        action="store_true",
        help="エージェントセキュリティレビューをスキップ",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="詳細表示",
    )

    args = parser.parse_args()

    # ソースディレクトリの検証
    source_path = Path(args.source).resolve()
    if not source_path.exists():
        print(f"❌ ソースディレクトリが存在しません: {source_path}")
        sys.exit(1)

    # アプリ名の決定
    app_name = args.app_name or source_path.name
    app_name = app_name.lower().replace(" ", "-").replace("_", "-")

    # 公開実行
    publisher = PortfolioPublisher(project_path=str(source_path))
    success, message = publisher.publish(
        source_dir=str(source_path),
        app_name=app_name,
        dry_run=args.dry_run,
        skip_confirm=args.yes,
        skip_agent_review=args.skip_agent_review,
        verbose=args.verbose,
    )

    if success:
        print(f"\n✅ {message}")
        sys.exit(0)
    else:
        print(f"\n❌ {message}")
        sys.exit(1)


if __name__ == "__main__":
    main()
