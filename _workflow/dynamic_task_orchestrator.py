#!/usr/bin/env python3
"""
動的タスク実行オーケストレーター
WBSに基づいて依存関係を考慮しながらタスクを動的に実行
"""

import json
import time
from datetime import datetime
from typing import List, Dict, Set, Optional
from collections import defaultdict
import subprocess

class DynamicTaskOrchestrator:
    """
    WBSベースの動的タスク実行エンジン
    """

    def __init__(self, wbs_file: str):
        """
        初期化
        Args:
            wbs_file: WBS定義ファイルのパス
        """
        with open(wbs_file, 'r', encoding='utf-8') as f:
            self.wbs = json.load(f)

        self.tasks = {task['id']: task for task in self.wbs['tasks']}
        self.completed_tasks: Set[str] = set()
        self.running_tasks: Dict[str, Dict] = {}
        self.failed_tasks: Set[str] = set()
        self.execution_log: List[Dict] = []

    def analyze_dependencies(self) -> Dict[str, List[str]]:
        """
        依存関係を解析してグラフを作成
        Returns:
            タスクIDをキー、依存先タスクIDのリストを値とする辞書
        """
        dep_graph = {}
        for task_id, task in self.tasks.items():
            dep_graph[task_id] = task['dependencies']
        return dep_graph

    def find_critical_path(self) -> List[str]:
        """
        クリティカルパスを特定
        Returns:
            クリティカルパス上のタスクIDのリスト
        """
        # 各タスクの最早開始時刻と最遅開始時刻を計算
        earliest_start = {}
        latest_start = {}

        # トポロジカルソート
        sorted_tasks = self.topological_sort()

        # 最早開始時刻を計算
        for task_id in sorted_tasks:
            task = self.tasks[task_id]
            if not task['dependencies']:
                earliest_start[task_id] = 0
            else:
                max_finish = 0
                for dep_id in task['dependencies']:
                    dep_task = self.tasks[dep_id]
                    finish_time = earliest_start[dep_id] + dep_task['estimated_hours']
                    max_finish = max(max_finish, finish_time)
                earliest_start[task_id] = max_finish

        # プロジェクト完了時刻
        project_duration = max(
            earliest_start[task_id] + self.tasks[task_id]['estimated_hours']
            for task_id in sorted_tasks
        )

        # 最遅開始時刻を計算（逆順）
        for task_id in reversed(sorted_tasks):
            task = self.tasks[task_id]
            # このタスクに依存するタスクを探す
            dependent_tasks = [
                t_id for t_id, t in self.tasks.items()
                if task_id in t['dependencies']
            ]

            if not dependent_tasks:
                # 終端タスク
                latest_start[task_id] = (
                    project_duration - task['estimated_hours']
                )
            else:
                min_start = float('inf')
                for dep_task_id in dependent_tasks:
                    min_start = min(min_start, latest_start[dep_task_id])
                latest_start[task_id] = min_start - task['estimated_hours']

        # クリティカルパス = 最早開始時刻 == 最遅開始時刻のタスク
        critical_path = [
            task_id for task_id in sorted_tasks
            if abs(earliest_start[task_id] - latest_start[task_id]) < 0.01
        ]

        return critical_path

    def topological_sort(self) -> List[str]:
        """
        タスクをトポロジカルソート
        Returns:
            依存関係を考慮した実行順序のタスクIDリスト
        """
        in_degree = defaultdict(int)
        for task_id, task in self.tasks.items():
            for dep_id in task['dependencies']:
                in_degree[dep_id] += 0  # 初期化
            in_degree[task_id] += len(task['dependencies'])

        queue = [
            task_id for task_id in self.tasks
            if in_degree[task_id] == 0
        ]
        sorted_tasks = []

        while queue:
            task_id = queue.pop(0)
            sorted_tasks.append(task_id)

            # このタスクに依存するタスクの入次数を減らす
            for other_id, other_task in self.tasks.items():
                if task_id in other_task['dependencies']:
                    in_degree[other_id] -= 1
                    if in_degree[other_id] == 0:
                        queue.append(other_id)

        return sorted_tasks

    def get_ready_tasks(self) -> List[str]:
        """
        実行可能なタスクを取得
        Returns:
            依存関係が満たされた実行可能なタスクIDのリスト
        """
        ready = []
        for task_id, task in self.tasks.items():
            if (task_id not in self.completed_tasks and
                task_id not in self.running_tasks and
                task_id not in self.failed_tasks):

                # 全ての依存タスクが完了しているか確認
                deps_satisfied = all(
                    dep_id in self.completed_tasks
                    for dep_id in task['dependencies']
                )

                if deps_satisfied:
                    ready.append(task_id)

        return ready

    def can_run_parallel(self, task_ids: List[str]) -> List[str]:
        """
        並列実行可能なタスクを選択
        Args:
            task_ids: 候補となるタスクIDのリスト
        Returns:
            並列実行可能なタスクIDのリスト
        """
        max_parallel = self.wbs['execution_rules']['max_parallel_tasks']
        current_running = len(self.running_tasks)
        available_slots = max_parallel - current_running

        if available_slots <= 0:
            return []

        # 優先度でソート
        priority_order = {'high': 3, 'medium': 2, 'low': 1}
        sorted_tasks = sorted(
            task_ids,
            key=lambda x: priority_order.get(
                self.tasks[x].get('priority', 'medium'), 2
            ),
            reverse=True
        )

        return sorted_tasks[:available_slots]

    def execute_task(self, task_id: str) -> Dict:
        """
        タスクを実行（実際にはサブエージェントを起動）
        Args:
            task_id: 実行するタスクID
        Returns:
            実行結果
        """
        task = self.tasks[task_id]
        print(f"\n🚀 Starting Task: {task_id} - {task['name']}")
        print(f"   Agent: {task['agent']}")
        print(f"   Estimated: {task['estimated_hours']}h")

        # Git worktree作成
        branch_name = f"task/{task_id.lower()}"
        worktree_path = f"./worktrees/task-{task_id.lower()}"

        try:
            # worktree作成
            subprocess.run(
                f"git worktree add -b {branch_name} {worktree_path} main",
                shell=True,
                check=True,
                capture_output=True
            )

            # ここで実際にはTask Toolを呼び出すが、
            # デモ用にシミュレーション
            self.running_tasks[task_id] = {
                'start_time': datetime.now().isoformat(),
                'agent': task['agent'],
                'worktree': worktree_path
            }

            return {
                'status': 'started',
                'task_id': task_id,
                'worktree': worktree_path
            }

        except subprocess.CalledProcessError as e:
            return {
                'status': 'failed',
                'task_id': task_id,
                'error': str(e)
            }

    def check_task_completion(self, task_id: str) -> bool:
        """
        タスクの完了状態を確認
        Args:
            task_id: 確認するタスクID
        Returns:
            完了していればTrue
        """
        # 実際にはgit statusやテスト結果を確認
        # デモ用に簡略化
        if task_id in self.running_tasks:
            # シミュレーション: 一定時間経過で完了
            start_time = datetime.fromisoformat(
                self.running_tasks[task_id]['start_time']
            )
            elapsed = (datetime.now() - start_time).seconds

            # 見積もり時間の10%で完了（デモ用）
            estimated_seconds = self.tasks[task_id]['estimated_hours'] * 60

            if elapsed > estimated_seconds:
                return True

        return False

    def complete_task(self, task_id: str):
        """
        タスクを完了としてマーク
        Args:
            task_id: 完了したタスクID
        """
        if task_id in self.running_tasks:
            del self.running_tasks[task_id]

        self.completed_tasks.add(task_id)
        self.tasks[task_id]['status'] = 'completed'

        print(f"✅ Completed: {task_id} - {self.tasks[task_id]['name']}")

        # ログに記録
        self.execution_log.append({
            'task_id': task_id,
            'status': 'completed',
            'timestamp': datetime.now().isoformat()
        })

    def execute_wbs(self):
        """
        WBS全体を実行
        """
        print("=" * 60)
        print("🎯 Dynamic Task Orchestrator v4.0")
        print("=" * 60)

        # クリティカルパス解析
        critical_path = self.find_critical_path()
        print(f"\n📊 Critical Path: {' → '.join(critical_path)}")

        # 実行ループ
        check_interval = self.wbs['execution_rules']['check_interval_seconds']

        while len(self.completed_tasks) < len(self.tasks):
            # 実行可能タスクを取得
            ready_tasks = self.get_ready_tasks()

            if ready_tasks:
                # 並列実行可能なタスクを選択
                to_execute = self.can_run_parallel(ready_tasks)

                # タスク実行
                for task_id in to_execute:
                    self.execute_task(task_id)

            # 実行中タスクの完了確認
            for task_id in list(self.running_tasks.keys()):
                if self.check_task_completion(task_id):
                    self.complete_task(task_id)

            # 進捗表示
            self.show_progress()

            # 全タスク完了チェック
            if len(self.completed_tasks) >= len(self.tasks):
                break

            # インターバル待機
            time.sleep(check_interval)

        print("\n" + "=" * 60)
        print("🎉 All tasks completed successfully!")
        print("=" * 60)

        self.generate_report()

    def show_progress(self):
        """
        進捗状況を表示
        """
        total = len(self.tasks)
        completed = len(self.completed_tasks)
        running = len(self.running_tasks)
        pending = total - completed - running

        progress = (completed / total) * 100

        print(f"\n📈 Progress: {progress:.1f}%")
        print(f"   ✅ Completed: {completed}")
        print(f"   🔄 Running: {running}")
        print(f"   ⏳ Pending: {pending}")

        if self.running_tasks:
            print("   Currently executing:")
            for task_id in self.running_tasks:
                print(f"      - {task_id}: {self.tasks[task_id]['name']}")

    def generate_report(self):
        """
        実行レポートを生成
        """
        report = {
            'project': self.wbs['project']['name'],
            'total_tasks': len(self.tasks),
            'completed_tasks': len(self.completed_tasks),
            'failed_tasks': len(self.failed_tasks),
            'critical_path': self.find_critical_path(),
            'execution_log': self.execution_log
        }

        # レポート保存
        with open('execution_report.json', 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        print("\n📄 Execution report saved to: execution_report.json")

    def generate_gantt_chart(self):
        """
        ガントチャート生成（テキスト形式）
        """
        print("\n📊 Gantt Chart:")
        print("=" * 60)

        sorted_tasks = self.topological_sort()

        for task_id in sorted_tasks:
            task = self.tasks[task_id]
            status_icon = "✅" if task_id in self.completed_tasks else "⏳"

            # 簡易的なバー表示
            bar_length = int(task['estimated_hours'] * 2)
            bar = "█" * bar_length

            print(f"{status_icon} {task_id:4} | {bar:20} | {task['name']}")

        print("=" * 60)


if __name__ == "__main__":
    # 使用例
    orchestrator = DynamicTaskOrchestrator("_workflow/config/WBS_TEMPLATE.json")
    orchestrator.execute_wbs()
    orchestrator.generate_gantt_chart()