#!/usr/bin/env python3
"""
Lyria Audio Generator - ゲーム効果音・BGM自動生成

Google Cloud Vertex AI の Lyria モデルを使用して、
ゲーム用のBGMと効果音を自動生成します。

使用方法:
    python3 audio_generator_lyria.py AUDIO_PROMPTS.json

必要な環境:
    - GCP認証: $GOOGLE_APPLICATION_CREDENTIALS または ~/.config/ai-agents/credentials/gcp/default.json
    - AUDIO_PROMPTS.json: 音声生成プロンプト定義
"""

import json
import os
import sys
import time
import base64
from pathlib import Path
from typing import Dict, List, Any, Optional
import subprocess

class LyriaAudioGenerator:
    """Vertex AI Lyria を使用した音声生成"""

    def __init__(self, credentials_path: str):
        """
        初期化

        Args:
            credentials_path: GCPサービスアカウントキーのパス
        """
        self.credentials_path = credentials_path
        self.project_id = None
        self.location = "us-central1"  # Lyria利用可能リージョン
        self.endpoint = f"https://{self.location}-aiplatform.googleapis.com"

        # GCP認証設定
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = credentials_path

        # プロジェクトID取得
        self._setup_project()

    def _setup_project(self):
        """GCPプロジェクトのセットアップ"""
        try:
            # credentials JSONからproject_id取得
            with open(self.credentials_path) as f:
                creds = json.load(f)
                self.project_id = creds.get("project_id")

            if not self.project_id:
                raise ValueError("project_id not found in credentials")

            print(f"✅ GCPプロジェクト: {self.project_id}")

        except Exception as e:
            print(f"❌ GCPプロジェクト設定エラー: {e}")
            raise

    def _call_lyria_api(self, prompt: str, negative_prompt: str = "",
                       bpm: int = 120, duration_seconds: int = 30) -> Optional[bytes]:
        """
        Lyria API呼び出し

        Args:
            prompt: 生成プロンプト
            negative_prompt: ネガティブプロンプト
            bpm: BPM (60-200)
            duration_seconds: 生成時間（秒）※実際は30秒固定

        Returns:
            生成された音声データ（WAVバイナリ）
        """
        try:
            # Vertex AI Lyria APIエンドポイント
            model = "lyria-002"
            endpoint_path = f"projects/{self.project_id}/locations/{self.location}/publishers/google/models/{model}"

            # リクエストボディ
            request_body = {
                "instances": [{
                    "prompt": prompt,
                    "negative_prompt": negative_prompt,
                    "sample_count": 1,
                    "guidance": 3.0,  # プロンプト強度（0.0-6.0）
                    "bpm": bpm,
                    "seed": int(time.time())  # ランダムシード
                }]
            }

            # curlコマンドでAPI呼び出し（google-cloud-aiplatformパッケージ不要）
            access_token = self._get_access_token()

            curl_command = [
                "curl",
                "-X", "POST",
                "-H", f"Authorization: Bearer {access_token}",
                "-H", "Content-Type: application/json",
                f"{self.endpoint}/v1/{endpoint_path}:predict",
                "-d", json.dumps(request_body)
            ]

            result = subprocess.run(
                curl_command,
                capture_output=True,
                text=True,
                timeout=120  # 2分タイムアウト
            )

            if result.returncode != 0:
                print(f"❌ API呼び出しエラー: {result.stderr}")
                return None

            # レスポンス解析
            response = json.loads(result.stdout)

            if "predictions" not in response:
                print(f"❌ APIレスポンスエラー: {response}")
                return None

            # Base64デコードして音声データ取得
            audio_b64 = response["predictions"][0].get("audioContent")
            if not audio_b64:
                print("❌ 音声データが含まれていません")
                return None

            audio_bytes = base64.b64decode(audio_b64)

            print(f"✅ 音声生成成功: {len(audio_bytes)} bytes")
            return audio_bytes

        except subprocess.TimeoutExpired:
            print("❌ API呼び出しタイムアウト（120秒）")
            return None
        except Exception as e:
            print(f"❌ Lyria API呼び出しエラー: {e}")
            return None

    def _get_access_token(self) -> str:
        """GCPアクセストークン取得"""
        try:
            result = subprocess.run(
                ["gcloud", "auth", "application-default", "print-access-token"],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode != 0:
                raise Exception(f"gcloud auth failed: {result.stderr}")

            return result.stdout.strip()

        except Exception as e:
            print(f"❌ アクセストークン取得エラー: {e}")
            print("⚠️  'gcloud auth application-default login' を実行してください")
            raise

    def generate_bgm(self, name: str, prompt: str, negative_prompt: str = "",
                     duration: int = 30, bpm: int = 120, output_file: str = None) -> bool:
        """
        BGM生成

        Args:
            name: BGM名
            prompt: 生成プロンプト
            negative_prompt: ネガティブプロンプト
            duration: 時間（秒）※Lyriaは30秒固定
            bpm: BPM
            output_file: 出力ファイルパス

        Returns:
            成功/失敗
        """
        print(f"\n🎵 BGM生成中: {name}")
        print(f"   プロンプト: {prompt}")
        print(f"   BPM: {bpm}, 時間: {duration}秒")

        # Lyria APIは30秒固定
        if duration != 30:
            print(f"⚠️  Lyriaは30秒固定です（指定: {duration}秒）")

        audio_data = self._call_lyria_api(
            prompt=prompt,
            negative_prompt=negative_prompt,
            bpm=bpm,
            duration_seconds=30
        )

        if audio_data and output_file:
            self._save_audio(audio_data, output_file)
            print(f"✅ BGM保存: {output_file}")
            return True

        return False

    def generate_sfx(self, name: str, prompt: str, duration: int = 1,
                     output_file: str = None) -> bool:
        """
        効果音生成

        Args:
            name: 効果音名
            prompt: 生成プロンプト
            duration: 時間（秒）※短い音でも30秒課金
            output_file: 出力ファイルパス

        Returns:
            成功/失敗
        """
        print(f"\n🔊 効果音生成中: {name}")
        print(f"   プロンプト: {prompt}")
        print(f"   時間: {duration}秒")

        # 短い音用にプロンプト調整
        short_prompt = f"{prompt}, very short sound effect, {duration} seconds duration, isolated sound"

        audio_data = self._call_lyria_api(
            prompt=short_prompt,
            negative_prompt="background music, melody, harmony, long duration",
            bpm=120,
            duration_seconds=30  # Lyriaは30秒固定
        )

        if audio_data and output_file:
            # TODO: 短い音の場合、30秒の音声から最初のN秒を切り出す処理
            # 現在は30秒全体を保存（後でトリミング可能）
            self._save_audio(audio_data, output_file)
            print(f"✅ 効果音保存: {output_file} (30秒生成、要トリミング)")
            return True

        return False

    def generate_from_prompts_file(self, prompts_file: str, base_dir: str = ".") -> Dict[str, Any]:
        """
        AUDIO_PROMPTS.json から一括生成

        Args:
            prompts_file: AUDIO_PROMPTS.jsonのパス
            base_dir: 基準ディレクトリ（相対パス解決用）

        Returns:
            生成結果サマリー
        """
        print(f"\n{'='*60}")
        print(f"🎵 AUDIO_PROMPTS.json から音声生成開始")
        print(f"{'='*60}")

        try:
            with open(prompts_file) as f:
                prompts = json.load(f)
        except Exception as e:
            print(f"❌ AUDIO_PROMPTS.json 読み込みエラー: {e}")
            return {"success": False, "error": str(e)}

        project_name = prompts.get("project_name", "Unknown")
        print(f"\nプロジェクト: {project_name}")

        results = {
            "project_name": project_name,
            "bgm": {"total": 0, "success": 0, "failed": 0, "files": []},
            "sfx": {"total": 0, "success": 0, "failed": 0, "files": []},
            "cost": 0.0
        }

        # BGM生成
        bgm_list = prompts.get("bgm", [])
        results["bgm"]["total"] = len(bgm_list)

        for bgm in bgm_list:
            output_path = os.path.join(base_dir, bgm["file"])
            success = self.generate_bgm(
                name=bgm["name"],
                prompt=bgm["prompt"],
                negative_prompt=bgm.get("negative_prompt", ""),
                duration=bgm.get("duration", 30),
                bpm=bgm.get("bpm", 120),
                output_file=output_path
            )

            if success:
                results["bgm"]["success"] += 1
                results["bgm"]["files"].append(output_path)
                results["cost"] += 0.06  # $0.06/30秒
            else:
                results["bgm"]["failed"] += 1

            # クォータ対策（2秒待機）
            time.sleep(2)

        # SFX生成
        sfx_list = prompts.get("sfx", [])
        results["sfx"]["total"] = len(sfx_list)

        for sfx in sfx_list:
            output_path = os.path.join(base_dir, sfx["file"])
            success = self.generate_sfx(
                name=sfx["name"],
                prompt=sfx["prompt"],
                duration=sfx.get("duration", 1),
                output_file=output_path
            )

            if success:
                results["sfx"]["success"] += 1
                results["sfx"]["files"].append(output_path)
                results["cost"] += 0.06  # 短い音でも30秒分課金
            else:
                results["sfx"]["failed"] += 1

            # クォータ対策（2秒待機）
            time.sleep(2)

        # サマリー表示
        self._print_summary(results)

        return results

    def _save_audio(self, audio_data: bytes, file_path: str):
        """音声ファイル保存"""
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "wb") as f:
            f.write(audio_data)

    def _print_summary(self, results: Dict[str, Any]):
        """生成結果サマリー表示"""
        print(f"\n{'='*60}")
        print(f"🎉 音声生成完了サマリー")
        print(f"{'='*60}")
        print(f"\nプロジェクト: {results['project_name']}")

        print(f"\n🎵 BGM:")
        print(f"   合計: {results['bgm']['total']}")
        print(f"   成功: {results['bgm']['success']}")
        print(f"   失敗: {results['bgm']['failed']}")

        print(f"\n🔊 効果音:")
        print(f"   合計: {results['sfx']['total']}")
        print(f"   成功: {results['sfx']['success']}")
        print(f"   失敗: {results['sfx']['failed']}")

        print(f"\n💰 推定コスト: ${results['cost']:.2f}")

        print(f"\n📁 生成ファイル:")
        for file in results['bgm']['files'] + results['sfx']['files']:
            print(f"   ✅ {file}")

        print(f"\n{'='*60}")


def main():
    """メイン処理"""
    if len(sys.argv) < 2:
        print("使用方法: python3 audio_generator_lyria.py AUDIO_PROMPTS.json")
        sys.exit(1)

    prompts_file = sys.argv[1]

    # GCP認証ファイル確認
    credentials_path = os.environ.get(
        'GOOGLE_APPLICATION_CREDENTIALS',
        os.path.expanduser("~/.config/ai-agents/credentials/gcp/default.json")
    )

    if not os.path.exists(credentials_path):
        print(f"❌ GCP認証ファイルが見つかりません: {credentials_path}")
        print("\n以下の手順でGCP認証を設定してください:")
        print("1. Google Cloud ConsoleでVertex AI APIを有効化")
        print("2. サービスアカウントキーを作成")
        print("3. 環境変数 GOOGLE_APPLICATION_CREDENTIALS にパスを設定")
        sys.exit(1)

    if not os.path.exists(prompts_file):
        print(f"❌ AUDIO_PROMPTS.json が見つかりません: {prompts_file}")
        sys.exit(1)

    # gcloud認証確認
    print("🔐 GCP認証確認中...")
    try:
        result = subprocess.run(
            ["gcloud", "auth", "application-default", "print-access-token"],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode != 0:
            print("⚠️  gcloud認証が必要です")
            print("   'gcloud auth application-default login' を実行してください")
            sys.exit(1)
    except Exception as e:
        print(f"❌ gcloud確認エラー: {e}")
        sys.exit(1)

    # 音声生成実行
    generator = LyriaAudioGenerator(credentials_path)

    base_dir = os.path.dirname(prompts_file)
    results = generator.generate_from_prompts_file(prompts_file, base_dir)

    # 結果をJSONで保存
    results_file = os.path.join(base_dir, "audio_generation_results.json")
    with open(results_file, "w") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"\n📊 詳細結果: {results_file}")

    # 失敗がある場合は終了コード1
    total_failed = results["bgm"]["failed"] + results["sfx"]["failed"]
    sys.exit(0 if total_failed == 0 else 1)


if __name__ == "__main__":
    main()
