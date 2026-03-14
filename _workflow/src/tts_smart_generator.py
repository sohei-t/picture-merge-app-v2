#!/usr/bin/env python3
"""
スマートTTS生成システム
文脈を考慮した自動分割と結合で、長い台本も1つのMP3ファイルに
"""

import os
import json
import re
import tempfile
import subprocess
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from pathlib import Path

# Google Cloud TTS をオプショナルにインポート
try:
    from google.cloud import texttospeech
    GOOGLE_TTS_AVAILABLE = True
except ImportError:
    GOOGLE_TTS_AVAILABLE = False
    print("Warning: google-cloud-texttospeech not installed.")


class SmartTTSGenerator:
    """スマートなTTS生成クラス"""

    def __init__(self, credentials_path: Optional[str] = None):
        """
        Args:
            credentials_path: Google Cloud認証JSONファイルのパス
        """
        # 認証パスの優先順位:
        # 1. 引数で明示的に指定
        # 2. 環境変数 GOOGLE_APPLICATION_CREDENTIALS
        # 3. .env ファイルから読み込み
        # 4. テンプレート環境のデフォルトパス

        if credentials_path:
            self.credentials_path = credentials_path
        elif os.environ.get('GOOGLE_APPLICATION_CREDENTIALS'):
            self.credentials_path = os.environ['GOOGLE_APPLICATION_CREDENTIALS']
        else:
            # .env ファイルを探して読み込み
            self._load_env_file()
            self.credentials_path = os.environ.get(
                'GOOGLE_APPLICATION_CREDENTIALS',
                os.path.expanduser("~/.config/ai-agents/credentials/gcp/default.json")
            )

        self.client = None
        self.max_bytes = 4500  # 5000バイト制限より少し小さめ

        if GOOGLE_TTS_AVAILABLE and os.path.exists(self.credentials_path):
            self._initialize_client()

    def _load_env_file(self):
        """カレントディレクトリから .env ファイルを探して読み込み"""
        try:
            from dotenv import load_dotenv

            # カレントディレクトリの .env
            if os.path.exists('.env'):
                load_dotenv('.env')
                return

            # 親ディレクトリの .env
            if os.path.exists('../.env'):
                load_dotenv('../.env')
                return

        except ImportError:
            # dotenvがない場合は手動で読み込み
            env_paths = ['.env', '../.env']
            for env_path in env_paths:
                if os.path.exists(env_path):
                    with open(env_path, 'r') as f:
                        for line in f:
                            line = line.strip()
                            if line and not line.startswith('#') and '=' in line:
                                key, value = line.split('=', 1)
                                # ~ を展開
                                value = os.path.expanduser(value.strip())
                                os.environ[key.strip()] = value
                    return

    def _initialize_client(self):
        """Google TTS クライアントを初期化"""
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = self.credentials_path
        self.client = texttospeech.TextToSpeechClient()
        print("✅ Google TTS client initialized")

    def split_text_by_context(self, text: str, is_ssml: bool = False) -> List[str]:
        """
        文脈を考慮してテキストを分割

        Args:
            text: 分割するテキスト
            is_ssml: SSML形式かどうか

        Returns:
            分割されたテキストのリスト
        """
        chunks = []
        current_chunk = ""

        if is_ssml:
            # SSMLタグを一時的に削除して分割処理
            text = re.sub(r'<speak>|</speak>', '', text)

        # 優先度順の区切り文字
        # 1. セクション区切り（breakタイムが長いもの）
        # 2. 段落区切り（改行2つ以上）
        # 3. 文の区切り（句点）
        # 4. 改行

        # まず大きなセクションで分割を試みる
        sections = re.split(r'<break time="[1-9]\d*s"/>', text)

        for section in sections:
            if not section.strip():
                continue

            # セクションが制限内なら追加
            if self._get_byte_size(current_chunk + section) <= self.max_bytes:
                current_chunk += section
                if section != sections[-1]:  # 最後のセクション以外
                    current_chunk += '<break time="1s"/>'
            else:
                # セクションが大きすぎる場合は段落で分割
                if current_chunk:
                    chunks.append(current_chunk.strip())
                    current_chunk = ""

                # 段落で分割
                paragraphs = section.split('\n\n')
                for paragraph in paragraphs:
                    if self._get_byte_size(current_chunk + paragraph) <= self.max_bytes:
                        current_chunk += paragraph + '\n\n'
                    else:
                        # 段落も大きすぎる場合は文で分割
                        if current_chunk:
                            chunks.append(current_chunk.strip())
                            current_chunk = ""

                        sentences = self._split_by_sentence(paragraph)
                        for sentence in sentences:
                            if self._get_byte_size(current_chunk + sentence) <= self.max_bytes:
                                current_chunk += sentence
                            else:
                                if current_chunk:
                                    chunks.append(current_chunk.strip())
                                current_chunk = sentence

        # 最後のチャンクを追加
        if current_chunk.strip():
            chunks.append(current_chunk.strip())

        # SSMLの場合は各チャンクに<speak>タグを追加
        if is_ssml:
            chunks = [f'<speak>{chunk}</speak>' for chunk in chunks]

        return chunks

    def _split_by_sentence(self, text: str) -> List[str]:
        """文単位で分割"""
        # 日本語の句点で分割
        sentences = re.split(r'([。！？])', text)

        # 句読点を文に含める
        result = []
        for i in range(0, len(sentences), 2):
            if i + 1 < len(sentences):
                result.append(sentences[i] + sentences[i + 1])
            else:
                result.append(sentences[i])

        return [s for s in result if s.strip()]

    def _get_byte_size(self, text: str) -> int:
        """テキストのバイトサイズを取得"""
        return len(text.encode('utf-8'))

    def generate_audio_chunks(self,
                            chunks: List[str],
                            voice_config: Optional[Dict] = None,
                            is_ssml: bool = False) -> List[str]:
        """
        テキストチャンクから音声ファイルを生成

        Args:
            chunks: テキストチャンクのリスト
            voice_config: 音声設定
            is_ssml: SSML形式かどうか

        Returns:
            生成された音声ファイルパスのリスト
        """
        if not self.client:
            print("❌ TTS client not initialized")
            return []

        temp_files = []

        # デフォルトの音声設定
        if voice_config is None:
            voice_config = {
                "language_code": "ja-JP",
                "name": "ja-JP-Wavenet-B",
                "ssml_gender": "MALE"
            }

        print(f"📝 {len(chunks)}個のチャンクを処理中...")

        for i, chunk in enumerate(chunks):
            print(f"  チャンク {i+1}/{len(chunks)} を生成中...")

            try:
                # 音声合成の入力
                if is_ssml:
                    synthesis_input = texttospeech.SynthesisInput(ssml=chunk)
                else:
                    synthesis_input = texttospeech.SynthesisInput(text=chunk)

                # 音声設定
                voice = texttospeech.VoiceSelectionParams(
                    language_code=voice_config.get('language_code', 'ja-JP'),
                    name=voice_config.get('name', 'ja-JP-Wavenet-B')
                )

                audio_config = texttospeech.AudioConfig(
                    audio_encoding=texttospeech.AudioEncoding.MP3,
                    speaking_rate=voice_config.get('speaking_rate', 1.0),
                    pitch=voice_config.get('pitch', 0.0),
                    volume_gain_db=voice_config.get('volume_gain_db', 0.0)
                )

                # API呼び出し
                response = self.client.synthesize_speech(
                    input=synthesis_input,
                    voice=voice,
                    audio_config=audio_config
                )

                # 一時ファイルに保存
                temp_file = tempfile.NamedTemporaryFile(
                    suffix=f'_chunk_{i}.mp3',
                    delete=False,
                    dir=tempfile.gettempdir()
                )
                temp_file.write(response.audio_content)
                temp_file.close()
                temp_files.append(temp_file.name)

                print(f"    ✅ チャンク {i+1} 完了 ({len(response.audio_content) / 1024:.2f} KB)")

            except Exception as e:
                print(f"    ❌ チャンク {i+1} エラー: {e}")

        return temp_files

    def merge_audio_files(self, audio_files: List[str], output_path: str) -> bool:
        """
        複数の音声ファイルを結合

        Args:
            audio_files: 結合する音声ファイルのリスト
            output_path: 出力ファイルパス

        Returns:
            成功したかどうか
        """
        if not audio_files:
            print("❌ 結合する音声ファイルがありません")
            return False

        try:
            # ffmpegが利用可能か確認
            result = subprocess.run(['which', 'ffmpeg'], capture_output=True, text=True)
            has_ffmpeg = result.returncode == 0

            if has_ffmpeg:
                # ffmpegを使用して結合
                print("🔧 ffmpegで音声ファイルを結合中...")

                # ファイルリストを作成
                list_file = tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False)
                for audio_file in audio_files:
                    list_file.write(f"file '{audio_file}'\n")
                list_file.close()

                # ffmpegで結合
                cmd = [
                    'ffmpeg', '-f', 'concat', '-safe', '0',
                    '-i', list_file.name,
                    '-c', 'copy',
                    '-y',  # 上書き確認なし
                    output_path
                ]

                result = subprocess.run(cmd, capture_output=True, text=True)
                os.unlink(list_file.name)

                if result.returncode == 0:
                    print(f"✅ 音声ファイルを結合しました: {output_path}")
                    return True
                else:
                    print(f"❌ ffmpeg結合エラー: {result.stderr}")
                    # フォールバック
                    return self._merge_with_python(audio_files, output_path)

            else:
                # ffmpegがない場合はPythonで結合
                return self._merge_with_python(audio_files, output_path)

        except Exception as e:
            print(f"❌ 結合エラー: {e}")
            return False

    def _merge_with_python(self, audio_files: List[str], output_path: str) -> bool:
        """Pythonで音声ファイルを結合（簡易版）"""
        print("🔧 Pythonで音声ファイルを結合中...")

        try:
            with open(output_path, 'wb') as output:
                for audio_file in audio_files:
                    with open(audio_file, 'rb') as input_file:
                        output.write(input_file.read())

            print(f"✅ 音声ファイルを結合しました: {output_path}")
            return True

        except Exception as e:
            print(f"❌ Python結合エラー: {e}")
            return False

    def generate_from_text(self,
                          text: str,
                          output_path: str,
                          voice_config: Optional[Dict] = None,
                          cleanup: bool = True) -> Tuple[bool, Dict]:
        """
        テキストから音声ファイルを生成（メインメソッド）

        Args:
            text: 入力テキスト（プレーンテキストまたはSSML）
            output_path: 出力MP3ファイルパス
            voice_config: 音声設定
            cleanup: 一時ファイルを削除するか

        Returns:
            (成功フラグ, 統計情報)
        """
        start_time = datetime.now()
        stats = {
            'total_characters': len(text),
            'total_bytes': self._get_byte_size(text),
            'chunks': 0,
            'temp_files': [],
            'duration': 0
        }

        print("\n" + "="*60)
        print("🎙️ スマートTTS音声生成を開始")
        print("="*60)

        # SSML判定
        is_ssml = text.strip().startswith('<speak>') or '<break' in text

        # テキストを文脈考慮で分割
        print("📝 テキストを分析中...")
        chunks = self.split_text_by_context(text, is_ssml)
        stats['chunks'] = len(chunks)

        print(f"📊 統計:")
        print(f"  - 総文字数: {stats['total_characters']:,}")
        print(f"  - 総バイト数: {stats['total_bytes']:,}")
        print(f"  - チャンク数: {stats['chunks']}")

        # 各チャンクの音声を生成
        temp_files = self.generate_audio_chunks(chunks, voice_config, is_ssml)
        stats['temp_files'] = temp_files

        if not temp_files:
            print("❌ 音声生成に失敗しました")
            return False, stats

        # 音声ファイルを結合
        success = self.merge_audio_files(temp_files, output_path)

        # クリーンアップ
        if cleanup and temp_files:
            print("🧹 一時ファイルを削除中...")
            for temp_file in temp_files:
                try:
                    os.unlink(temp_file)
                except:
                    pass

        # 統計情報を更新
        end_time = datetime.now()
        stats['duration'] = (end_time - start_time).total_seconds()

        if success:
            file_size = os.path.getsize(output_path) / 1024  # KB
            print(f"\n🎉 生成完了！")
            print(f"  📁 ファイル: {output_path}")
            print(f"  📊 サイズ: {file_size:.2f} KB")
            print(f"  ⏱️ 処理時間: {stats['duration']:.2f}秒")

            # コスト推定
            cost_wavenet = stats['total_characters'] * (16.00 / 1_000_000)
            print(f"  💰 推定コスト: ${cost_wavenet:.4f} (WaveNet)")
            print(f"  📢 無料枠残り: {1_000_000 - stats['total_characters']:,} 文字/月")

        return success, stats


def create_workflow_integration():
    """git-worktree-agentワークフローへの統合用関数"""

    integration_code = '''
# git-worktree-agentのワークフローに統合

from tts_smart_generator import SmartTTSGenerator

def generate_project_narration(project_data):
    """プロジェクトの解説音声を生成"""

    # 台本を準備（SSMLまたはMarkdown）
    script_path = project_data.get('narration_script', 'docs/narration_script.ssml')
    output_path = project_data.get('output_path', 'docs/narration.mp3')

    # 台本を読み込み
    with open(script_path, 'r', encoding='utf-8') as f:
        script = f.read()

    # スマートTTSジェネレーターを初期化
    tts = SmartTTSGenerator()

    # 音声を生成（自動的に分割・結合）
    success, stats = tts.generate_from_text(
        text=script,
        output_path=output_path,
        voice_config={
            'language_code': 'ja-JP',
            'name': 'ja-JP-Wavenet-B',
            'speaking_rate': 1.0,
            'pitch': 0.0
        }
    )

    if success:
        print(f"✅ 解説音声を生成: {output_path}")
        # HTMLドキュメントに音声を組み込み
        update_html_with_audio(output_path)

    return success

# ワークフローのタスクとして登録
workflow_tasks.append({
    "id": "DOCS-3",
    "name": "解説音声生成",
    "description": "プロジェクトの解説音声を自動生成",
    "dependencies": ["DOCS-1", "DOCS-2"],  # HTMLとScript生成後
    "action": generate_project_narration
})
'''

    # 統合ファイルを作成
    output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'workflow_tts_integration.py')
    with open(output_path, 'w') as f:
        f.write(integration_code)

    print("\n📝 ワークフロー統合コードを生成しました")


if __name__ == "__main__":
    # テスト実行
    print("SmartTTSGenerator テスト")

    # 3Dゲームの台本でテスト
    tts = SmartTTSGenerator()

    # SSMLファイルを読み込み
    ssml_path = "/Users/tsujisouhei/Desktop/3d-shooting-game/docs/narration_script.ssml"
    if os.path.exists(ssml_path):
        with open(ssml_path, 'r', encoding='utf-8') as f:
            script = f.read()

        # 1つのファイルに結合して生成
        success, stats = tts.generate_from_text(
            text=script,
            output_path="/Users/tsujisouhei/Desktop/3d-shooting-game/docs/narration_complete.mp3"
        )

        if success:
            print("\n🎧 音声を再生:")
            print("open /Users/tsujisouhei/Desktop/3d-shooting-game/docs/narration_complete.mp3")