#!/usr/bin/env python3
"""
GitHub Pages用パス検証・自動修正ツール

目的:
- HTML/CSS/JS内の絶対パスを検出
- 相対パスに自動変換
- GitHub Pages環境を模倣したローカルテスト

使用方法:
  python3 _workflow/src/path_validator.py project/public/
"""

import re
import sys
from pathlib import Path
from typing import List, Dict, Tuple
import http.server
import socketserver
import threading
import time
import subprocess


class PathValidator:
    def __init__(self, public_dir: Path):
        self.public_dir = Path(public_dir)
        self.issues: List[Dict] = []
        self.fixes: List[Dict] = []

    def validate_and_fix(self) -> Tuple[List[Dict], List[Dict]]:
        """パス検証と自動修正を実行"""
        print("=" * 60)
        print("🔍 GitHub Pages用パス検証開始")
        print("=" * 60)
        print(f"対象ディレクトリ: {self.public_dir}")
        print()

        # HTML, CSS, JSファイルを検証
        html_files = list(self.public_dir.glob("**/*.html"))
        css_files = list(self.public_dir.glob("**/*.css"))
        js_files = list(self.public_dir.glob("**/*.js"))

        all_files = html_files + css_files + js_files

        print(f"📄 検証対象: {len(all_files)}ファイル")
        print(f"  - HTML: {len(html_files)}")
        print(f"  - CSS: {len(css_files)}")
        print(f"  - JS: {len(js_files)}")
        print()

        for file_path in all_files:
            self._validate_file(file_path)

        # 結果サマリー
        self._print_summary()

        return self.issues, self.fixes

    def _validate_file(self, file_path: Path):
        """個別ファイルの検証と修正"""
        try:
            content = file_path.read_text(encoding='utf-8')
            original_content = content
            modified = False

            relative_path = file_path.relative_to(self.public_dir)

            # 1. 絶対パス検出（/ で始まる src/href）
            absolute_paths = re.findall(r'((?:src|href|content)=["\'])(/[^"\']+)', content)
            for attr, path in absolute_paths:
                if not path.startswith('//'):  # プロトコル相対URLは除外
                    # 絶対パスを相対パスに変換
                    fixed_path = '.' + path
                    content = content.replace(f'{attr}{path}', f'{attr}{fixed_path}')
                    modified = True

                    self.issues.append({
                        'file': str(relative_path),
                        'type': '絶対パス',
                        'original': path,
                        'fixed': fixed_path
                    })

            # 2. file:// プロトコル検出
            file_protocols = re.findall(r'file://[^\s\'"]+', content)
            for protocol_url in file_protocols:
                self.issues.append({
                    'file': str(relative_path),
                    'type': 'file://プロトコル',
                    'original': protocol_url,
                    'fixed': '（要手動修正）'
                })

            # 3. ../ の過度な使用（警告のみ）
            parent_refs = content.count('../')
            if parent_refs > 3:
                self.issues.append({
                    'file': str(relative_path),
                    'type': '../の過剰使用',
                    'original': f'{parent_refs}回',
                    'fixed': '（確認推奨）'
                })

            # 4. ルート相対パス（CSSのurl()内）
            css_urls = re.findall(r'url\(["\']?(/[^)"\'"]+)', content)
            for url_path in css_urls:
                if not url_path.startswith('//'):
                    fixed_path = '.' + url_path
                    content = re.sub(
                        rf'url\(["\']?{re.escape(url_path)}',
                        f'url({fixed_path}',
                        content
                    )
                    modified = True

                    self.issues.append({
                        'file': str(relative_path),
                        'type': 'CSS絶対パス',
                        'original': url_path,
                        'fixed': fixed_path
                    })

            # 修正内容を保存
            if modified:
                file_path.write_text(content, encoding='utf-8')
                self.fixes.append({
                    'file': str(relative_path),
                    'changes': len([i for i in self.issues if i['file'] == str(relative_path)])
                })
                print(f"✅ 修正: {relative_path} ({len([i for i in self.issues if i['file'] == str(relative_path)])}箇所)")

        except Exception as e:
            print(f"⚠️  エラー: {relative_path} - {e}")

    def _print_summary(self):
        """結果サマリーを出力"""
        print()
        print("=" * 60)
        print("📊 検証結果サマリー")
        print("=" * 60)

        if not self.issues:
            print("✅ 問題なし！すべてのパスが相対パスです。")
            return

        # 問題タイプ別集計
        issue_types = {}
        for issue in self.issues:
            issue_type = issue['type']
            issue_types[issue_type] = issue_types.get(issue_type, 0) + 1

        print(f"🔴 検出された問題: {len(self.issues)}件")
        for issue_type, count in issue_types.items():
            print(f"  - {issue_type}: {count}件")

        print()
        print(f"✅ 自動修正完了: {len(self.fixes)}ファイル")

        # 詳細リスト（最大10件）
        if self.issues:
            print()
            print("📋 問題詳細（最大10件）:")
            for i, issue in enumerate(self.issues[:10]):
                print(f"  {i+1}. [{issue['type']}] {issue['file']}")
                print(f"     変更前: {issue['original']}")
                print(f"     変更後: {issue['fixed']}")

            if len(self.issues) > 10:
                print(f"  ... 他 {len(self.issues) - 10}件")

        print()


class LocalServerTester:
    """GitHub Pages環境を模倣したローカルサーバーテスト"""

    def __init__(self, public_dir: Path, app_name: str):
        self.public_dir = Path(public_dir)
        self.app_name = app_name
        self.port = 8000

    def test(self):
        """ローカルサーバーで動作確認"""
        print("=" * 60)
        print("🌐 ローカルサーバーテスト（GitHub Pages環境模倣）")
        print("=" * 60)

        # サーバー起動
        print(f"サーバー起動中: http://localhost:{self.port}/{self.app_name}/")

        # シンプルなHTTPサーバー起動
        handler = http.server.SimpleHTTPRequestHandler

        try:
            with socketserver.TCPServer(("", self.port), handler) as httpd:
                # バックグラウンドでサーバー起動
                server_thread = threading.Thread(target=httpd.serve_forever)
                server_thread.daemon = True
                server_thread.start()

                time.sleep(1)  # サーバー起動待機

                # 重要ファイルのアクセステスト
                test_urls = [
                    f"http://localhost:{self.port}/{self.app_name}/index.html",
                    f"http://localhost:{self.port}/{self.app_name}/about.html",
                    f"http://localhost:{self.port}/{self.app_name}/explanation.mp3",
                ]

                print("\n📄 アクセステスト:")
                results = []
                for url in test_urls:
                    try:
                        result = subprocess.run(
                            ['curl', '-s', '-o', '/dev/null', '-w', '%{http_code}', url],
                            capture_output=True,
                            text=True,
                            timeout=5
                        )
                        status = result.stdout.strip()

                        if status == '200':
                            print(f"  ✅ {url} - OK")
                            results.append(True)
                        else:
                            print(f"  ❌ {url} - NG (HTTP {status})")
                            results.append(False)
                    except Exception as e:
                        print(f"  ⚠️  {url} - エラー: {e}")
                        results.append(False)

                # サーバー停止
                httpd.shutdown()

                # 結果サマリー
                print()
                if all(results):
                    print("✅ すべてのファイルにアクセス可能です！")
                else:
                    print("⚠️  一部のファイルにアクセスできませんでした。")

                print()
                print("💡 手動確認:")
                print(f"  ブラウザで確認: http://localhost:{self.port}/{self.app_name}/index.html")
                print(f"  about.html: http://localhost:{self.port}/{self.app_name}/about.html")

        except OSError as e:
            print(f"⚠️  サーバー起動失敗: {e}")
            print(f"  ポート{self.port}が使用中の可能性があります")


def main():
    """メイン処理"""
    if len(sys.argv) < 2:
        print("使用方法: python3 _workflow/src/path_validator.py <public_dir>")
        print("例: python3 _workflow/src/path_validator.py project/public/")
        sys.exit(1)

    public_dir = Path(sys.argv[1])

    if not public_dir.exists():
        print(f"エラー: ディレクトリが存在しません: {public_dir}")
        sys.exit(1)

    # アプリ名を推定（ディレクトリ名から）
    app_name = public_dir.parent.name if public_dir.name == 'public' else public_dir.name

    # パス検証と自動修正
    validator = PathValidator(public_dir)
    issues, fixes = validator.validate_and_fix()

    # ローカルサーバーテスト（オプション）
    if '--test' in sys.argv:
        tester = LocalServerTester(public_dir.parent, app_name)
        tester.test()

    # 終了コード
    if any(issue['type'] in ['file://プロトコル'] for issue in issues):
        print()
        print("⚠️  手動修正が必要な問題があります。")
        sys.exit(1)
    else:
        print()
        print("✅ パス検証・修正完了！GitHub Pagesで正常に動作するはずです。")
        sys.exit(0)


if __name__ == '__main__':
    main()
