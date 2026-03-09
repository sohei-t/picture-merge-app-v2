#!/usr/bin/env python3
"""
DELIVERY準備スクリプト
公開対象ファイルを収集し、DELIVERYフォルダを生成
"""

import os
import shutil
import json
from pathlib import Path
from typing import List, Dict, Optional, Set
from dataclasses import dataclass, field
from datetime import datetime

from portfolio_config import get_config, PortfolioConfig


@dataclass
class DeliveryManifest:
    """DELIVERYマニフェスト"""
    app_name: str
    created_at: str
    source_path: str
    files: List[str] = field(default_factory=list)
    excluded: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    total_size: int = 0

    def to_dict(self) -> Dict:
        return {
            "app_name": self.app_name,
            "created_at": self.created_at,
            "source_path": self.source_path,
            "files_count": len(self.files),
            "files": self.files,
            "excluded_count": len(self.excluded),
            "excluded": self.excluded,
            "warnings": self.warnings,
            "total_size_bytes": self.total_size,
            "total_size_human": self._human_size(self.total_size),
        }

    def _human_size(self, size: int) -> str:
        for unit in ["B", "KB", "MB", "GB"]:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"


class DeliveryOrganizer:
    """DELIVERY準備オーガナイザー"""

    def __init__(self, config: PortfolioConfig = None):
        self.config = config or get_config()

    def prepare_delivery(
        self,
        source_dir: str,
        app_name: str,
        output_dir: str = None,
    ) -> DeliveryManifest:
        """
        DELIVERYフォルダを準備

        Args:
            source_dir: ソースディレクトリ（アプリのルート）
            app_name: アプリ名（リポジトリ内のフォルダ名）
            output_dir: 出力先（デフォルト: source_dir/DELIVERY）

        Returns:
            DeliveryManifest: 生成されたマニフェスト
        """
        source_path = Path(source_dir).resolve()
        output_path = Path(output_dir) if output_dir else source_path / "DELIVERY"

        # マニフェスト初期化
        manifest = DeliveryManifest(
            app_name=app_name,
            created_at=datetime.now().isoformat(),
            source_path=str(source_path),
        )

        print("\n" + "=" * 60)
        print("  DELIVERY準備")
        print("=" * 60)
        print(f"\n  ソース: {source_path}")
        print(f"  出力先: {output_path}")
        print(f"  アプリ名: {app_name}")

        # 既存のDELIVERYフォルダをクリア
        if output_path.exists():
            print(f"\n  既存のDELIVERYフォルダを削除中...")
            shutil.rmtree(output_path)

        output_path.mkdir(parents=True, exist_ok=True)

        # ファイルを収集
        print(f"\n  ファイルを収集中...")
        collected_files = self._collect_files(source_path, output_path)

        # ファイルをコピー
        print(f"\n  ファイルをコピー中...")
        for src_file, rel_path in collected_files:
            dest_file = output_path / rel_path
            dest_file.parent.mkdir(parents=True, exist_ok=True)

            try:
                shutil.copy2(src_file, dest_file)
                manifest.files.append(rel_path)
                manifest.total_size += src_file.stat().st_size
            except Exception as e:
                manifest.warnings.append(f"コピー失敗: {rel_path} - {e}")

        # 必須ファイルチェック
        missing_required = []
        for required in self.config.REQUIRED_FILES:
            if required not in manifest.files:
                missing_required.append(required)
                manifest.warnings.append(f"必須ファイルがありません: {required}")

        # 推奨ファイルチェック
        for recommended in self.config.RECOMMENDED_FILES:
            found = any(f.endswith(recommended) or f == recommended for f in manifest.files)
            if not found:
                # 警告ではなく情報として記録
                pass

        # マニフェストを保存
        manifest_path = output_path / ".delivery_manifest.json"
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(manifest.to_dict(), f, ensure_ascii=False, indent=2)

        # 結果表示
        self._print_summary(manifest, missing_required)

        return manifest

    def _collect_files(
        self,
        source_path: Path,
        output_path: Path,
    ) -> List[tuple]:
        """公開対象ファイルを収集"""
        collected = []
        excluded = []

        for file_path in source_path.rglob("*"):
            if not file_path.is_file():
                continue

            # 出力先自体は除外
            try:
                file_path.relative_to(output_path)
                continue
            except ValueError:
                pass

            # 相対パス
            rel_path = str(file_path.relative_to(source_path))

            # 除外チェック
            if self.config.should_exclude(rel_path):
                excluded.append(rel_path)
                continue

            # 拡張子チェック
            if not self.config.is_allowed_extension(rel_path):
                excluded.append(rel_path)
                continue

            collected.append((file_path, rel_path))

        print(f"    収集: {len(collected)} ファイル")
        print(f"    除外: {len(excluded)} ファイル")

        return collected

    def _print_summary(self, manifest: DeliveryManifest, missing_required: List[str]):
        """サマリーを表示"""
        print("\n" + "-" * 60)
        print("  【DELIVERY準備完了】")
        print("-" * 60)
        print(f"  ファイル数: {len(manifest.files)}")
        print(f"  合計サイズ: {manifest.to_dict()['total_size_human']}")

        if missing_required:
            print(f"\n  ⚠️  必須ファイルが不足しています:")
            for f in missing_required:
                print(f"      - {f}")

        if manifest.warnings:
            print(f"\n  ⚠️  警告: {len(manifest.warnings)} 件")
            for w in manifest.warnings[:5]:
                print(f"      - {w}")
            if len(manifest.warnings) > 5:
                print(f"      ... 他 {len(manifest.warnings) - 5} 件")

        print("\n  【含まれるファイル】")
        for f in sorted(manifest.files)[:20]:
            print(f"    - {f}")
        if len(manifest.files) > 20:
            print(f"    ... 他 {len(manifest.files) - 20} ファイル")

        print("\n" + "=" * 60 + "\n")


def prepare_from_worktree(
    worktree_path: str,
    app_name: str = None,
) -> DeliveryManifest:
    """
    ワークツリーからDELIVERY準備

    Args:
        worktree_path: ワークツリーのパス
        app_name: アプリ名（省略時はフォルダ名から推測）
    """
    worktree = Path(worktree_path).resolve()

    # アプリ名を推測
    if not app_name:
        # worktrees/mission-v1 のような形式から取得
        app_name = worktree.name
        if app_name.startswith("mission-"):
            # PROJECT_INFO.yaml から取得を試みる
            project_info = worktree / "PROJECT_INFO.yaml"
            if project_info.exists():
                import yaml
                with open(project_info, "r", encoding="utf-8") as f:
                    info = yaml.safe_load(f)
                    if info and "project" in info:
                        app_name = info["project"].get("name", app_name)
                        # スペースをハイフンに変換、小文字化
                        app_name = app_name.lower().replace(" ", "-")

    organizer = DeliveryOrganizer()
    return organizer.prepare_delivery(
        source_dir=str(worktree),
        app_name=app_name,
    )


def find_and_prepare(base_dir: str = None) -> Optional[DeliveryManifest]:
    """
    現在のディレクトリまたは指定ディレクトリからDELIVERYを準備

    自動的にアプリのルートを検出
    """
    if base_dir:
        search_path = Path(base_dir)
    else:
        search_path = Path.cwd()

    # index.html があるディレクトリを探す
    if (search_path / "index.html").exists():
        app_name = search_path.name
        organizer = DeliveryOrganizer()
        return organizer.prepare_delivery(
            source_dir=str(search_path),
            app_name=app_name,
        )

    # worktrees 内を探す
    worktrees_dir = search_path / "worktrees"
    if worktrees_dir.exists():
        for worktree in worktrees_dir.iterdir():
            if worktree.is_dir() and (worktree / "index.html").exists():
                return prepare_from_worktree(str(worktree))

    print("❌ アプリのルートが見つかりません。")
    print("   index.html があるディレクトリで実行してください。")
    return None


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="DELIVERY準備")
    parser.add_argument("source", nargs="?", help="ソースディレクトリ")
    parser.add_argument("-n", "--name", help="アプリ名")
    parser.add_argument("-o", "--output", help="出力先ディレクトリ")
    args = parser.parse_args()

    if args.source:
        organizer = DeliveryOrganizer()
        manifest = organizer.prepare_delivery(
            source_dir=args.source,
            app_name=args.name or Path(args.source).name,
            output_dir=args.output,
        )
    else:
        manifest = find_and_prepare()

    if manifest:
        print(f"✅ DELIVERY準備完了: {manifest.app_name}")
        print(f"   ファイル数: {len(manifest.files)}")
    else:
        exit(1)
