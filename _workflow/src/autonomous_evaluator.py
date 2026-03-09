#!/usr/bin/env python3
"""
自律評価システム - Phase別worktreeの自動評価・選択

複数のworktreeを自動的に評価し、最良のものを選択する
"""

import json
import os
import subprocess
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class EvaluationCriteria:
    """評価基準"""
    test_pass_rate: float = 0.30    # テスト合格率の重み
    code_quality: float = 0.25      # コード品質の重み
    performance: float = 0.20       # パフォーマンスの重み
    security: float = 0.15          # セキュリティの重み
    simplicity: float = 0.10        # シンプルさの重み


@dataclass
class WorktreeScore:
    """worktreeの評価スコア"""
    worktree_path: str
    total_score: float
    test_pass_rate: float
    code_quality: float
    performance: float
    security: float
    simplicity: float
    details: Dict


class AutonomousEvaluator:
    """自律評価システム"""

    def __init__(self, project_path: Path):
        self.project_path = Path(project_path)
        self.worktrees_dir = self.project_path / "worktrees"

    def evaluate_test_pass_rate(self, worktree_path: Path) -> float:
        """
        テスト合格率を評価

        Returns:
            float: スコア（0-100）
        """
        try:
            # テスト結果ファイルを確認
            test_result_file = worktree_path / "test-results.json"

            if not test_result_file.exists():
                # テストを実行
                result = subprocess.run(
                    ["npm", "test", "--", "--json"],
                    cwd=worktree_path,
                    capture_output=True,
                    text=True,
                    timeout=300
                )

                if result.returncode == 0:
                    test_data = json.loads(result.stdout)
                    total = test_data.get('numTotalTests', 0)
                    passed = test_data.get('numPassedTests', 0)

                    if total > 0:
                        pass_rate = (passed / total) * 100
                        logger.info(f"✅ Test pass rate: {pass_rate:.1f}% ({passed}/{total})")
                        return pass_rate
                    else:
                        logger.warning("⚠️ No tests found")
                        return 50.0  # テストがない場合は中間スコア
                else:
                    logger.warning(f"⚠️ Test execution failed: {result.stderr}")
                    return 0.0

            else:
                # 既存の結果を読み込み
                with open(test_result_file) as f:
                    test_data = json.load(f)
                    total = test_data.get('numTotalTests', 0)
                    passed = test_data.get('numPassedTests', 0)
                    if total > 0:
                        return (passed / total) * 100
                    else:
                        return 50.0

        except Exception as e:
            logger.error(f"❌ Error evaluating tests: {e}")
            return 0.0

    def evaluate_code_quality(self, worktree_path: Path) -> float:
        """
        コード品質を評価（静的解析）

        Returns:
            float: スコア（0-100）
        """
        try:
            # ESLintまたはPylintなどを実行
            result = subprocess.run(
                ["npx", "eslint", "src/", "--format", "json"],
                cwd=worktree_path,
                capture_output=True,
                text=True,
                timeout=60
            )

            if result.stdout:
                lint_data = json.loads(result.stdout)
                total_issues = sum(
                    len(file.get('messages', []))
                    for file in lint_data
                )

                # ファイル数を取得
                src_files = list((worktree_path / "src").rglob("*.js")) + \
                            list((worktree_path / "src").rglob("*.ts"))
                num_files = len(src_files)

                if num_files > 0:
                    issues_per_file = total_issues / num_files
                    # 1ファイルあたり5問題以下なら高スコア
                    score = max(0, 100 - (issues_per_file * 10))
                    logger.info(f"✅ Code quality score: {score:.1f} (issues: {total_issues})")
                    return score
                else:
                    return 70.0  # デフォルト

            else:
                logger.warning("⚠️ Linting skipped (no output)")
                return 70.0

        except Exception as e:
            logger.warning(f"⚠️ Code quality check failed: {e}")
            return 70.0  # エラー時はデフォルトスコア

    def evaluate_performance(self, worktree_path: Path) -> float:
        """
        パフォーマンスを評価（ベンチマーク）

        Returns:
            float: スコア（0-100）
        """
        try:
            # ベンチマークファイルを確認
            benchmark_file = worktree_path / "benchmark-results.json"

            if not benchmark_file.exists():
                # ベンチマークを実行
                result = subprocess.run(
                    ["npm", "run", "benchmark"],
                    cwd=worktree_path,
                    capture_output=True,
                    text=True,
                    timeout=120
                )

                if result.returncode == 0:
                    # 結果ファイルを再確認
                    if benchmark_file.exists():
                        with open(benchmark_file) as f:
                            bench_data = json.load(f)
                            avg_response_time = bench_data.get('avg_response_time_ms', 1000)

                            # 100ms以下なら満点、1000ms以上なら0点
                            if avg_response_time <= 100:
                                score = 100
                            elif avg_response_time >= 1000:
                                score = 0
                            else:
                                score = 100 - ((avg_response_time - 100) / 9)

                            logger.info(f"✅ Performance score: {score:.1f} (avg: {avg_response_time}ms)")
                            return score
                    else:
                        logger.warning("⚠️ Benchmark file not found after execution")
                        return 70.0
                else:
                    logger.warning("⚠️ Benchmark execution failed")
                    return 70.0

            else:
                # 既存の結果を読み込み
                with open(benchmark_file) as f:
                    bench_data = json.load(f)
                    avg_response_time = bench_data.get('avg_response_time_ms', 1000)
                    if avg_response_time <= 100:
                        return 100
                    elif avg_response_time >= 1000:
                        return 0
                    else:
                        return 100 - ((avg_response_time - 100) / 9)

        except Exception as e:
            logger.warning(f"⚠️ Performance evaluation failed: {e}")
            return 70.0

    def evaluate_security(self, worktree_path: Path) -> float:
        """
        セキュリティを評価（脆弱性スキャン）

        Returns:
            float: スコア（0-100）
        """
        try:
            # npm audit を実行
            result = subprocess.run(
                ["npm", "audit", "--json"],
                cwd=worktree_path,
                capture_output=True,
                text=True,
                timeout=60
            )

            if result.stdout:
                audit_data = json.loads(result.stdout)
                vulnerabilities = audit_data.get('metadata', {}).get('vulnerabilities', {})

                critical = vulnerabilities.get('critical', 0)
                high = vulnerabilities.get('high', 0)
                moderate = vulnerabilities.get('moderate', 0)
                low = vulnerabilities.get('low', 0)

                # スコア計算（critical: -20, high: -10, moderate: -5, low: -2）
                score = 100 - (critical * 20 + high * 10 + moderate * 5 + low * 2)
                score = max(0, score)

                logger.info(f"✅ Security score: {score:.1f} (critical: {critical}, high: {high})")
                return score
            else:
                logger.warning("⚠️ Security audit skipped")
                return 80.0

        except Exception as e:
            logger.warning(f"⚠️ Security evaluation failed: {e}")
            return 80.0

    def evaluate_simplicity(self, worktree_path: Path) -> float:
        """
        シンプルさを評価（コード行数、複雑度）

        Returns:
            float: スコア（0-100）
        """
        try:
            src_dir = worktree_path / "src"
            if not src_dir.exists():
                return 70.0

            # 行数をカウント
            total_lines = 0
            for file in src_dir.rglob("*.js"):
                with open(file) as f:
                    total_lines += len(f.readlines())
            for file in src_dir.rglob("*.ts"):
                with open(file) as f:
                    total_lines += len(f.readlines())

            # 1000行以下なら満点、5000行以上なら0点
            if total_lines <= 1000:
                score = 100
            elif total_lines >= 5000:
                score = 0
            else:
                score = 100 - ((total_lines - 1000) / 40)

            logger.info(f"✅ Simplicity score: {score:.1f} (lines: {total_lines})")
            return max(0, score)

        except Exception as e:
            logger.warning(f"⚠️ Simplicity evaluation failed: {e}")
            return 70.0

    def evaluate_worktree(
        self,
        worktree_path: Path,
        criteria: EvaluationCriteria
    ) -> WorktreeScore:
        """
        worktreeを総合評価

        Args:
            worktree_path: 評価対象のworktreeパス
            criteria: 評価基準

        Returns:
            WorktreeScore: 評価結果
        """
        logger.info(f"\n📊 Evaluating: {worktree_path.name}")
        logger.info("=" * 60)

        # 各項目を評価
        test_score = self.evaluate_test_pass_rate(worktree_path)
        quality_score = self.evaluate_code_quality(worktree_path)
        perf_score = self.evaluate_performance(worktree_path)
        security_score = self.evaluate_security(worktree_path)
        simplicity_score = self.evaluate_simplicity(worktree_path)

        # 加重平均で総合スコア計算
        total_score = (
            test_score * criteria.test_pass_rate +
            quality_score * criteria.code_quality +
            perf_score * criteria.performance +
            security_score * criteria.security +
            simplicity_score * criteria.simplicity
        )

        result = WorktreeScore(
            worktree_path=str(worktree_path),
            total_score=total_score,
            test_pass_rate=test_score,
            code_quality=quality_score,
            performance=perf_score,
            security=security_score,
            simplicity=simplicity_score,
            details={
                "test_pass_rate": f"{test_score:.1f}",
                "code_quality": f"{quality_score:.1f}",
                "performance": f"{perf_score:.1f}",
                "security": f"{security_score:.1f}",
                "simplicity": f"{simplicity_score:.1f}"
            }
        )

        logger.info(f"\n✅ Total Score: {total_score:.1f}/100")
        logger.info("=" * 60)

        return result

    def select_best_worktree(
        self,
        worktree_names: List[str],
        criteria: Optional[EvaluationCriteria] = None
    ) -> tuple[str, WorktreeScore]:
        """
        複数のworktreeから最良を自動選択

        Args:
            worktree_names: 評価対象のworktree名のリスト
            criteria: 評価基準（省略時はデフォルト）

        Returns:
            tuple: (選択されたworktree名, 評価結果)
        """
        if criteria is None:
            criteria = EvaluationCriteria()

        results = {}

        logger.info("\n🚀 Starting autonomous evaluation...")
        logger.info(f"📋 Evaluating {len(worktree_names)} worktrees")

        for wt_name in worktree_names:
            wt_path = self.worktrees_dir / wt_name
            if wt_path.exists():
                score_result = self.evaluate_worktree(wt_path, criteria)
                results[wt_name] = score_result
            else:
                logger.warning(f"⚠️ Worktree not found: {wt_name}")

        if not results:
            raise ValueError("No valid worktrees found for evaluation")

        # 最高スコアを選択
        best_name = max(results, key=lambda k: results[k].total_score)
        best_score = results[best_name]

        logger.info("\n" + "=" * 60)
        logger.info("🏆 EVALUATION RESULTS")
        logger.info("=" * 60)

        for name, score in sorted(results.items(), key=lambda x: x[1].total_score, reverse=True):
            logger.info(f"{name}: {score.total_score:.1f}/100")

        logger.info("\n✅ SELECTED: " + best_name)
        logger.info(f"   Score: {best_score.total_score:.1f}/100")
        logger.info("=" * 60)

        # 結果をJSONで保存
        report_path = self.project_path / "EVALUATION_REPORT.json"
        with open(report_path, 'w') as f:
            json.dump({
                "selected": best_name,
                "results": {
                    name: {
                        "total_score": score.total_score,
                        "details": score.details
                    }
                    for name, score in results.items()
                },
                "criteria": {
                    "test_pass_rate": criteria.test_pass_rate,
                    "code_quality": criteria.code_quality,
                    "performance": criteria.performance,
                    "security": criteria.security,
                    "simplicity": criteria.simplicity
                }
            }, f, indent=2)

        logger.info(f"\n📄 Evaluation report saved: {report_path}")

        return best_name, best_score

    def merge_to_main_and_sync(self, selected_worktree: str, phase: str = None, skip_file_check: bool = False) -> bool:
        """選択されたworktreeをmainにマージし、他のworktreeに同期

        Args:
            selected_worktree: 選択されたworktree名（例: "phase1-planning-a"）
            phase: フェーズ名（例: "phase1"）- 自動判定も可能
            skip_file_check: 重要ファイルチェックをスキップするか（Phase 1-Aでは True）

        Returns:
            bool: 成功したらTrue
        """
        try:
            # フェーズを自動判定
            if phase is None:
                if 'phase1' in selected_worktree:
                    phase = 'phase1'
                elif 'phase2' in selected_worktree:
                    phase = 'phase2'
                elif 'phase4' in selected_worktree:
                    phase = 'phase4'

            logger.info("\n" + "=" * 60)
            logger.info(f"🔄 Merging {selected_worktree} to main...")
            logger.info("=" * 60)

            # ブランチ名を推定（worktree名からphaseN-プレフィックスを除去）
            branch_name = selected_worktree
            for prefix in ['phase1-', 'phase2-', 'phase3-', 'phase4-', 'phase5-']:
                branch_name = branch_name.replace(prefix, 'phase/')

            # mainにマージ（M4 Mac対応）
            git_cmd = '/usr/bin/git' if os.path.exists('/usr/bin/git') else 'git'
            subprocess.run(
                [git_cmd, 'merge', '--no-edit', branch_name],
                cwd=self.project_path,
                check=True
            )
            logger.info(f"✅ Merged {branch_name} to main")

            # Phase別の重要ファイル確認（skip_file_check=Trueの場合はスキップ）
            if not skip_file_check:
                # Phase別に確認すべきファイルを定義
                phase_required_files = {
                    'phase1': {
                        'required': ['REQUIREMENTS.md', 'SPEC.md'],  # Phase 1-A完了時点での必須
                        'optional': ['IMAGE_PROMPTS.json', 'AUDIO_PROMPTS.json', 'TECH_STACK.md', 'WBS.json']  # Phase 1-B完了時点
                    },
                    'phase2': {
                        'required': ['src/', 'index.html'],
                        'optional': ['tests/', 'assets/']
                    },
                    'phase4': {
                        'required': [],
                        'optional': ['benchmark-results.json', 'coverage/']
                    }
                }

                if phase in phase_required_files:
                    config = phase_required_files[phase]
                    missing_required = []
                    missing_optional = []

                    for file in config.get('required', []):
                        file_path = self.project_path / file
                        if file_path.exists():
                            logger.info(f"  ✅ {file} - 存在確認（必須）")
                        else:
                            missing_required.append(file)
                            logger.error(f"  ❌ {file} - 必須ファイルが見つかりません")

                    for file in config.get('optional', []):
                        file_path = self.project_path / file
                        if file_path.exists():
                            logger.info(f"  ✅ {file} - 存在確認（オプション）")
                        else:
                            missing_optional.append(file)
                            logger.info(f"  ℹ️  {file} - オプションファイル（未生成）")

                    if missing_required:
                        logger.error(f"\n❌ 必須ファイルが不足しています: {', '.join(missing_required)}")
                        logger.error("   → このPhaseの成果物が不完全です。再実行を検討してください。")

                    if missing_optional:
                        logger.info(f"\nℹ️  オプションファイル（後続Phaseで生成予定）: {', '.join(missing_optional)}")

            # すべてのworktreeに同期
            logger.info("\n🔄 Syncing to all worktrees...")
            sync_success = 0
            sync_failed = 0

            if self.worktrees_dir.exists():
                for worktree in self.worktrees_dir.iterdir():
                    if worktree.is_dir() and worktree.name != selected_worktree:
                        try:
                            # git merge main を各worktreeで実行
                            subprocess.run(
                                [git_cmd, 'merge', '--no-edit', 'main'],
                                cwd=worktree,
                                check=True,
                                capture_output=True
                            )
                            logger.info(f"  ✅ Synced to {worktree.name}")
                            sync_success += 1
                        except subprocess.CalledProcessError:
                            logger.warning(f"  ⚠️  Failed to sync to {worktree.name}")
                            sync_failed += 1

            logger.info(f"\n✅ Merge and sync completed! (Success: {sync_success}, Failed: {sync_failed})")
            return True

        except subprocess.CalledProcessError as e:
            logger.error(f"❌ Merge failed: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Unexpected error: {e}")
            return False


def main():
    """CLI エントリーポイント"""
    import sys

    if len(sys.argv) < 2:
        print("Usage: python3 autonomous_evaluator.py <project_path> [worktree1] [worktree2] ... [options]")
        print("\nOptions:")
        print("  --auto-merge         選択されたworktreeを自動でmainにマージし全worktreeに同期")
        print("  --skip-file-check    Phase別の重要ファイルチェックをスキップ（Phase 1前半用）")
        print("  --phase=<phase>      フェーズを明示的に指定（phase1, phase2, phase4）")
        print("\nExample:")
        print("  python3 autonomous_evaluator.py ~/Desktop/AI-Apps/myapp-agent phase2-impl-prototype-a phase2-impl-prototype-b")
        print("  python3 autonomous_evaluator.py . phase1-planning-a phase1-planning-b --auto-merge")
        print("  python3 autonomous_evaluator.py . phase1-planning-a phase1-planning-b --auto-merge --skip-file-check")
        sys.exit(1)

    # オプションを抽出
    args = sys.argv[1:]
    options = [a for a in args if a.startswith('--')]
    non_options = [a for a in args if not a.startswith('--')]

    project_path = Path(non_options[0]) if non_options else Path('.')
    worktree_names = non_options[1:] if len(non_options) > 1 else []

    # オプション解析
    auto_merge = '--auto-merge' in options
    skip_file_check = '--skip-file-check' in options
    phase = None
    for opt in options:
        if opt.startswith('--phase='):
            phase = opt.split('=')[1]

    # worktree_namesからオプションを除外
    worktree_names = [w for w in worktree_names if not w.startswith('--')]

    if not worktree_names:
        # worktrees/配下の全フォルダを評価
        worktrees_dir = project_path / "worktrees"
        if worktrees_dir.exists():
            worktree_names = [d.name for d in worktrees_dir.iterdir() if d.is_dir()]

    evaluator = AutonomousEvaluator(project_path)
    best_name, best_score = evaluator.select_best_worktree(worktree_names)

    print(f"\n🎉 Best worktree: {best_name}")
    print(f"   Total score: {best_score.total_score:.1f}/100")

    # 自動マージ・同期（--auto-mergeオプション）
    if auto_merge:
        print("\n🔄 Auto-merge enabled - merging to main and syncing...")
        if skip_file_check:
            print("ℹ️  File check skipped (--skip-file-check)")
        evaluator.merge_to_main_and_sync(best_name, phase=phase, skip_file_check=skip_file_check)


if __name__ == "__main__":
    main()
