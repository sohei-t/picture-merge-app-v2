#!/usr/bin/env python3
"""
ワークフロー状態管理

エージェントの実行状態を追跡し、中断からの復旧と
Phase 7（修正ワークフロー）の実行を支援する
"""

import os
import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum


class PhaseStatus(Enum):
    """フェーズの状態"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class WorkflowStatus(Enum):
    """ワークフロー全体の状態"""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    AWAITING_REVIEW = "awaiting_review"      # Phase 6完了、ユーザーレビュー待ち
    MODIFICATION_REQUESTED = "modification_requested"  # 修正依頼あり
    MODIFICATION_IN_PROGRESS = "modification_in_progress"  # Phase 7実行中
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class PhaseRecord:
    """フェーズの実行記録"""
    phase_number: int
    phase_name: str
    status: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    agents_used: List[str] = field(default_factory=list)
    outputs: Dict[str, Any] = field(default_factory=dict)
    error_message: Optional[str] = None


@dataclass
class ModificationRecord:
    """修正の記録"""
    iteration: int
    requested_at: str
    feedback: str
    phases_to_rerun: List[int]
    status: str  # pending, in_progress, completed
    completed_at: Optional[str] = None


@dataclass
class PortfolioRecord:
    """ポートフォリオ公開の記録"""
    published: bool = False
    app_name: Optional[str] = None
    app_url: Optional[str] = None
    commit_hash: Optional[str] = None
    last_published_at: Optional[str] = None
    security_check_passed: bool = False
    agent_review_passed: bool = False


@dataclass
class WorkflowState:
    """ワークフロー全体の状態"""
    project_name: str
    project_path: str
    workflow_type: str  # creative_webapp, tdd_webapp, etc.
    status: str
    created_at: str
    updated_at: str
    current_phase: int
    phases: List[Dict] = field(default_factory=list)
    portfolio: Dict = field(default_factory=dict)
    modifications: List[Dict] = field(default_factory=list)
    metadata: Dict = field(default_factory=dict)

    @classmethod
    def create_new(cls, project_name: str, project_path: str, workflow_type: str) -> "WorkflowState":
        """新規ワークフロー状態を作成"""
        now = datetime.now().isoformat()
        return cls(
            project_name=project_name,
            project_path=project_path,
            workflow_type=workflow_type,
            status=WorkflowStatus.NOT_STARTED.value,
            created_at=now,
            updated_at=now,
            current_phase=0,
            phases=[],
            portfolio=asdict(PortfolioRecord()),
            modifications=[],
            metadata={},
        )


class WorkflowStateManager:
    """ワークフロー状態管理マネージャー"""

    STATE_FILENAME = ".workflow_state.json"

    # フェーズ定義
    PHASES = {
        1: "計画",
        2: "デザイン",
        3: "実装",
        4: "改善ループ",
        5: "完成処理",
        6: "ポートフォリオ公開",
        7: "修正ワークフロー",
    }

    def __init__(self, project_path: str):
        self.project_path = Path(project_path).resolve()
        self.state_file = self.project_path / self.STATE_FILENAME
        self._state: Optional[WorkflowState] = None

    @property
    def state(self) -> Optional[WorkflowState]:
        """現在の状態を取得"""
        if self._state is None:
            self._state = self.load_state()
        return self._state

    def load_state(self) -> Optional[WorkflowState]:
        """状態ファイルを読み込み"""
        if not self.state_file.exists():
            return None

        try:
            with open(self.state_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                return WorkflowState(**data)
        except Exception as e:
            print(f"  ⚠️ 状態ファイル読み込みエラー: {e}")
            return None

    def save_state(self):
        """状態をファイルに保存"""
        if self._state is None:
            return

        self._state.updated_at = datetime.now().isoformat()

        with open(self.state_file, "w", encoding="utf-8") as f:
            json.dump(asdict(self._state), f, ensure_ascii=False, indent=2)

    def initialize(self, project_name: str, workflow_type: str = "creative_webapp") -> WorkflowState:
        """新規ワークフローを初期化"""
        self._state = WorkflowState.create_new(
            project_name=project_name,
            project_path=str(self.project_path),
            workflow_type=workflow_type,
        )
        self.save_state()
        return self._state

    def get_or_create(self, project_name: str, workflow_type: str = "creative_webapp") -> WorkflowState:
        """状態を取得、なければ作成"""
        if self.state is None:
            return self.initialize(project_name, workflow_type)
        return self.state

    # ===========================================
    # フェーズ管理
    # ===========================================

    def start_phase(self, phase_number: int, agents: List[str] = None):
        """フェーズを開始"""
        if self._state is None:
            raise ValueError("ワークフローが初期化されていません")

        phase_name = self.PHASES.get(phase_number, f"Phase {phase_number}")

        record = PhaseRecord(
            phase_number=phase_number,
            phase_name=phase_name,
            status=PhaseStatus.IN_PROGRESS.value,
            started_at=datetime.now().isoformat(),
            agents_used=agents or [],
        )

        # 既存のフェーズ記録を更新または追加
        existing_idx = None
        for i, p in enumerate(self._state.phases):
            if p.get("phase_number") == phase_number:
                existing_idx = i
                break

        if existing_idx is not None:
            self._state.phases[existing_idx] = asdict(record)
        else:
            self._state.phases.append(asdict(record))

        self._state.current_phase = phase_number
        self._state.status = WorkflowStatus.IN_PROGRESS.value
        self.save_state()

        print(f"\n  {'─' * 50}")
        print(f"  【Phase {phase_number}】 {phase_name} 開始")
        print(f"  {'─' * 50}")

    def complete_phase(self, phase_number: int, outputs: Dict = None):
        """フェーズを完了"""
        if self._state is None:
            return

        for p in self._state.phases:
            if p.get("phase_number") == phase_number:
                p["status"] = PhaseStatus.COMPLETED.value
                p["completed_at"] = datetime.now().isoformat()
                if outputs:
                    p["outputs"] = outputs
                break

        self.save_state()
        print(f"  ✅ Phase {phase_number} 完了")

    def fail_phase(self, phase_number: int, error_message: str):
        """フェーズを失敗として記録"""
        if self._state is None:
            return

        for p in self._state.phases:
            if p.get("phase_number") == phase_number:
                p["status"] = PhaseStatus.FAILED.value
                p["completed_at"] = datetime.now().isoformat()
                p["error_message"] = error_message
                break

        self._state.status = WorkflowStatus.FAILED.value
        self.save_state()
        print(f"  ❌ Phase {phase_number} 失敗: {error_message}")

    def get_phase_status(self, phase_number: int) -> Optional[str]:
        """フェーズの状態を取得"""
        if self._state is None:
            return None

        for p in self._state.phases:
            if p.get("phase_number") == phase_number:
                return p.get("status")
        return None

    # ===========================================
    # Phase 6: ポートフォリオ公開
    # ===========================================

    def record_portfolio_publish(
        self,
        app_name: str,
        app_url: str,
        commit_hash: str,
        security_check_passed: bool,
        agent_review_passed: bool,
    ):
        """ポートフォリオ公開を記録"""
        if self._state is None:
            return

        self._state.portfolio = {
            "published": True,
            "app_name": app_name,
            "app_url": app_url,
            "commit_hash": commit_hash,
            "last_published_at": datetime.now().isoformat(),
            "security_check_passed": security_check_passed,
            "agent_review_passed": agent_review_passed,
        }

        self._state.status = WorkflowStatus.AWAITING_REVIEW.value
        self.save_state()

    # ===========================================
    # Phase 7: 修正ワークフロー
    # ===========================================

    def request_modification(self, feedback: str, phases_to_rerun: List[int] = None):
        """修正を依頼"""
        if self._state is None:
            return

        # デフォルトは Phase 3 (実装) から再実行
        if phases_to_rerun is None:
            phases_to_rerun = [3, 4, 5, 6]

        iteration = len(self._state.modifications) + 1

        record = ModificationRecord(
            iteration=iteration,
            requested_at=datetime.now().isoformat(),
            feedback=feedback,
            phases_to_rerun=phases_to_rerun,
            status="pending",
        )

        self._state.modifications.append(asdict(record))
        self._state.status = WorkflowStatus.MODIFICATION_REQUESTED.value
        self._state.current_phase = 7
        self.save_state()

        print(f"\n  📝 修正依頼 #{iteration} を記録しました")
        print(f"  再実行するフェーズ: {phases_to_rerun}")

    def start_modification(self):
        """修正ワークフローを開始"""
        if self._state is None or not self._state.modifications:
            return

        # 最新の修正依頼を取得
        latest = self._state.modifications[-1]
        latest["status"] = "in_progress"
        self._state.status = WorkflowStatus.MODIFICATION_IN_PROGRESS.value
        self.save_state()

    def complete_modification(self):
        """修正ワークフローを完了"""
        if self._state is None or not self._state.modifications:
            return

        latest = self._state.modifications[-1]
        latest["status"] = "completed"
        latest["completed_at"] = datetime.now().isoformat()
        self._state.status = WorkflowStatus.AWAITING_REVIEW.value
        self.save_state()

        print(f"  ✅ 修正ワークフロー完了（イテレーション #{latest['iteration']}）")

    def get_pending_modification(self) -> Optional[Dict]:
        """保留中の修正を取得"""
        if self._state is None:
            return None

        for mod in reversed(self._state.modifications):
            if mod.get("status") in ["pending", "in_progress"]:
                return mod
        return None

    # ===========================================
    # ワークフロー完了
    # ===========================================

    def complete_workflow(self):
        """ワークフロー全体を完了"""
        if self._state is None:
            return

        self._state.status = WorkflowStatus.COMPLETED.value
        self.save_state()

        print("\n" + "=" * 60)
        print("  🎉 ワークフロー完了")
        print("=" * 60)

    # ===========================================
    # 状態レポート
    # ===========================================

    def print_status_report(self):
        """状態レポートを表示"""
        if self._state is None:
            print("  ワークフロー状態: 未初期化")
            return

        print("\n" + "=" * 60)
        print("  📊 ワークフロー状態レポート")
        print("=" * 60)

        print(f"\n  プロジェクト: {self._state.project_name}")
        print(f"  ワークフロー: {self._state.workflow_type}")
        print(f"  状態: {self._state.status}")
        print(f"  現在のフェーズ: {self._state.current_phase}")

        print("\n  【フェーズ進捗】")
        for phase_num, phase_name in self.PHASES.items():
            status = self.get_phase_status(phase_num)
            if status == PhaseStatus.COMPLETED.value:
                icon = "✅"
            elif status == PhaseStatus.IN_PROGRESS.value:
                icon = "🔄"
            elif status == PhaseStatus.FAILED.value:
                icon = "❌"
            else:
                icon = "⬜"
            print(f"    {icon} Phase {phase_num}: {phase_name}")

        if self._state.portfolio.get("published"):
            print("\n  【ポートフォリオ】")
            print(f"    URL: {self._state.portfolio.get('app_url')}")
            print(f"    コミット: {self._state.portfolio.get('commit_hash')}")

        if self._state.modifications:
            print(f"\n  【修正履歴】: {len(self._state.modifications)} 回")
            for mod in self._state.modifications:
                status_icon = "✅" if mod.get("status") == "completed" else "🔄"
                print(f"    {status_icon} #{mod['iteration']}: {mod['feedback'][:30]}...")

        print("\n" + "=" * 60)

    def get_next_action_prompt(self) -> str:
        """次のアクションを示すプロンプトを生成"""
        if self._state is None:
            return "ワークフローを開始してください。"

        status = self._state.status

        if status == WorkflowStatus.NOT_STARTED.value:
            return "Phase 1（計画）を開始してください。"

        elif status == WorkflowStatus.IN_PROGRESS.value:
            phase = self._state.current_phase
            phase_name = self.PHASES.get(phase, f"Phase {phase}")
            return f"Phase {phase}（{phase_name}）を続行してください。"

        elif status == WorkflowStatus.AWAITING_REVIEW.value:
            return """
ユーザーレビュー待ちです。

【ユーザーへ】
公開されたアプリを確認してください:
- URL: {app_url}

修正が必要な場合は、修正内容を教えてください。
問題なければ「完了」と伝えてください。

【修正が必要な場合のコマンド例】
「修正依頼: ボタンの色を青から緑に変更してください」
""".format(app_url=self._state.portfolio.get("app_url", "(未公開)"))

        elif status == WorkflowStatus.MODIFICATION_REQUESTED.value:
            mod = self.get_pending_modification()
            if mod:
                return f"""
修正依頼があります:
- フィードバック: {mod.get('feedback')}
- 再実行するフェーズ: {mod.get('phases_to_rerun')}

Phase 7（修正ワークフロー）を開始してください。
"""
            return "修正ワークフローを開始してください。"

        elif status == WorkflowStatus.MODIFICATION_IN_PROGRESS.value:
            mod = self.get_pending_modification()
            phases = mod.get("phases_to_rerun", []) if mod else []
            return f"修正ワークフロー実行中です。再実行フェーズ: {phases}"

        elif status == WorkflowStatus.COMPLETED.value:
            return "ワークフローは完了しています。新しいプロジェクトを開始しますか？"

        elif status == WorkflowStatus.FAILED.value:
            return "ワークフローが失敗しています。エラーを確認して再実行してください。"

        return "状態を確認してください。"


# ===========================================
# 便利関数
# ===========================================

def get_state_manager(project_path: str = None) -> WorkflowStateManager:
    """状態マネージャーを取得"""
    if project_path is None:
        project_path = os.getcwd()
    return WorkflowStateManager(project_path)


def print_workflow_status(project_path: str = None):
    """ワークフロー状態を表示"""
    manager = get_state_manager(project_path)
    manager.print_status_report()


def get_next_action(project_path: str = None) -> str:
    """次のアクションを取得"""
    manager = get_state_manager(project_path)
    return manager.get_next_action_prompt()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="ワークフロー状態管理")
    parser.add_argument("--path", default=".", help="プロジェクトパス")
    parser.add_argument("--status", action="store_true", help="状態を表示")
    parser.add_argument("--next", action="store_true", help="次のアクションを表示")
    parser.add_argument("--init", help="新規ワークフローを初期化（プロジェクト名を指定）")
    args = parser.parse_args()

    manager = get_state_manager(args.path)

    if args.init:
        manager.initialize(args.init)
        print(f"✅ ワークフローを初期化しました: {args.init}")

    if args.status:
        manager.print_status_report()

    if args.next:
        print(manager.get_next_action_prompt())
