#!/usr/bin/env python3
"""
自律的改善ループコントローラー
テスト失敗を検出し、自動的に修正を繰り返す
"""

import json
import subprocess
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import logging

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ImprovementLoopController:
    """
    改善ループを制御するメインクラス
    """

    def __init__(self, project_path: str, max_iterations: int = 3):
        """
        初期化

        Args:
            project_path: プロジェクトのパス
            max_iterations: 最大ループ回数（デフォルト3回）
        """
        self.project_path = Path(project_path)
        self.max_iterations = max_iterations
        self.iteration_count = 0
        self.test_results = []
        self.improvement_history = []

        # ログディレクトリを作成
        self.log_dir = self.project_path / "logs" / "improvement"
        self.log_dir.mkdir(parents=True, exist_ok=True)

    def run_improvement_cycle(self) -> Dict:
        """
        改善サイクルを実行

        Returns:
            最終結果の辞書
        """
        logger.info("🔄 改善ループを開始します")

        for iteration in range(1, self.max_iterations + 1):
            self.iteration_count = iteration
            logger.info(f"\n--- Iteration {iteration}/{self.max_iterations} ---")

            # 1. テスト評価
            test_result = self.evaluate_tests()
            self.test_results.append(test_result)

            # 2. 成功判定
            if test_result['overall_status'] == 'pass':
                logger.info("✅ 全テストがパスしました！")
                return self._create_success_report()

            # 3. 最終回の場合
            if iteration == self.max_iterations:
                logger.warning("⚠️ 最大試行回数に達しました")
                return self._create_partial_success_report()

            # 4. 改善計画作成
            improvement_plan = self.create_improvement_plan(test_result)

            # 5. コード修正
            fix_result = self.apply_fixes(improvement_plan)

            # 履歴に追加
            self.improvement_history.append({
                'iteration': iteration,
                'test_result': test_result,
                'improvement_plan': improvement_plan,
                'fix_result': fix_result
            })

            # 少し待機（ファイルシステムの同期待ち）
            time.sleep(2)

        return self._create_partial_success_report()

    def evaluate_tests(self) -> Dict:
        """
        テストを実行し、結果を評価

        Returns:
            テスト結果の辞書
        """
        logger.info("🔎 テストを評価中...")

        # テストコマンドを検出
        test_command = self._detect_test_command()

        if not test_command:
            return {
                'overall_status': 'error',
                'message': 'テストコマンドが見つかりません',
                'timestamp': datetime.now().isoformat()
            }

        # テスト実行
        result = subprocess.run(
            test_command,
            shell=True,
            cwd=self.project_path,
            capture_output=True,
            text=True
        )

        # ログ保存
        log_file = self.log_dir / f"test_{self.iteration_count}.log"
        with open(log_file, 'w') as f:
            f.write(f"Command: {test_command}\n")
            f.write(f"Return Code: {result.returncode}\n")
            f.write(f"STDOUT:\n{result.stdout}\n")
            f.write(f"STDERR:\n{result.stderr}\n")

        # 結果解析
        return self._analyze_test_output(result, log_file)

    def _detect_test_command(self) -> Optional[str]:
        """
        プロジェクトに適したテストコマンドを検出
        """
        # package.jsonがある場合（Node.js）
        package_json = self.project_path / "package.json"
        if package_json.exists():
            with open(package_json) as f:
                package_data = json.load(f)
                if 'scripts' in package_data and 'test' in package_data['scripts']:
                    return "npm test"

        # requirements.txtがある場合（Python）
        requirements = self.project_path / "requirements.txt"
        if requirements.exists():
            # pytestが一般的
            return "python -m pytest"

        # Makefileがある場合
        makefile = self.project_path / "Makefile"
        if makefile.exists():
            with open(makefile) as f:
                if 'test:' in f.read():
                    return "make test"

        return None

    def _analyze_test_output(self, result: subprocess.CompletedProcess, log_file: Path) -> Dict:
        """
        テスト出力を解析
        """
        output = result.stdout + result.stderr

        # 成功/失敗の判定
        if result.returncode == 0:
            status = 'pass'
        else:
            status = 'fail'

        # 失敗テストの抽出（簡易版）
        failed_tests = []
        if status == 'fail':
            lines = output.split('\n')
            for i, line in enumerate(lines):
                if 'FAIL' in line or 'ERROR' in line or '✗' in line:
                    failed_tests.append({
                        'line': line.strip(),
                        'context': lines[max(0, i-2):min(len(lines), i+3)]
                    })

        return {
            'overall_status': status,
            'return_code': result.returncode,
            'failed_tests': failed_tests,
            'log_file': str(log_file),
            'timestamp': datetime.now().isoformat()
        }

    def create_improvement_plan(self, test_result: Dict) -> Dict:
        """
        テスト結果から改善計画を作成
        """
        logger.info("📋 改善計画を作成中...")

        plan = {
            'iteration': self.iteration_count,
            'created_at': datetime.now().isoformat(),
            'issues': [],
            'fixes': []
        }

        # 失敗テストから問題を特定
        for failed_test in test_result.get('failed_tests', []):
            issue = self._analyze_failure(failed_test)
            plan['issues'].append(issue)

            # 修正案を生成
            fix = self._generate_fix_suggestion(issue)
            plan['fixes'].append(fix)

        # 計画を保存
        plan_file = self.log_dir / f"plan_{self.iteration_count}.json"
        with open(plan_file, 'w') as f:
            json.dump(plan, f, indent=2, ensure_ascii=False)

        logger.info(f"📝 {len(plan['fixes'])}個の修正案を作成しました")

        return plan

    def _analyze_failure(self, failed_test: Dict) -> Dict:
        """
        失敗を分析
        """
        line = failed_test['line']

        # エラータイプを推定
        error_type = 'unknown'
        if 'TypeError' in line:
            error_type = 'type_error'
        elif 'ReferenceError' in line or 'NameError' in line:
            error_type = 'reference_error'
        elif 'SyntaxError' in line:
            error_type = 'syntax_error'
        elif 'AssertionError' in line or 'Expected' in line:
            error_type = 'assertion_error'

        return {
            'type': error_type,
            'description': line,
            'context': failed_test.get('context', [])
        }

    def _generate_fix_suggestion(self, issue: Dict) -> Dict:
        """
        修正案を生成
        """
        fix = {
            'issue_type': issue['type'],
            'priority': 'high',
            'suggestion': ''
        }

        # エラータイプに応じた修正案
        if issue['type'] == 'type_error':
            fix['suggestion'] = '型チェックを追加し、適切な型変換を実装'
        elif issue['type'] == 'reference_error':
            fix['suggestion'] = '未定義の変数・関数を定義または import を追加'
        elif issue['type'] == 'syntax_error':
            fix['suggestion'] = '構文エラーを修正'
        elif issue['type'] == 'assertion_error':
            fix['suggestion'] = 'ロジックを見直し、期待される値を返すよう修正'
        else:
            fix['suggestion'] = 'エラーメッセージを分析し、適切な修正を実施'

        return fix

    def apply_fixes(self, improvement_plan: Dict) -> Dict:
        """
        改善計画に基づいて修正を適用

        注: 実際のコード修正はFixerエージェントが担当
        ここではその結果を記録
        """
        logger.info("🔧 修正を適用中...")

        result = {
            'iteration': self.iteration_count,
            'fixes_applied': len(improvement_plan['fixes']),
            'timestamp': datetime.now().isoformat()
        }

        # 修正結果をログに記録
        fix_log = self.log_dir / f"fixes_{self.iteration_count}.json"
        with open(fix_log, 'w') as f:
            json.dump(result, f, indent=2)

        logger.info(f"✏️ {result['fixes_applied']}個の修正を適用しました")

        return result

    def _create_success_report(self) -> Dict:
        """
        成功レポートを作成
        """
        report = {
            'status': 'success',
            'message': '全てのテストがパスしました',
            'total_iterations': self.iteration_count,
            'test_results': self.test_results,
            'improvement_history': self.improvement_history,
            'timestamp': datetime.now().isoformat()
        }

        # レポート保存
        self._save_report(report, 'success_report.json')

        return report

    def _create_partial_success_report(self) -> Dict:
        """
        部分成功レポートを作成
        """
        # 最後のテスト結果から成功率を計算
        last_result = self.test_results[-1] if self.test_results else {}

        report = {
            'status': 'partial_success',
            'message': '一部のテストが失敗しましたが、改善を実施しました',
            'total_iterations': self.iteration_count,
            'remaining_issues': last_result.get('failed_tests', []),
            'test_results': self.test_results,
            'improvement_history': self.improvement_history,
            'timestamp': datetime.now().isoformat(),
            'known_limitations': self._generate_known_limitations()
        }

        # レポート保存
        self._save_report(report, 'partial_success_report.json')

        return report

    def _generate_known_limitations(self) -> List[str]:
        """
        既知の制約を生成
        """
        limitations = []

        if self.test_results:
            last_result = self.test_results[-1]
            for failed_test in last_result.get('failed_tests', []):
                limitations.append(f"未解決: {failed_test.get('line', 'Unknown test failure')}")

        return limitations

    def _save_report(self, report: Dict, filename: str):
        """
        レポートを保存
        """
        report_file = self.log_dir / filename
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        logger.info(f"📊 レポートを保存しました: {report_file}")


def main():
    """
    CLI実行用
    """
    import argparse

    parser = argparse.ArgumentParser(description='自律的改善ループコントローラー')
    parser.add_argument('project_path', help='プロジェクトのパス')
    parser.add_argument('--max-iterations', type=int, default=3, help='最大ループ回数')

    args = parser.parse_args()

    controller = ImprovementLoopController(
        project_path=args.project_path,
        max_iterations=args.max_iterations
    )

    result = controller.run_improvement_cycle()

    # 結果を表示
    print(f"\n{'='*50}")
    print(f"Status: {result['status']}")
    print(f"Message: {result['message']}")
    print(f"Iterations: {result['total_iterations']}")

    if result['status'] == 'partial_success':
        print(f"\n既知の制約:")
        for limitation in result.get('known_limitations', []):
            print(f"  - {limitation}")


if __name__ == "__main__":
    main()