#!/usr/bin/env python3
"""
🔐 認証情報チェッカー
API認証の状態を確認し、必要な設定を案内
"""

import os
import sys
import json
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import subprocess

# dotenv サポート（オプショナル）
try:
    from dotenv import load_dotenv
    DOTENV_AVAILABLE = True
except ImportError:
    DOTENV_AVAILABLE = False


@dataclass
class CredentialStatus:
    """認証情報の状態"""
    service: str
    status: str  # 'ok', 'missing', 'invalid', 'unconfigured'
    message: str
    path: Optional[str] = None
    setup_guide: Optional[str] = None


class CredentialChecker:
    """認証情報チェッカークラス"""

    def __init__(self, project_path: str = None):
        """
        Args:
            project_path: プロジェクトのパス（デフォルト: カレントディレクトリ）
        """
        self.project_path = Path(project_path or os.getcwd())
        self.template_path = Path(os.environ.get("WORKFLOW_TEMPLATE_PATH", str(self.project_path / "_workflow")))

        # .env ファイルを読み込み
        self._load_env()

    def _load_env(self):
        """環境変数を読み込み"""
        env_file = self.project_path / ".env"

        if DOTENV_AVAILABLE and env_file.exists():
            load_dotenv(env_file)
            print(f"✅ .env ファイルを読み込みました: {env_file}")
        elif env_file.exists():
            # dotenvがない場合は手動で読み込み
            with open(env_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        os.environ[key.strip()] = value.strip()
            print(f"✅ .env ファイルを読み込みました（手動）: {env_file}")
        else:
            print(f"⚠️  .env ファイルが見つかりません: {env_file}")

    def check_gcp_credentials(self) -> CredentialStatus:
        """GCP認証をチェック"""
        # 環境変数から取得
        cred_path = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')

        if not cred_path:
            # フォールバック: テンプレート環境を探す
            template_cred = self.template_path / "credentials" / "gcp-workflow-key.json"
            if template_cred.exists():
                cred_path = str(template_cred)
                os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = cred_path

        if not cred_path:
            return CredentialStatus(
                service="GCP (Text-to-Speech & Imagen)",
                status="unconfigured",
                message="GOOGLE_APPLICATION_CREDENTIALS が設定されていません",
                setup_guide="1. Google Cloud Consoleでサービスアカウント作成\n"
                           "2. Text-to-Speech API と Vertex AI APIを有効化\n"
                           "3. 認証キーをダウンロード\n"
                           "4. .env に GOOGLE_APPLICATION_CREDENTIALS を設定"
            )

        cred_file = Path(cred_path)
        if not cred_file.exists():
            return CredentialStatus(
                service="GCP (Text-to-Speech & Imagen)",
                status="missing",
                message=f"認証ファイルが見つかりません: {cred_path}",
                path=cred_path
            )

        # 認証ファイルの内容を検証
        try:
            with open(cred_file, 'r') as f:
                data = json.load(f)
                if 'type' in data and 'project_id' in data:
                    return CredentialStatus(
                        service="GCP (Text-to-Speech & Imagen)",
                        status="ok",
                        message=f"✓ プロジェクト: {data.get('project_id', 'unknown')}",
                        path=cred_path
                    )
                else:
                    return CredentialStatus(
                        service="GCP (Text-to-Speech & Imagen)",
                        status="invalid",
                        message="認証ファイルの形式が不正です",
                        path=cred_path
                    )
        except Exception as e:
            return CredentialStatus(
                service="GCP (Text-to-Speech & Imagen)",
                status="invalid",
                message=f"認証ファイルの読み込みエラー: {e}",
                path=cred_path
            )

    def check_github_credentials(self) -> CredentialStatus:
        """GitHub認証をチェック"""
        # GitHub CLIの認証状態を確認
        try:
            result = subprocess.run(
                ['gh', 'auth', 'status'],
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode == 0:
                # ユーザー名を取得
                user_result = subprocess.run(
                    ['gh', 'api', 'user', '--jq', '.login'],
                    capture_output=True,
                    text=True,
                    timeout=5
                )

                if user_result.returncode == 0:
                    username = user_result.stdout.strip()
                    return CredentialStatus(
                        service="GitHub",
                        status="ok",
                        message=f"✓ ユーザー: {username}",
                        path="gh CLI"
                    )

            return CredentialStatus(
                service="GitHub",
                status="unconfigured",
                message="GitHub CLIが認証されていません",
                setup_guide="gh auth login を実行してください"
            )

        except FileNotFoundError:
            return CredentialStatus(
                service="GitHub",
                status="missing",
                message="GitHub CLIがインストールされていません",
                setup_guide="brew install gh を実行してください"
            )
        except Exception as e:
            return CredentialStatus(
                service="GitHub",
                status="invalid",
                message=f"エラー: {e}",
                path=None
            )

    def check_openai_credentials(self) -> CredentialStatus:
        """OpenAI認証をチェック（オプション）"""
        api_key = os.environ.get('OPENAI_API_KEY')

        if not api_key:
            return CredentialStatus(
                service="OpenAI",
                status="unconfigured",
                message="未設定（オプション）",
                setup_guide=".env に OPENAI_API_KEY を設定"
            )

        # APIキーの形式を簡易チェック
        if api_key.startswith('sk-') and len(api_key) > 20:
            return CredentialStatus(
                service="OpenAI",
                status="ok",
                message="✓ APIキーが設定されています",
                path="環境変数"
            )
        else:
            return CredentialStatus(
                service="OpenAI",
                status="invalid",
                message="APIキーの形式が不正です",
                path="環境変数"
            )

    def check_all(self) -> List[CredentialStatus]:
        """すべての認証情報をチェック"""
        return [
            self.check_gcp_credentials(),
            self.check_github_credentials(),
            self.check_openai_credentials(),
        ]

    def print_report(self):
        """チェック結果を表示"""
        results = self.check_all()

        print("\n" + "=" * 60)
        print("🔐 認証情報チェックレポート")
        print("=" * 60)

        all_ok = True
        required_missing = []

        for result in results:
            status_icon = {
                'ok': '✅',
                'missing': '❌',
                'invalid': '⚠️',
                'unconfigured': '⚪'
            }.get(result.status, '❓')

            print(f"\n{status_icon} {result.service}")
            print(f"   状態: {result.status}")
            print(f"   {result.message}")

            if result.path:
                print(f"   パス: {result.path}")

            if result.setup_guide:
                print(f"\n   📝 セットアップガイド:")
                for line in result.setup_guide.split('\n'):
                    print(f"      {line}")

            # 必須サービスのチェック
            if result.service in ["GCP (Text-to-Speech & Imagen)", "GitHub"]:
                if result.status != 'ok':
                    all_ok = False
                    required_missing.append(result.service)

        print("\n" + "=" * 60)

        if all_ok:
            print("✅ すべての必須認証が設定されています")
            print("\n🚀 ワークフローを実行できます:")
            print("   python3 _workflow/src/workflow_orchestrator.py creative_webapp {app-name}")
        else:
            print("⚠️  一部の必須認証が未設定です")
            print("\n❌ 未設定の必須サービス:")
            for service in required_missing:
                print(f"   - {service}")
            print("\n📚 詳細なセットアップ手順:")
            print("   cat API_CREDENTIALS_SETUP.md")

        print("=" * 60 + "\n")

        return all_ok

    def export_env_template(self):
        """現在の環境変数を .env.template 形式で出力"""
        template_file = self.project_path / ".env.template"

        if template_file.exists():
            print(f"✅ .env.template が既に存在します: {template_file}")
            return

        # テンプレートをコピー
        source_template = self.template_path / ".env.template"
        if source_template.exists():
            import shutil
            shutil.copy(source_template, template_file)
            print(f"✅ .env.template を作成しました: {template_file}")
        else:
            print(f"❌ テンプレートが見つかりません: {source_template}")


def main():
    """CLIエントリーポイント"""
    if len(sys.argv) > 1:
        project_path = sys.argv[1]
    else:
        project_path = os.getcwd()

    checker = CredentialChecker(project_path)
    all_ok = checker.print_report()

    # 終了コード
    sys.exit(0 if all_ok else 1)


if __name__ == "__main__":
    main()
