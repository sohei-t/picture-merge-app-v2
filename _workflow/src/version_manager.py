#!/usr/bin/env python3
"""
バージョン管理ユーティリティ
"""

import os
import json
from datetime import datetime
from pathlib import Path

class VersionManager:
    def __init__(self):
        self.version_file = Path("VERSION")
        self.changelog_file = Path("CHANGELOG.md")

    def get_current_version(self):
        """現在のバージョンを取得"""
        if self.version_file.exists():
            return self.version_file.read_text().strip()
        return "0.0.1"

    def bump_version(self, bump_type="patch"):
        """バージョンを更新（major.minor.patch）"""
        current = self.get_current_version()
        parts = current.split('.')

        if bump_type == "major":
            parts[0] = str(int(parts[0]) + 1)
            parts[1] = "0"
            parts[2] = "0"
        elif bump_type == "minor":
            parts[1] = str(int(parts[1]) + 1)
            parts[2] = "0"
        elif bump_type == "patch":
            parts[2] = str(int(parts[2]) + 1)

        new_version = '.'.join(parts)
        self.version_file.write_text(new_version)

        # 変更履歴に追加
        self.add_to_changelog(new_version)

        return new_version

    def add_to_changelog(self, version, changes=None):
        """変更履歴に追加"""
        date = datetime.now().strftime("%Y-%m-%d")

        if not self.changelog_file.exists():
            content = "# 変更履歴\n\n"
        else:
            content = self.changelog_file.read_text()

        new_entry = f"\n## [{version}] - {date}\n\n"

        if changes:
            for change in changes:
                new_entry += f"- {change}\n"
        else:
            new_entry += "- 更新\n"

        # 最初のバージョンエントリの前に挿入
        if "##" in content:
            parts = content.split("##", 1)
            content = parts[0] + new_entry + "\n##" + parts[1]
        else:
            content += new_entry

        self.changelog_file.write_text(content)

if __name__ == "__main__":
    vm = VersionManager()
    print(f"現在のバージョン: {vm.get_current_version()}")
