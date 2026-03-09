#!/usr/bin/env python3
"""
ポートフォリオ公開設定
階層型設定システムと連携して、安全な公開を実現
"""

import os
import sys
from pathlib import Path
from typing import Dict, List, Set

# 階層型設定システムのパスを追加
CONFIG_SCRIPTS_DIR = Path.home() / ".config" / "ai-agents" / "scripts"
if CONFIG_SCRIPTS_DIR.exists():
    sys.path.insert(0, str(CONFIG_SCRIPTS_DIR))
    try:
        from config_resolver import load_profile, resolve_config
    except ImportError:
        load_profile = None
        resolve_config = None
else:
    load_profile = None
    resolve_config = None


class PortfolioConfig:
    """ポートフォリオ公開の設定管理"""

    def __init__(self, project_path: str = None):
        self.project_path = Path(project_path) if project_path else Path.cwd()
        self._load_config()

    def _load_config(self):
        """設定を読み込み"""
        # 階層型設定システムから読み込み
        if resolve_config:
            config = resolve_config(str(self.project_path))
        else:
            config = {}

        # GitHub設定
        self.github_username = config.get("GITHUB_USERNAME", os.environ.get("GITHUB_USERNAME", ""))
        self.github_repo = config.get("GITHUB_PORTFOLIO_REPO", os.environ.get("GITHUB_PORTFOLIO_REPO", "ai-agent-portfolio"))
        self.github_token = config.get("GITHUB_TOKEN", os.environ.get("GITHUB_TOKEN", ""))

        # リポジトリURL
        self.repo_url = f"https://github.com/{self.github_username}/{self.github_repo}"
        self.repo_clone_url = f"https://github.com/{self.github_username}/{self.github_repo}.git"

        # GitHub Pages URL
        self.pages_url = f"https://{self.github_username}.github.io/{self.github_repo}"

    # =========================================
    # 除外パターン（絶対に公開しないファイル）
    # =========================================

    EXCLUDE_PATTERNS: Set[str] = {
        # 環境設定・認証
        ".env",
        ".env.*",
        ".env.local",
        ".env.development",
        ".env.production",
        "*.env",

        # 認証情報
        "credentials/",
        "credentials",
        "*.key",
        "*.pem",
        "*.p12",
        "*.pfx",
        "*.crt",
        "*.cer",
        "secrets.*",
        "secret.*",
        "*secret*",
        "*credential*",
        "*password*",
        "service-account*.json",
        "gcp-*.json",
        "firebase-*.json",

        # Git・バージョン管理
        ".git/",
        ".git",
        ".gitignore",
        ".gitattributes",

        # 依存関係・ビルド
        "node_modules/",
        "node_modules",
        "__pycache__/",
        "__pycache__",
        "*.pyc",
        "*.pyo",
        ".cache/",
        "dist/",
        "build/",
        "*.egg-info/",
        ".eggs/",
        "venv/",
        ".venv/",
        "env/",

        # IDE・エディタ
        ".idea/",
        ".vscode/",
        "*.swp",
        "*.swo",
        "*~",
        ".DS_Store",
        "Thumbs.db",

        # テスト・カバレッジ
        "coverage/",
        ".coverage",
        "htmlcov/",
        ".pytest_cache/",
        ".nyc_output/",

        # ログ・一時ファイル
        "*.log",
        "logs/",
        "tmp/",
        "temp/",

        # ワークフロー固有
        "worktrees/",
        "ai-agents-config/",
        "CLAUDE.md",
        "*.command",

        # その他
        "package-lock.json",
        "yarn.lock",
        "pnpm-lock.yaml",
    }

    # =========================================
    # 公開必須ファイル
    # =========================================

    REQUIRED_FILES: List[str] = [
        "index.html",
        "README.md",
    ]

    RECOMMENDED_FILES: List[str] = [
        "about.html",
        "style.css",
        "app.js",
        "script.js",
    ]

    # =========================================
    # セキュリティチェック用パターン
    # =========================================

    # APIキーパターン（正規表現）
    API_KEY_PATTERNS: List[str] = [
        # 汎用
        r'["\']?[Aa][Pp][Ii][_-]?[Kk][Ee][Yy]["\']?\s*[:=]\s*["\'][A-Za-z0-9_\-]{20,}["\']',
        r'["\']?[Ss][Ee][Cc][Rr][Ee][Tt][_-]?[Kk][Ee][Yy]["\']?\s*[:=]\s*["\'][A-Za-z0-9_\-]{20,}["\']',
        r'["\']?[Aa][Cc][Cc][Ee][Ss][Ss][_-]?[Tt][Oo][Kk][Ee][Nn]["\']?\s*[:=]\s*["\'][A-Za-z0-9_\-]{20,}["\']',

        # AWS
        r'AKIA[0-9A-Z]{16}',
        r'["\']?aws[_-]?access[_-]?key[_-]?id["\']?\s*[:=]\s*["\'][A-Z0-9]{20}["\']',
        r'["\']?aws[_-]?secret[_-]?access[_-]?key["\']?\s*[:=]\s*["\'][A-Za-z0-9/+=]{40}["\']',

        # GCP
        r'"type"\s*:\s*"service_account"',
        r'"private_key"\s*:\s*"-----BEGIN',
        r'AIza[0-9A-Za-z_-]{35}',  # Google API Key

        # Firebase
        r'["\']?apiKey["\']?\s*:\s*["\']AIza[A-Za-z0-9_-]{35}["\']',

        # GitHub
        r'gh[pousr]_[A-Za-z0-9]{36,}',
        r'github_pat_[A-Za-z0-9]{22}_[A-Za-z0-9]{59}',

        # Stripe
        r'sk_live_[A-Za-z0-9]{24,}',
        r'pk_live_[A-Za-z0-9]{24,}',
        r'sk_test_[A-Za-z0-9]{24,}',

        # OpenAI
        r'sk-[A-Za-z0-9]{48}',

        # Anthropic
        r'sk-ant-[A-Za-z0-9_-]{40,}',

        # Slack
        r'xox[baprs]-[0-9]{10,}-[A-Za-z0-9]{10,}',

        # 汎用パスワード
        r'["\']?password["\']?\s*[:=]\s*["\'][^"\']{8,}["\']',
        r'["\']?passwd["\']?\s*[:=]\s*["\'][^"\']{8,}["\']',

        # データベース接続
        r'mongodb(\+srv)?://[^\s]+',
        r'postgres(ql)?://[^\s]+',
        r'mysql://[^\s]+',
        r'redis://[^\s]+',
    ]

    # 危険なファイル内容パターン
    DANGEROUS_CONTENT_PATTERNS: List[str] = [
        r'-----BEGIN (RSA |DSA |EC |OPENSSH )?PRIVATE KEY-----',
        r'-----BEGIN CERTIFICATE-----',
        r'"private_key_id"\s*:',
        r'"client_email"\s*:\s*"[^"]+@[^"]+\.iam\.gserviceaccount\.com"',
    ]

    # 内部パス・URL（漏洩リスク）
    INTERNAL_PATH_PATTERNS: List[str] = [
        r'/Users/[a-zA-Z0-9_-]+/',
        r'/home/[a-zA-Z0-9_-]+/',
        r'C:\\Users\\[a-zA-Z0-9_-]+\\',
        r'192\.168\.\d{1,3}\.\d{1,3}',
        r'10\.\d{1,3}\.\d{1,3}\.\d{1,3}',
        r'172\.(1[6-9]|2[0-9]|3[01])\.\d{1,3}\.\d{1,3}',
        r'localhost:\d{4,5}',
    ]

    # =========================================
    # 公開対象の拡張子
    # =========================================

    ALLOWED_EXTENSIONS: Set[str] = {
        # Web
        ".html", ".htm", ".css", ".js", ".jsx", ".ts", ".tsx",
        ".json", ".xml", ".svg", ".ico",

        # 画像
        ".png", ".jpg", ".jpeg", ".gif", ".webp", ".avif",

        # 音声・動画
        ".mp3", ".wav", ".ogg", ".mp4", ".webm",

        # フォント
        ".woff", ".woff2", ".ttf", ".otf", ".eot",

        # ドキュメント
        ".md", ".txt", ".pdf",

        # データ
        ".csv",

        # その他
        ".map",  # Source maps（必要な場合のみ）
    }

    # =========================================
    # ヘルパーメソッド
    # =========================================

    def should_exclude(self, filepath: str) -> bool:
        """ファイルを除外すべきかチェック"""
        path = Path(filepath)
        name = path.name

        # パターンマッチ
        for pattern in self.EXCLUDE_PATTERNS:
            if pattern.endswith("/"):
                # ディレクトリパターン
                if pattern.rstrip("/") in str(path.parent).split(os.sep):
                    return True
                if name == pattern.rstrip("/"):
                    return True
            elif "*" in pattern:
                # ワイルドカードパターン
                import fnmatch
                if fnmatch.fnmatch(name, pattern):
                    return True
                if fnmatch.fnmatch(str(path), pattern):
                    return True
            else:
                # 完全一致
                if name == pattern:
                    return True

        return False

    def is_allowed_extension(self, filepath: str) -> bool:
        """許可された拡張子かチェック"""
        ext = Path(filepath).suffix.lower()
        return ext in self.ALLOWED_EXTENSIONS or ext == ""  # 拡張子なしも許可（README等）

    def get_app_url(self, app_name: str) -> str:
        """アプリのGitHub Pages URLを取得"""
        return f"{self.pages_url}/apps/{app_name}/"

    def get_repo_app_path(self, app_name: str) -> str:
        """リポジトリ内のアプリパスを取得"""
        return f"apps/{app_name}"


# グローバル設定インスタンス
_config = None

def get_config(project_path: str = None) -> PortfolioConfig:
    """設定インスタンスを取得"""
    global _config
    if _config is None or project_path:
        _config = PortfolioConfig(project_path)
    return _config


if __name__ == "__main__":
    # テスト実行
    config = get_config()
    print(f"GitHub User: {config.github_username}")
    print(f"GitHub Repo: {config.github_repo}")
    print(f"Repo URL: {config.repo_url}")
    print(f"Pages URL: {config.pages_url}")
    print(f"\nExclude patterns: {len(config.EXCLUDE_PATTERNS)}")
    print(f"API key patterns: {len(config.API_KEY_PATTERNS)}")
