#!/usr/bin/env python3
"""
進捗レポート生成
"""

import time
import json
from datetime import datetime
from pathlib import Path

class ProgressReporter:
    def __init__(self):
        self.start_time = time.time()
        self.tasks = []
        self.current_task = None

    def start_task(self, name, total_steps=1):
        """タスクを開始"""
        task = {
            "name": name,
            "start": time.time(),
            "total_steps": total_steps,
            "current_step": 0,
            "status": "in_progress"
        }
        self.current_task = task
        self.tasks.append(task)
        print(f"📋 {name} 開始...")

    def update_progress(self, step, message=""):
        """進捗を更新"""
        if self.current_task:
            self.current_task["current_step"] = step
            percent = (step / self.current_task["total_steps"]) * 100
            bar_length = 30
            filled = int(bar_length * step / self.current_task["total_steps"])
            bar = "=" * filled + "-" * (bar_length - filled)

            print(f"\r[{bar}] {percent:.1f}% {message}", end="")

            if step >= self.current_task["total_steps"]:
                print()  # 改行
                self.complete_task()

    def complete_task(self, status="completed"):
        """タスクを完了"""
        if self.current_task:
            self.current_task["end"] = time.time()
            self.current_task["duration"] = self.current_task["end"] - self.current_task["start"]
            self.current_task["status"] = status
            print(f"✅ {self.current_task['name']} 完了 ({self.current_task['duration']:.1f}秒)")
            self.current_task = None

    def generate_report(self):
        """最終レポートを生成"""
        total_duration = time.time() - self.start_time

        report = {
            "generated_at": datetime.now().isoformat(),
            "total_duration": total_duration,
            "tasks": self.tasks,
            "summary": {
                "total_tasks": len(self.tasks),
                "completed": len([t for t in self.tasks if t["status"] == "completed"]),
                "failed": len([t for t in self.tasks if t["status"] == "failed"])
            }
        }

        # レポートを保存
        report_path = Path("progress_report.json")
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2, default=str)

        # サマリーを表示
        print("\n" + "="*50)
        print("📊 実行完了レポート")
        print("="*50)
        print(f"総実行時間: {total_duration:.1f}秒")
        print(f"完了タスク: {report['summary']['completed']}/{report['summary']['total_tasks']}")

        return report

# 使用例
if __name__ == "__main__":
    reporter = ProgressReporter()

    # タスク1
    reporter.start_task("ファイル処理", 100)
    for i in range(100):
        time.sleep(0.01)
        reporter.update_progress(i + 1, f"ファイル {i+1}/100")

    # タスク2
    reporter.start_task("データベース更新", 50)
    for i in range(50):
        time.sleep(0.01)
        reporter.update_progress(i + 1)

    # レポート生成
    reporter.generate_report()
