#!/usr/bin/env python3
"""
セキュリティチェッカー
公開前にファイル内の秘密情報を検出
"""

import os
import re
import json
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, field
from enum import Enum

from portfolio_config import get_config, PortfolioConfig


class Severity(Enum):
    """問題の深刻度"""
    CRITICAL = "CRITICAL"  # 絶対に公開禁止（APIキー、秘密鍵等）
    HIGH = "HIGH"          # 高リスク（パスワード、内部URL等）
    MEDIUM = "MEDIUM"      # 中リスク（内部パス、デバッグ情報等）
    LOW = "LOW"            # 低リスク（確認推奨）


@dataclass
class SecurityIssue:
    """検出されたセキュリティ問題"""
    file_path: str
    line_number: int
    severity: Severity
    issue_type: str
    description: str
    matched_content: str  # マスク済みの内容
    recommendation: str


@dataclass
class SecurityReport:
    """セキュリティチェックレポート"""
    scan_path: str
    total_files: int
    scanned_files: int
    skipped_files: int
    issues: List[SecurityIssue] = field(default_factory=list)

    @property
    def has_critical(self) -> bool:
        return any(i.severity == Severity.CRITICAL for i in self.issues)

    @property
    def has_high(self) -> bool:
        return any(i.severity == Severity.HIGH for i in self.issues)

    @property
    def is_safe(self) -> bool:
        return not self.has_critical and not self.has_high

    def get_summary(self) -> Dict:
        """サマリーを取得"""
        by_severity = {s.value: 0 for s in Severity}
        for issue in self.issues:
            by_severity[issue.severity.value] += 1
        return {
            "total_files": self.total_files,
            "scanned_files": self.scanned_files,
            "skipped_files": self.skipped_files,
            "issues_count": len(self.issues),
            "by_severity": by_severity,
            "is_safe": self.is_safe,
        }


class SecurityChecker:
    """セキュリティチェッカー"""

    def __init__(self, config: PortfolioConfig = None):
        self.config = config or get_config()

        # バイナリ拡張子（スキャンしない）
        self.binary_extensions = {
            ".png", ".jpg", ".jpeg", ".gif", ".webp", ".avif",
            ".ico", ".mp3", ".wav", ".ogg", ".mp4", ".webm",
            ".woff", ".woff2", ".ttf", ".otf", ".eot",
            ".pdf", ".zip", ".tar", ".gz",
        }

    def scan_directory(self, directory: str) -> SecurityReport:
        """ディレクトリをスキャン"""
        dir_path = Path(directory)
        report = SecurityReport(
            scan_path=str(dir_path),
            total_files=0,
            scanned_files=0,
            skipped_files=0,
        )

        if not dir_path.exists():
            print(f"  ディレクトリが存在しません: {directory}")
            return report

        # 全ファイルを列挙
        all_files = list(dir_path.rglob("*"))
        report.total_files = len([f for f in all_files if f.is_file()])

        for file_path in all_files:
            if not file_path.is_file():
                continue

            # バイナリファイルはスキップ
            if file_path.suffix.lower() in self.binary_extensions:
                report.skipped_files += 1
                continue

            # 除外パターンに一致するファイルはスキップ
            if self.config.should_exclude(str(file_path)):
                report.skipped_files += 1
                continue

            # ファイルをスキャン
            issues = self._scan_file(file_path)
            report.issues.extend(issues)
            report.scanned_files += 1

        return report

    def scan_file(self, file_path: str) -> List[SecurityIssue]:
        """単一ファイルをスキャン"""
        return self._scan_file(Path(file_path))

    def _scan_file(self, file_path: Path) -> List[SecurityIssue]:
        """ファイル内容をスキャン"""
        issues = []

        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
            lines = content.split("\n")
        except Exception as e:
            return issues

        rel_path = str(file_path)

        # 各行をチェック
        for line_num, line in enumerate(lines, 1):
            # APIキーパターンチェック
            for pattern in self.config.API_KEY_PATTERNS:
                matches = re.finditer(pattern, line, re.IGNORECASE)
                for match in matches:
                    issues.append(SecurityIssue(
                        file_path=rel_path,
                        line_number=line_num,
                        severity=Severity.CRITICAL,
                        issue_type="API_KEY",
                        description="APIキーまたはトークンが検出されました",
                        matched_content=self._mask_sensitive(match.group()),
                        recommendation="このファイルを公開対象から除外するか、該当箇所を削除してください",
                    ))

            # 危険なコンテンツパターンチェック
            for pattern in self.config.DANGEROUS_CONTENT_PATTERNS:
                if re.search(pattern, line, re.IGNORECASE):
                    issues.append(SecurityIssue(
                        file_path=rel_path,
                        line_number=line_num,
                        severity=Severity.CRITICAL,
                        issue_type="SENSITIVE_DATA",
                        description="秘密鍵または認証情報が検出されました",
                        matched_content=self._mask_line(line),
                        recommendation="このファイルは絶対に公開しないでください",
                    ))

            # 内部パスパターンチェック
            for pattern in self.config.INTERNAL_PATH_PATTERNS:
                if re.search(pattern, line):
                    issues.append(SecurityIssue(
                        file_path=rel_path,
                        line_number=line_num,
                        severity=Severity.MEDIUM,
                        issue_type="INTERNAL_PATH",
                        description="内部パスまたはIPアドレスが検出されました",
                        matched_content=self._mask_line(line),
                        recommendation="ハードコードされたパスを相対パスまたは環境変数に置き換えてください",
                    ))

        # ファイル名自体のチェック
        filename_issues = self._check_filename(file_path)
        issues.extend(filename_issues)

        return issues

    def _check_filename(self, file_path: Path) -> List[SecurityIssue]:
        """ファイル名の危険性をチェック"""
        issues = []
        name = file_path.name.lower()

        dangerous_names = {
            ".env": (Severity.CRITICAL, "環境変数ファイル"),
            "credentials": (Severity.CRITICAL, "認証情報ファイル"),
            "secret": (Severity.CRITICAL, "秘密情報ファイル"),
            "password": (Severity.HIGH, "パスワードファイル"),
            "private": (Severity.HIGH, "プライベートキーファイル"),
            "serviceaccount": (Severity.CRITICAL, "サービスアカウントファイル"),
        }

        for keyword, (severity, desc) in dangerous_names.items():
            if keyword in name:
                issues.append(SecurityIssue(
                    file_path=str(file_path),
                    line_number=0,
                    severity=severity,
                    issue_type="DANGEROUS_FILENAME",
                    description=f"危険なファイル名: {desc}",
                    matched_content=name,
                    recommendation="このファイルを公開対象から除外してください",
                ))

        return issues

    def _mask_sensitive(self, text: str) -> str:
        """機密情報をマスク"""
        if len(text) <= 10:
            return "*" * len(text)
        return text[:4] + "*" * (len(text) - 8) + text[-4:]

    def _mask_line(self, line: str) -> str:
        """行をマスク（最大50文字、中間をマスク）"""
        line = line.strip()
        if len(line) <= 20:
            return line[:5] + "..." + line[-5:] if len(line) > 10 else line
        return line[:10] + "..." + line[-10:]


def print_report(report: SecurityReport, verbose: bool = False):
    """レポートを表示"""
    print("\n" + "=" * 60)
    print("  セキュリティスキャンレポート")
    print("=" * 60)

    summary = report.get_summary()

    print(f"\n  スキャン対象: {report.scan_path}")
    print(f"  総ファイル数: {summary['total_files']}")
    print(f"  スキャン済み: {summary['scanned_files']}")
    print(f"  スキップ: {summary['skipped_files']}")

    print(f"\n  検出された問題: {summary['issues_count']} 件")
    print(f"    CRITICAL: {summary['by_severity']['CRITICAL']}")
    print(f"    HIGH: {summary['by_severity']['HIGH']}")
    print(f"    MEDIUM: {summary['by_severity']['MEDIUM']}")
    print(f"    LOW: {summary['by_severity']['LOW']}")

    if report.is_safe:
        print("\n  " + "=" * 56)
        print("  ✅ 重大な問題は検出されませんでした。公開可能です。")
        print("  " + "=" * 56)
    else:
        print("\n  " + "=" * 56)
        print("  ❌ 重大な問題が検出されました。公開を中止してください。")
        print("  " + "=" * 56)

    # 詳細表示
    if report.issues and (verbose or not report.is_safe):
        print("\n  【検出された問題の詳細】")
        print("-" * 60)

        for i, issue in enumerate(report.issues, 1):
            severity_icon = {
                Severity.CRITICAL: "🚨",
                Severity.HIGH: "⚠️ ",
                Severity.MEDIUM: "📋",
                Severity.LOW: "ℹ️ ",
            }[issue.severity]

            print(f"\n  [{i}] {severity_icon} {issue.severity.value}: {issue.issue_type}")
            print(f"      ファイル: {issue.file_path}")
            if issue.line_number > 0:
                print(f"      行: {issue.line_number}")
            print(f"      説明: {issue.description}")
            print(f"      内容: {issue.matched_content}")
            print(f"      推奨: {issue.recommendation}")

    print("\n" + "=" * 60 + "\n")


def check_directory(directory: str, verbose: bool = False) -> Tuple[bool, SecurityReport]:
    """
    ディレクトリをチェック

    Returns:
        (is_safe, report): 安全かどうかとレポート
    """
    checker = SecurityChecker()
    report = checker.scan_directory(directory)
    print_report(report, verbose)
    return report.is_safe, report


def check_files(files: List[str], verbose: bool = False) -> Tuple[bool, SecurityReport]:
    """
    ファイルリストをチェック

    Returns:
        (is_safe, report): 安全かどうかとレポート
    """
    checker = SecurityChecker()

    report = SecurityReport(
        scan_path="(file list)",
        total_files=len(files),
        scanned_files=0,
        skipped_files=0,
    )

    for file_path in files:
        path = Path(file_path)
        if not path.exists():
            report.skipped_files += 1
            continue

        issues = checker.scan_file(file_path)
        report.issues.extend(issues)
        report.scanned_files += 1

    print_report(report, verbose)
    return report.is_safe, report


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="セキュリティチェッカー")
    parser.add_argument("path", nargs="?", default=".", help="スキャン対象のパス")
    parser.add_argument("-v", "--verbose", action="store_true", help="詳細表示")
    args = parser.parse_args()

    is_safe, report = check_directory(args.path, args.verbose)
    exit(0 if is_safe else 1)
