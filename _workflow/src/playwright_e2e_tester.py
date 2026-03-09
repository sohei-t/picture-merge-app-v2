#!/usr/bin/env python3
"""
Playwright E2Eテスター - Playwright MCPを使用した自動E2Eテスト

目的:
- すべてのユーザーフローを実際のブラウザで検証
- 全機能が正常に動作するまで繰り返しテスト
- Playwright MCPを活用してテストを自動生成・実行

使用方法:
  python3 _workflow/src/playwright_e2e_tester.py <app_url> [--scenarios <scenarios_file>]

例:
  python3 _workflow/src/playwright_e2e_tester.py http://localhost:3000
  python3 _workflow/src/playwright_e2e_tester.py http://localhost:8080 --scenarios e2e_scenarios.json
"""

import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PlaywrightE2ETester:
    """Playwright MCPを使用したE2Eテスター"""

    def __init__(self, app_url: str, project_path: Path = Path(".")):
        self.app_url = app_url
        self.project_path = Path(project_path)
        self.scenarios_file = self.project_path / "E2E_SCENARIOS.json"
        self.results_file = self.project_path / "E2E_TEST_RESULTS.json"

    def generate_scenarios(self, project_info: Dict) -> List[Dict]:
        """プロジェクト情報からE2Eテストシナリオを自動生成

        Args:
            project_info: PROJECT_INFO.yamlから読み込んだプロジェクト情報

        Returns:
            List[Dict]: テストシナリオのリスト
        """
        project_name = project_info.get('name', 'App')
        project_type = project_info.get('type', 'web')

        logger.info(f"🎯 Generating E2E scenarios for: {project_name} ({project_type})")

        scenarios = []

        # 基本シナリオ（全アプリ共通）
        scenarios.append({
            "name": "Basic Page Load",
            "description": "アプリケーションが正常に読み込まれる",
            "steps": [
                {"action": "goto", "url": self.app_url},
                {"action": "wait_for_load_state", "state": "networkidle"},
                {"action": "assert_title_contains", "text": project_name}
            ]
        })

        # プロジェクトタイプ別シナリオ
        if 'todo' in project_name.lower() or 'task' in project_name.lower():
            scenarios.extend(self._generate_todo_scenarios())
        elif 'game' in project_type.lower() or 'ゲーム' in project_name.lower():
            scenarios.extend(self._generate_game_scenarios())
        elif 'chat' in project_name.lower():
            scenarios.extend(self._generate_chat_scenarios())
        elif 'calculator' in project_name.lower():
            scenarios.extend(self._generate_calculator_scenarios())
        else:
            scenarios.extend(self._generate_generic_web_scenarios())

        # シナリオをファイルに保存
        with open(self.scenarios_file, 'w', encoding='utf-8') as f:
            json.dump({"scenarios": scenarios}, f, indent=2, ensure_ascii=False)

        logger.info(f"✅ Generated {len(scenarios)} scenarios: {self.scenarios_file}")
        return scenarios

    def _generate_todo_scenarios(self) -> List[Dict]:
        """TODOアプリ用シナリオ"""
        return [
            {
                "name": "Add New Todo",
                "description": "新しいTODOを追加できる",
                "steps": [
                    {"action": "goto", "url": self.app_url},
                    {"action": "fill", "selector": "input[type='text'], input[placeholder*='todo' i]", "text": "Test Task"},
                    {"action": "click", "selector": "button:has-text('Add'), button:has-text('追加')"},
                    {"action": "wait_for_selector", "selector": "text=Test Task"},
                    {"action": "assert_text_visible", "text": "Test Task"}
                ]
            },
            {
                "name": "Complete Todo",
                "description": "TODOを完了にできる",
                "steps": [
                    {"action": "goto", "url": self.app_url},
                    {"action": "fill", "selector": "input[type='text']", "text": "Complete Me"},
                    {"action": "click", "selector": "button:has-text('Add')"},
                    {"action": "click", "selector": "input[type='checkbox']:near(text='Complete Me')"},
                    {"action": "assert_element_has_class", "selector": "text=Complete Me", "class": "completed"}
                ]
            },
            {
                "name": "Delete Todo",
                "description": "TODOを削除できる",
                "steps": [
                    {"action": "goto", "url": self.app_url},
                    {"action": "fill", "selector": "input[type='text']", "text": "Delete Me"},
                    {"action": "click", "selector": "button:has-text('Add')"},
                    {"action": "click", "selector": "button:has-text('Delete'):near(text='Delete Me'), button:has-text('削除'):near(text='Delete Me')"},
                    {"action": "assert_text_not_visible", "text": "Delete Me"}
                ]
            }
        ]

    def _generate_game_scenarios(self) -> List[Dict]:
        """ゲームアプリ用シナリオ"""
        return [
            {
                "name": "Game Start",
                "description": "ゲームを開始できる",
                "steps": [
                    {"action": "goto", "url": self.app_url},
                    {"action": "click", "selector": "button:has-text('Start'), button:has-text('スタート'), button:has-text('開始')"},
                    {"action": "wait_for_selector", "selector": "canvas, #game-canvas"},
                    {"action": "assert_element_visible", "selector": "canvas, #game-canvas"}
                ]
            },
            {
                "name": "Player Controls",
                "description": "プレイヤー操作が動作する",
                "steps": [
                    {"action": "goto", "url": self.app_url},
                    {"action": "click", "selector": "button:has-text('Start')"},
                    {"action": "keyboard_press", "key": "ArrowRight"},
                    {"action": "keyboard_press", "key": "ArrowLeft"},
                    {"action": "keyboard_press", "key": "Space"},
                    {"action": "wait", "ms": 1000}
                ]
            },
            {
                "name": "Game Over Flow",
                "description": "ゲームオーバーからリスタートできる",
                "steps": [
                    {"action": "goto", "url": self.app_url},
                    {"action": "click", "selector": "button:has-text('Start')"},
                    {"action": "wait_for_selector", "selector": "text=Game Over, text=ゲームオーバー", "timeout": 60000},
                    {"action": "click", "selector": "button:has-text('Restart'), button:has-text('再開始')"},
                    {"action": "assert_element_visible", "selector": "canvas"}
                ]
            }
        ]

    def _generate_chat_scenarios(self) -> List[Dict]:
        """チャットアプリ用シナリオ"""
        return [
            {
                "name": "Send Message",
                "description": "メッセージを送信できる",
                "steps": [
                    {"action": "goto", "url": self.app_url},
                    {"action": "fill", "selector": "input[type='text'], textarea", "text": "Hello World"},
                    {"action": "click", "selector": "button:has-text('Send'), button:has-text('送信')"},
                    {"action": "wait_for_selector", "selector": "text=Hello World"},
                    {"action": "assert_text_visible", "text": "Hello World"}
                ]
            }
        ]

    def _generate_calculator_scenarios(self) -> List[Dict]:
        """計算機アプリ用シナリオ"""
        return [
            {
                "name": "Basic Calculation",
                "description": "基本的な計算ができる",
                "steps": [
                    {"action": "goto", "url": self.app_url},
                    {"action": "click", "selector": "button:has-text('2')"},
                    {"action": "click", "selector": "button:has-text('+')"},
                    {"action": "click", "selector": "button:has-text('3')"},
                    {"action": "click", "selector": "button:has-text('=')"},
                    {"action": "assert_text_visible", "text": "5"}
                ]
            }
        ]

    def _generate_generic_web_scenarios(self) -> List[Dict]:
        """一般的なWebアプリ用シナリオ"""
        return [
            {
                "name": "Navigation",
                "description": "ページ間のナビゲーションが動作する",
                "steps": [
                    {"action": "goto", "url": self.app_url},
                    {"action": "click", "selector": "a:has-text('About'), a:has-text('について')"},
                    {"action": "wait_for_url", "pattern": "**/about**"},
                    {"action": "go_back"},
                    {"action": "wait_for_url", "pattern": self.app_url}
                ]
            },
            {
                "name": "Form Submission",
                "description": "フォーム送信が動作する",
                "steps": [
                    {"action": "goto", "url": self.app_url},
                    {"action": "fill", "selector": "input[type='text']:first", "text": "Test Input"},
                    {"action": "click", "selector": "button[type='submit'], input[type='submit']"},
                    {"action": "wait_for_load_state", "state": "networkidle"}
                ]
            }
        ]

    def run_scenarios_with_playwright_mcp(self, scenarios: List[Dict]) -> Dict:
        """Playwright MCPを使用してシナリオを実行

        注意: この関数はClaude Codeの環境で実行されることを想定
        Playwright MCPツールを直接呼び出します
        """
        logger.info("\n" + "=" * 60)
        logger.info("🎭 Running E2E tests with Playwright MCP")
        logger.info("=" * 60)

        results = {
            "total": len(scenarios),
            "passed": 0,
            "failed": 0,
            "errors": [],
            "details": []
        }

        for i, scenario in enumerate(scenarios):
            logger.info(f"\n📋 Scenario {i+1}/{len(scenarios)}: {scenario['name']}")
            logger.info(f"   {scenario['description']}")

            try:
                # Claude Codeの環境でPlaywright MCPツールを使用
                # 注意: この部分はClaude Codeによって実行される必要があります
                result = self._execute_scenario_steps(scenario)

                if result['success']:
                    results['passed'] += 1
                    logger.info(f"   ✅ PASSED")
                else:
                    results['failed'] += 1
                    results['errors'].append({
                        "scenario": scenario['name'],
                        "error": result.get('error', 'Unknown error')
                    })
                    logger.error(f"   ❌ FAILED: {result.get('error')}")

                results['details'].append({
                    "scenario": scenario['name'],
                    "success": result['success'],
                    "duration_ms": result.get('duration_ms', 0),
                    "error": result.get('error')
                })

            except Exception as e:
                results['failed'] += 1
                results['errors'].append({
                    "scenario": scenario['name'],
                    "error": str(e)
                })
                logger.error(f"   ❌ ERROR: {e}")

        # 結果を保存
        with open(self.results_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)

        logger.info("\n" + "=" * 60)
        logger.info(f"📊 E2E Test Results")
        logger.info("=" * 60)
        logger.info(f"Total: {results['total']}")
        logger.info(f"✅ Passed: {results['passed']}")
        logger.info(f"❌ Failed: {results['failed']}")
        logger.info(f"Pass Rate: {results['passed']/results['total']*100:.1f}%")
        logger.info("=" * 60)

        return results

    def _execute_scenario_steps(self, scenario: Dict) -> Dict:
        """シナリオのステップを実行

        注意: この関数はClaude Codeによって呼び出され、
        Playwright MCPツールを使用してブラウザ操作を実行します

        Returns:
            Dict: {'success': bool, 'error': str, 'duration_ms': int}
        """
        # この関数はClaude Codeによってオーバーライドされることを想定
        # ここではダミー実装を提供
        logger.warning("⚠️  This function should be called by Claude Code with Playwright MCP access")

        return {
            "success": False,
            "error": "Playwright MCP is not available in standalone execution. Run via Claude Code.",
            "duration_ms": 0
        }

    def generate_test_report_html(self) -> Path:
        """E2Eテスト結果のHTML レポートを生成"""
        if not self.results_file.exists():
            logger.error("❌ No test results found")
            return None

        with open(self.results_file, 'r', encoding='utf-8') as f:
            results = json.load(f)

        report_path = self.project_path / "E2E_TEST_REPORT.html"

        pass_rate = results['passed'] / results['total'] * 100 if results['total'] > 0 else 0
        status_color = "#4CAF50" if pass_rate >= 100 else "#FF9800" if pass_rate >= 70 else "#F44336"

        html_content = f"""<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>E2E Test Report</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background: #f5f5f5;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 20px;
        }}
        .stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-bottom: 20px;
        }}
        .stat-card {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .stat-value {{
            font-size: 2em;
            font-weight: bold;
            color: {status_color};
        }}
        .scenario-list {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .scenario-item {{
            padding: 15px;
            border-bottom: 1px solid #eee;
        }}
        .scenario-item:last-child {{
            border-bottom: none;
        }}
        .passed {{ color: #4CAF50; }}
        .failed {{ color: #F44336; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🎭 E2E Test Report</h1>
        <p>Playwright MCP による自動テスト結果</p>
    </div>

    <div class="stats">
        <div class="stat-card">
            <div class="stat-label">Total Tests</div>
            <div class="stat-value">{results['total']}</div>
        </div>
        <div class="stat-card">
            <div class="stat-label">✅ Passed</div>
            <div class="stat-value" style="color: #4CAF50">{results['passed']}</div>
        </div>
        <div class="stat-card">
            <div class="stat-label">❌ Failed</div>
            <div class="stat-value" style="color: #F44336">{results['failed']}</div>
        </div>
        <div class="stat-card">
            <div class="stat-label">Pass Rate</div>
            <div class="stat-value">{pass_rate:.1f}%</div>
        </div>
    </div>

    <div class="scenario-list">
        <h2>Test Scenarios</h2>
"""

        for detail in results.get('details', []):
            status_icon = "✅" if detail['success'] else "❌"
            status_class = "passed" if detail['success'] else "failed"
            error_info = f"<div style='color: #F44336; margin-top: 5px;'>Error: {detail['error']}</div>" if detail.get('error') else ""

            html_content += f"""
        <div class="scenario-item">
            <div class="{status_class}">
                {status_icon} <strong>{detail['scenario']}</strong>
                <span style="float: right; color: #999;">{detail.get('duration_ms', 0)}ms</span>
            </div>
            {error_info}
        </div>
"""

        html_content += """
    </div>
</body>
</html>
"""

        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(html_content)

        logger.info(f"✅ HTML report generated: {report_path}")
        return report_path


def main():
    """CLI エントリーポイント"""
    if len(sys.argv) < 2:
        print("Usage: python3 _workflow/src/playwright_e2e_tester.py <app_url> [--scenarios <file>]")
        print("\nExample:")
        print("  python3 _workflow/src/playwright_e2e_tester.py http://localhost:3000")
        sys.exit(1)

    app_url = sys.argv[1]
    scenarios_file = None

    if '--scenarios' in sys.argv:
        idx = sys.argv.index('--scenarios')
        scenarios_file = sys.argv[idx + 1] if len(sys.argv) > idx + 1 else None

    tester = PlaywrightE2ETester(app_url)

    # PROJECT_INFO.yamlから情報を読み込み
    project_info_path = Path("PROJECT_INFO.yaml")
    if project_info_path.exists():
        import yaml
        with open(project_info_path, 'r') as f:
            data = yaml.safe_load(f)
            project_info = data.get('project', {})
    else:
        project_info = {'name': 'App', 'type': 'web'}

    # シナリオ生成
    scenarios = tester.generate_scenarios(project_info)

    print("\n" + "=" * 60)
    print("🎭 Playwright E2E Tester")
    print("=" * 60)
    print(f"App URL: {app_url}")
    print(f"Scenarios: {len(scenarios)}")
    print("=" * 60)
    print("\n⚠️  This script requires Playwright MCP to run tests.")
    print("Please execute via Claude Code with Playwright MCP enabled.")
    print("\nScenarios have been generated:")
    print(f"  {tester.scenarios_file}")
    print("\nTo run tests, use Claude Code and say:")
    print("  'Run E2E tests using Playwright MCP with E2E_SCENARIOS.json'")


if __name__ == '__main__':
    main()
