#!/usr/bin/env python3
"""
Google Text-to-Speech統合
解説台本を音声ファイルに変換
"""

import os
import json
import base64
from typing import Dict, Optional
from pathlib import Path

# Google Cloud TTS をオプショナルにインポート
try:
    from google.cloud import texttospeech
    GOOGLE_TTS_AVAILABLE = True
except ImportError:
    GOOGLE_TTS_AVAILABLE = False
    print("Warning: google-cloud-texttospeech not installed. TTS features will be limited.")

class TTSGenerator:
    """Text-to-Speech生成クラス"""

    def __init__(self, credentials_path: Optional[str] = None):
        """
        Args:
            credentials_path: Google Cloud認証JSONファイルのパス
        """
        self.credentials_path = credentials_path
        self.client = None

        if GOOGLE_TTS_AVAILABLE and credentials_path:
            self._initialize_client()

    def _initialize_client(self):
        """Google TTS クライアントを初期化"""
        if self.credentials_path and os.path.exists(self.credentials_path):
            os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = self.credentials_path
            self.client = texttospeech.TextToSpeechClient()
            print("Google TTS client initialized successfully")
        else:
            print(f"Warning: Credentials file not found at {self.credentials_path}")

    def generate_audio(self,
                      text: str,
                      output_path: str = "narration.mp3",
                      voice_config: Optional[Dict] = None) -> Optional[str]:
        """
        テキストから音声ファイルを生成

        Args:
            text: 読み上げるテキスト
            output_path: 出力ファイルパス
            voice_config: 音声設定

        Returns:
            生成された音声ファイルのパス、失敗時はNone
        """

        if not GOOGLE_TTS_AVAILABLE:
            print("Google TTS is not available. Generating placeholder file...")
            return self._generate_placeholder_audio(text, output_path)

        if not self.client:
            print("TTS client not initialized. Generating placeholder file...")
            return self._generate_placeholder_audio(text, output_path)

        try:
            # デフォルトの音声設定
            if voice_config is None:
                voice_config = self._get_default_voice_config()

            # SSML形式かプレーンテキストかを判定
            if text.strip().startswith('<speak>'):
                synthesis_input = texttospeech.SynthesisInput(ssml=text)
            else:
                synthesis_input = texttospeech.SynthesisInput(text=text)

            # 音声設定
            voice = texttospeech.VoiceSelectionParams(
                language_code=voice_config['voice']['languageCode'],
                name=voice_config['voice'].get('name'),
                ssml_gender=texttospeech.SsmlVoiceGender[voice_config['voice']['ssmlGender']]
            )

            # オーディオ設定
            audio_config = texttospeech.AudioConfig(
                audio_encoding=texttospeech.AudioEncoding.MP3,
                speaking_rate=voice_config['audioConfig'].get('speakingRate', 1.0),
                pitch=voice_config['audioConfig'].get('pitch', 0.0),
                volume_gain_db=voice_config['audioConfig'].get('volumeGainDb', 0.0),
                effects_profile_id=voice_config['audioConfig'].get('effectsProfileId', [])
            )

            # 音声合成リクエスト
            response = self.client.synthesize_speech(
                input=synthesis_input,
                voice=voice,
                audio_config=audio_config
            )

            # 音声ファイルを保存
            with open(output_path, 'wb') as out:
                out.write(response.audio_content)

            print(f"Audio file generated successfully: {output_path}")
            return output_path

        except Exception as e:
            print(f"Error generating audio: {e}")
            return self._generate_placeholder_audio(text, output_path)

    def _get_default_voice_config(self) -> Dict:
        """デフォルトの音声設定を取得"""
        return {
            "voice": {
                "languageCode": "ja-JP",
                "name": "ja-JP-Wavenet-B",
                "ssmlGender": "MALE"
            },
            "audioConfig": {
                "speakingRate": 1.0,
                "pitch": 0.0,
                "volumeGainDb": 0.0,
                "effectsProfileId": ["headphone-class-device"]
            }
        }

    def _generate_placeholder_audio(self, text: str, output_path: str) -> str:
        """
        プレースホルダー音声ファイルを生成
        （実際のTTSが利用できない場合の代替）
        """

        # メタデータファイルを作成
        metadata_path = output_path.replace('.mp3', '_metadata.json')
        metadata = {
            "type": "placeholder",
            "text_length": len(text),
            "estimated_duration": len(text) / 10,  # 大まかな推定時間（秒）
            "message": "This is a placeholder audio file. Google TTS is not configured.",
            "setup_instructions": {
                "1": "Install google-cloud-texttospeech: pip install google-cloud-texttospeech",
                "2": "Get Google Cloud credentials from https://console.cloud.google.com",
                "3": "Enable Text-to-Speech API",
                "4": "Set credentials path in environment or config"
            }
        }

        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)

        # 簡単な無音MP3を生成（ヘッダーのみ）
        # これは実際の音声ではなく、プレースホルダーとしての最小限のMP3ファイル
        mp3_header = b'\xff\xfb\x90\x00'  # MP3ヘッダーの簡易版
        with open(output_path, 'wb') as f:
            f.write(mp3_header)

        print(f"Placeholder audio file created: {output_path}")
        print(f"Metadata saved to: {metadata_path}")
        return output_path

    def batch_generate(self,
                      scripts: Dict[str, str],
                      output_dir: str = "./audio",
                      voice_config: Optional[Dict] = None) -> Dict[str, str]:
        """
        複数の台本を一括で音声化

        Args:
            scripts: {filename: text} の辞書
            output_dir: 出力ディレクトリ
            voice_config: 音声設定

        Returns:
            {filename: audio_path} の辞書
        """

        os.makedirs(output_dir, exist_ok=True)
        results = {}

        for filename, text in scripts.items():
            output_path = os.path.join(output_dir, f"{filename}.mp3")
            audio_path = self.generate_audio(text, output_path, voice_config)
            if audio_path:
                results[filename] = audio_path

        return results

    def estimate_cost(self, text: str) -> Dict:
        """
        Google TTS APIの使用料金を推定

        Args:
            text: 読み上げるテキスト

        Returns:
            料金推定情報
        """

        # 文字数をカウント
        char_count = len(text)

        # Google TTS の料金体系（2024年時点の目安）
        # WaveNet voices: $16.00 per 1 million characters
        # Standard voices: $4.00 per 1 million characters
        wavenet_rate = 16.00 / 1_000_000
        standard_rate = 4.00 / 1_000_000

        return {
            "character_count": char_count,
            "estimated_cost_wavenet": f"${char_count * wavenet_rate:.4f}",
            "estimated_cost_standard": f"${char_count * standard_rate:.4f}",
            "free_tier_remaining": max(0, 1_000_000 - char_count),  # 月間無料枠
            "note": "First 1 million characters per month are free"
        }


class TTSConfig:
    """TTS設定管理クラス"""

    @staticmethod
    def create_config_template() -> Dict:
        """設定テンプレートを作成"""
        return {
            "google_cloud": {
                "credentials_path": "${GOOGLE_APPLICATION_CREDENTIALS}",
                "project_id": "${GOOGLE_CLOUD_PROJECT}"
            },
            "default_voice": {
                "language": "ja-JP",
                "voice_name": "ja-JP-Wavenet-B",
                "gender": "MALE",
                "speaking_rate": 1.0,
                "pitch": 0.0
            },
            "audio_settings": {
                "format": "MP3",
                "sample_rate": 24000,
                "effects_profile": ["headphone-class-device"]
            },
            "batch_settings": {
                "max_concurrent": 5,
                "retry_count": 3,
                "retry_delay": 1000
            }
        }

    @staticmethod
    def save_template(filepath: str = "tts_config_template.json"):
        """設定テンプレートをファイルに保存"""
        template = TTSConfig.create_config_template()
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(template, f, ensure_ascii=False, indent=2)
        return filepath


def setup_tts_environment():
    """TTS環境のセットアップヘルパー"""

    setup_script = """#!/bin/bash
# Google Cloud Text-to-Speech セットアップスクリプト

echo "📢 Google Cloud Text-to-Speech セットアップを開始します..."

# 1. パッケージのインストール
echo "1. 必要なパッケージをインストールしています..."
pip install google-cloud-texttospeech

# 2. 認証情報の確認
echo "2. Google Cloud認証情報を確認しています..."
if [ -z "$GOOGLE_APPLICATION_CREDENTIALS" ]; then
    echo "⚠️  GOOGLE_APPLICATION_CREDENTIALS が設定されていません"
    echo "   以下の手順で設定してください："
    echo "   1. https://console.cloud.google.com にアクセス"
    echo "   2. プロジェクトを作成または選択"
    echo "   3. Text-to-Speech API を有効化"
    echo "   4. サービスアカウントキーを作成"
    echo "   5. export GOOGLE_APPLICATION_CREDENTIALS='path/to/key.json'"
else
    echo "✅ 認証情報が設定されています: $GOOGLE_APPLICATION_CREDENTIALS"
fi

# 3. API有効化の確認
echo "3. Text-to-Speech APIの有効化を確認しています..."
echo "   https://console.cloud.google.com/apis/library/texttospeech.googleapis.com"

# 4. テンプレート設定ファイルの作成
echo "4. 設定テンプレートを作成しています..."
python -c "
from tts_generator import TTSConfig
TTSConfig.save_template('tts_config_template.json')
print('✅ tts_config_template.json を作成しました')
"

echo ""
echo "🎉 セットアップ完了！"
echo "次のステップ："
echo "1. Google Cloud認証情報を設定"
echo "2. tts_config_template.json を編集"
echo "3. TTSGenerator クラスを使用して音声生成"
"""

    # セットアップスクリプトを保存
    setup_path = "setup_tts.sh"
    with open(setup_path, 'w') as f:
        f.write(setup_script)
    os.chmod(setup_path, 0o755)

    print(f"Setup script created: {setup_path}")
    print("Run './setup_tts.sh' to configure Google TTS")

    return setup_path


if __name__ == "__main__":
    # セットアップヘルパーを実行
    setup_tts_environment()

    # 設定テンプレートを作成
    TTSConfig.save_template()

    print("\n📝 使用例:")
    print("```python")
    print("from tts_generator import TTSGenerator")
    print("")
    print("# TTSジェネレーターを初期化")
    print("tts = TTSGenerator(credentials_path='path/to/credentials.json')")
    print("")
    print("# テキストを音声に変換")
    print("text = 'こんにちは、これはテストです。'")
    print("audio_path = tts.generate_audio(text, 'output.mp3')")
    print("")
    print("# 料金を推定")
    print("cost = tts.estimate_cost(text)")
    print("print(cost)")
    print("```")