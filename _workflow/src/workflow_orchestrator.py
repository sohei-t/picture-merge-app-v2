#!/usr/bin/env python3
"""
Workflow Orchestrator - 自律型並列処理対応ワークフロー実行システム
Version 6.0 - Autonomous Parallel Workflow System

このシステムは、AIエージェントのワークフローを自動的に実行し、
並列処理による高速化と自律的な品質改善を実現します。
"""

import os
import sys
import json
import yaml
import time
import subprocess
import threading
import queue
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TaskStatus(Enum):
    """タスクの状態"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"

class AgentType(Enum):
    """エージェントタイプ"""
    REQUIREMENTS = "requirements_analyst"
    PLANNER = "planner"
    ARCHITECT = "architect"
    TEST_DESIGNER = "test_designer"
    UI_DESIGNER = "ui_designer"
    FRONTEND = "frontend_dev"
    BACKEND = "backend_dev"
    DATABASE = "db_expert"
    EVALUATOR = "evaluator"
    IMPROVEMENT_PLANNER = "improvement_planner"
    FIXER = "fixer"
    GATEKEEPER = "gatekeeper"
    DOCUMENTER = "documenter"
    LAUNCHER = "launcher_creator"
    REVIEWER = "reviewer"
    GENERALIST = "generalist"
    # Game-specific agents
    GAME_DESIGN = "game_design"
    ASSET_REQUIREMENTS = "asset_requirements"
    CORE_GAME_LOGIC = "core_game_logic"
    ASSET_INTEGRATION = "asset_integration"
    UI_HUD = "ui_hud"
    GAME_INTEGRATION = "game_integration"
    PLAYTEST = "playtest"
    BALANCE_TUNING = "balance_tuning"
    MOBILE_GAMING_SPECIALIST = "mobile_gaming_specialist"  # NEW!

@dataclass
class Task:
    """タスク定義"""
    id: str
    name: str
    agent: AgentType
    description: str
    dependencies: List[str] = field(default_factory=list)
    status: TaskStatus = TaskStatus.PENDING
    result: Optional[Dict] = None
    error: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None

    @property
    def duration(self) -> Optional[float]:
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return None

@dataclass
class WorkflowPhase:
    """ワークフローフェーズ"""
    name: str
    agents: List[AgentType]
    parallel: bool = False
    max_iterations: int = 1
    success_criteria: Optional[str] = None
    tasks: List[Task] = field(default_factory=list)

class WorkflowOrchestrator:
    """
    ワークフロー実行オーケストレーター
    自律的にエージェントを起動し、並列処理を管理
    """

    def __init__(self, config_path: str = "_workflow/config/agent_config.yaml"):
        self.config_path = Path(config_path)
        self.config = self._load_config()
        self.task_queue = queue.Queue()
        self.results = {}
        self.executor = ThreadPoolExecutor(max_workers=3)
        self.current_worktree = None

    def _load_config(self) -> Dict:
        """設定ファイルを読み込み"""
        if not self.config_path.exists():
            raise FileNotFoundError(f"Config file not found: {self.config_path}")

        with open(self.config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)

    def execute_workflow(self, workflow_name: str, project_name: str) -> Dict:
        """
        ワークフローを実行

        Args:
            workflow_name: 実行するワークフロー名
            project_name: プロジェクト名

        Returns:
            実行結果のディクショナリ
        """
        logger.info(f"🚀 Starting workflow: {workflow_name} for project: {project_name}")

        # ワークフロー定義を取得
        workflow_def = self.config['workflows'].get(workflow_name)
        if not workflow_def:
            raise ValueError(f"Workflow not found: {workflow_name}")

        # Worktree作成
        self.current_worktree = self._create_worktree(project_name)

        try:
            # フェーズごとに実行
            results = {}
            phases = workflow_def.get('phases', [])

            for phase_def in phases:
                phase = WorkflowPhase(
                    name=phase_def['phase'],
                    agents=[AgentType(a) for a in phase_def['agents']],
                    parallel=phase_def.get('parallel', False),
                    max_iterations=phase_def.get('max_iterations', 1),
                    success_criteria=phase_def.get('success_criteria')
                )

                logger.info(f"📋 Executing phase: {phase.name}")
                phase_result = self._execute_phase(phase)
                results[phase.name] = phase_result

                # 改善ループの場合、成功するまで繰り返し
                if phase.name == "改善ループ":
                    iteration = 1
                    while iteration < phase.max_iterations:
                        if self._check_success_criteria(phase_result, phase.success_criteria):
                            break

                        logger.info(f"🔄 Improvement iteration {iteration + 1}/{phase.max_iterations}")
                        phase_result = self._execute_phase(phase)
                        results[f"{phase.name}_iteration_{iteration + 1}"] = phase_result
                        iteration += 1

            # 成果物をマージ
            if not workflow_def.get('auto_merge', True):
                logger.info("⚠️ Auto-merge disabled. Manual merge required.")
            else:
                self._merge_results(project_name)

            return {
                'status': 'success',
                'workflow': workflow_name,
                'project': project_name,
                'worktree': str(self.current_worktree),
                'phases': results,
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"❌ Workflow execution failed: {e}")
            return {
                'status': 'failed',
                'error': str(e),
                'workflow': workflow_name,
                'project': project_name,
                'timestamp': datetime.now().isoformat()
            }

    def _create_worktree(self, project_name: str) -> Path:
        """Git Worktreeを作成"""
        worktree_path = Path(f"./worktrees/mission-{project_name}")

        if worktree_path.exists():
            logger.warning(f"Worktree already exists: {worktree_path}")
            return worktree_path

        # git worktree add -b feat/{project_name} ./worktrees/mission-{project_name} main
        cmd = [
            "git", "worktree", "add",
            "-b", f"feat/{project_name}",
            str(worktree_path),
            "main"
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"Failed to create worktree: {result.stderr}")

        logger.info(f"✅ Created worktree: {worktree_path}")
        return worktree_path

    def _execute_phase(self, phase: WorkflowPhase) -> Dict:
        """フェーズを実行（並列/直列処理対応）"""
        phase_start = datetime.now()

        # タスクを生成
        tasks = []
        for i, agent in enumerate(phase.agents):
            task = Task(
                id=f"{phase.name}_{agent.value}_{i}",
                name=f"{agent.value} task",
                agent=agent,
                description=f"Execute {agent.value} for {phase.name}"
            )
            tasks.append(task)

        # 実行（並列または直列）
        if phase.parallel:
            results = self._execute_parallel(tasks)
        else:
            results = self._execute_serial(tasks)

        phase_end = datetime.now()

        return {
            'phase': phase.name,
            'parallel': phase.parallel,
            'tasks': [self._task_to_dict(t) for t in tasks],
            'duration': (phase_end - phase_start).total_seconds(),
            'success': all(t.status == TaskStatus.COMPLETED for t in tasks)
        }

    def _execute_parallel(self, tasks: List[Task]) -> Dict:
        """タスクを並列実行"""
        logger.info(f"⚡ Executing {len(tasks)} tasks in parallel")

        futures = {}
        for task in tasks:
            future = self.executor.submit(self._execute_task, task)
            futures[future] = task

        # 結果を収集
        results = {}
        for future in as_completed(futures):
            task = futures[future]
            try:
                result = future.result()
                task.status = TaskStatus.COMPLETED
                task.result = result
                results[task.id] = result
                logger.info(f"✅ Task completed: {task.name}")
            except Exception as e:
                task.status = TaskStatus.FAILED
                task.error = str(e)
                logger.error(f"❌ Task failed: {task.name} - {e}")

        return results

    def _execute_serial(self, tasks: List[Task]) -> Dict:
        """タスクを直列実行"""
        logger.info(f"📝 Executing {len(tasks)} tasks serially")

        results = {}
        for task in tasks:
            try:
                result = self._execute_task(task)
                task.status = TaskStatus.COMPLETED
                task.result = result
                results[task.id] = result
                logger.info(f"✅ Task completed: {task.name}")
            except Exception as e:
                task.status = TaskStatus.FAILED
                task.error = str(e)
                logger.error(f"❌ Task failed: {task.name} - {e}")
                break  # 直列実行では失敗時に停止

        return results

    def _execute_task(self, task: Task) -> Dict:
        """個別タスクを実行（エージェント起動）"""
        task.start_time = datetime.now()
        task.status = TaskStatus.RUNNING

        logger.info(f"🤖 Launching agent: {task.agent.value}")

        # エージェント設定を取得
        agent_config = self.config['agents'].get(task.agent.value, {})

        # Claudeコードを使ってTaskツールを呼び出すコマンドを生成
        # 実際の実装では、Claude APIを直接呼び出すか、
        # サブプロセスでClaude CLIを実行

        # シミュレーション（実際にはClaude APIを呼ぶ）
        time.sleep(2)  # エージェント実行のシミュレーション

        task.end_time = datetime.now()

        # 結果を返す（シミュレーション）
        return {
            'agent': task.agent.value,
            'status': 'completed',
            'duration': task.duration,
            'output': f"Output from {task.agent.value}",
            'files_created': [],
            'tests_passed': True if 'test' in task.agent.value else None
        }

    def _check_success_criteria(self, phase_result: Dict, criteria: Optional[str]) -> bool:
        """成功基準をチェック"""
        if not criteria:
            return True

        if criteria == "all_tests_pass":
            # すべてのテストが成功しているかチェック
            for task in phase_result.get('tasks', []):
                if task.get('tests_passed') is False:
                    return False
            return True

        return True

    def _merge_results(self, project_name: str):
        """成果物をメインブランチにマージ"""
        logger.info("🔀 Merging results to main branch")

        # git merge feat/{project_name}
        cmd = ["git", "merge", f"feat/{project_name}"]
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            logger.error(f"Merge failed: {result.stderr}")
            raise RuntimeError("Failed to merge results")

        logger.info("✅ Successfully merged to main branch")

    def _task_to_dict(self, task: Task) -> Dict:
        """タスクを辞書形式に変換"""
        return {
            'id': task.id,
            'name': task.name,
            'agent': task.agent.value,
            'status': task.status.value,
            'duration': task.duration,
            'error': task.error
        }

    def cleanup(self):
        """リソースのクリーンアップ"""
        self.executor.shutdown(wait=True)

        if self.current_worktree and self.current_worktree.exists():
            # git worktree remove
            cmd = ["git", "worktree", "remove", str(self.current_worktree)]
            subprocess.run(cmd, capture_output=True, text=True)
            logger.info(f"🧹 Cleaned up worktree: {self.current_worktree}")


def main():
    """メインエントリーポイント"""
    import argparse

    parser = argparse.ArgumentParser(description='Workflow Orchestrator')
    parser.add_argument('workflow', help='Workflow name to execute')
    parser.add_argument('project', help='Project name')
    parser.add_argument('--config', default='_workflow/config/agent_config.yaml', help='Config file path')

    args = parser.parse_args()

    # オーケストレーター実行
    orchestrator = WorkflowOrchestrator(args.config)

    try:
        result = orchestrator.execute_workflow(args.workflow, args.project)

        # 結果を表示
        print("\n" + "="*60)
        print("📊 WORKFLOW EXECUTION REPORT")
        print("="*60)
        print(json.dumps(result, indent=2, ensure_ascii=False))

    finally:
        orchestrator.cleanup()


if __name__ == "__main__":
    main()