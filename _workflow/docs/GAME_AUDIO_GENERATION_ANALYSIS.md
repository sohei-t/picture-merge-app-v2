# ゲーム効果音・BGM生成機能 - 実装可能性分析

**作成日**: 2025-12-18
**目的**: ゲーム開発ワークフローに効果音・BGM自動生成機能を追加

---

## 🎵 利用可能なAPI

### 1. Google Cloud Lyria（推奨 - GCP統合）

**概要:**
- Google の Vertex AI で提供される音楽生成AI
- TTS/Imagen と同じGCP環境で統合可能

**仕様:**
```yaml
model: lyria-002
output:
  format: WAV
  duration: 30秒
  sample_rate: 48kHz
  type: インストゥルメンタル（ボーカルなし）

pricing: $0.06 / 30秒

features:
  - テキストプロンプトから音楽生成
  - ネガティブプロンプト対応
  - BPM設定（60-200）
  - ムード/ジャンル指定
  - SynthID透かし（責任あるAI）
```

**API例:**
```python
from google.cloud import aiplatform

endpoint = "us-central1-aiplatform.googleapis.com"
model = "lyria-002"

request = {
    "instances": [{
        "prompt": "8-bit retro game background music, upbeat, adventurous, chiptune style, 120 BPM",
        "negative_prompt": "vocals, lyrics, drums",
        "sample_count": 1,
        "seed": 42
    }]
}

# 30秒のWAVファイル生成（$0.06）
response = client.predict(request)
```

**対応ムード（ゲーム向け）:**
- Ambient（環境音）
- Bright Tones（明るい）
- Chill（落ち着いた）
- Danceable（リズミカル）
- Dreamy（夢のような）
- Experimental（実験的）
- Funky（ファンキー）
- Lo-fi（ローファイ）
- Psychedelic（サイケデリック）

### 2. ElevenLabs Sound Effects API（代替案1）

**概要:**
- 効果音特化のAPI
- 短い効果音に最適

**仕様:**
```yaml
output:
  duration: 最大22秒
  format: MP3/WAV

pricing: 有料プラン（詳細不明）

features:
  - テキストから効果音生成
  - 商用利用可能（ロイヤリティフリー）
  - Python SDK対応
```

**API例:**
```python
from elevenlabs import ElevenLabs

client = ElevenLabs(api_key="YOUR_API_KEY")

result = client.text_to_sound_effects.convert(
    text="8-bit coin collect sound effect",
    duration_seconds=2,
    prompt_influence=0.3
)
```

### 3. Stable Audio（代替案2）

**概要:**
- Stability AI の音楽・効果音生成モデル
- 最大3分の楽曲生成可能

**仕様:**
```yaml
output:
  duration: 最大3分
  quality: スタジオ品質

features:
  - Text-to-Audio
  - Audio-to-Audio
  - Audio Inpainting
```

---

## 🎮 ワークフロー統合案

### Phase 1-6: AIプロンプト生成（拡張）

**既存:**
```yaml
Phase 1-6 (画像必要な場合):
  output: IMAGE_PROMPTS.json
```

**拡張後:**
```yaml
Phase 1-6 (ゲームプロジェクトの場合):
  output:
    - IMAGE_PROMPTS.json（画像生成用）
    - AUDIO_PROMPTS.json（音声生成用）← NEW
```

**AUDIO_PROMPTS.json 例:**
```json
{
  "project_name": "Space Invaders Clone",
  "bgm": [
    {
      "name": "main_theme",
      "prompt": "8-bit retro space game background music, upbeat, adventurous, chiptune style, 120 BPM, synthesizer heavy",
      "negative_prompt": "vocals, lyrics, acoustic instruments",
      "duration": 30,
      "loop": true,
      "file": "assets/audio/bgm_main.wav"
    },
    {
      "name": "game_over",
      "prompt": "8-bit sad game over theme, slow tempo, minor key, retro synthesizer, 80 BPM",
      "negative_prompt": "vocals, upbeat, major key",
      "duration": 10,
      "loop": false,
      "file": "assets/audio/bgm_game_over.wav"
    }
  ],
  "sfx": [
    {
      "name": "player_shoot",
      "prompt": "8-bit laser shoot sound effect, short, sharp, retro game style",
      "duration": 1,
      "file": "assets/audio/sfx_shoot.wav"
    },
    {
      "name": "enemy_explosion",
      "prompt": "8-bit explosion sound effect, retro game style, punchy, short burst",
      "duration": 1,
      "file": "assets/audio/sfx_explosion.wav"
    },
    {
      "name": "coin_collect",
      "prompt": "8-bit coin collect sound, cheerful, short ping, retro game style",
      "duration": 0.5,
      "file": "assets/audio/sfx_coin.wav"
    }
  ]
}
```

### Phase 2: 実装（音声生成追加）

**拡張後のPhase 2:**
```yaml
Phase 2: 実装フェーズ

画像生成が必要な場合:
  1. IMAGE_PROMPTS.json 確認
  2. use the gcp skill 宣言
  3. Vertex AI Imagen API で画像生成
  4. 失敗時のみSVG代替

音声生成が必要な場合（ゲーム等）: ← NEW
  1. AUDIO_PROMPTS.json 確認
  2. use the gcp skill 宣言（同じ認証）
  3. Vertex AI Lyria API で音声生成
  4. 失敗時は無音（エラー記録）

  手順:
    a. BGM生成（各30秒、$0.06/曲）
    b. 効果音生成（各1-2秒、$0.01/音）
    c. HTMLへの自動組み込み
```

---

## 💰 コスト試算

### ゲーム1本あたりのコスト例

**Space Invaders Clone:**
```yaml
BGM:
  - main_theme: 30秒 × $0.06 = $0.06
  - game_over: 10秒 × $0.02 = $0.02

SFX:
  - player_shoot: 1秒 × $0.002 = $0.002
  - enemy_explosion: 1秒 × $0.002 = $0.002
  - coin_collect: 0.5秒 × $0.001 = $0.001

合計: 約 $0.09 / ゲーム
```

**比較（既存ワークフロー）:**
```yaml
画像生成（Imagen）:
  - player_ship.png: $0.02
  - enemy_alien.png: $0.02
  - bullet.png: $0.02
  合計: $0.06

音声解説（TTS）:
  - explanation.mp3: $0.00（無料枠内）

新規追加（音声生成）:
  - BGM + SFX: $0.09

総コスト: $0.15 / ゲームプロジェクト
```

**結論: 許容範囲内（$0.20以下を目標）**

---

## 🛠️ 実装方針

### Option A: Lyria統合（推奨）

**理由:**
- 既存のGCP認証を再利用
- Imagen/TTS と同じAPIパターン
- 管理が一元化

**実装ファイル:**
```python
# src/audio_generator_lyria.py（新規）

import json
from google.cloud import aiplatform

class LyriaAudioGenerator:
    """Vertex AI Lyria を使用した音声生成"""

    def __init__(self, credentials_path):
        self.credentials_path = credentials_path
        self.client = aiplatform.gapic.PredictionServiceClient(
            credentials=credentials_path
        )

    def generate_bgm(self, prompt, duration=30, bpm=120):
        """BGM生成"""
        request = {
            "instances": [{
                "prompt": prompt,
                "sample_count": 1,
                "guidance": 3.0,
                "bpm": bpm
            }]
        }
        response = self.client.predict(request)
        return response.predictions[0]["audioContent"]

    def generate_sfx(self, prompt, duration=1):
        """効果音生成（短時間用）"""
        # 短い音は duration を調整
        request = {
            "instances": [{
                "prompt": f"{prompt}, very short, {duration} seconds",
                "sample_count": 1
            }]
        }
        response = self.client.predict(request)
        return response.predictions[0]["audioContent"]

    def generate_from_prompts_file(self, prompts_file):
        """AUDIO_PROMPTS.json から一括生成"""
        with open(prompts_file) as f:
            prompts = json.load(f)

        results = {
            "bgm": [],
            "sfx": []
        }

        # BGM生成
        for bgm in prompts.get("bgm", []):
            print(f"🎵 BGM生成中: {bgm['name']}")
            audio = self.generate_bgm(
                prompt=bgm["prompt"],
                duration=bgm.get("duration", 30)
            )
            self.save_audio(audio, bgm["file"])
            results["bgm"].append(bgm["name"])

        # SFX生成
        for sfx in prompts.get("sfx", []):
            print(f"🔊 効果音生成中: {sfx['name']}")
            audio = self.generate_sfx(
                prompt=sfx["prompt"],
                duration=sfx.get("duration", 1)
            )
            self.save_audio(audio, sfx["file"])
            results["sfx"].append(sfx["name"])

        return results

    def save_audio(self, audio_content, file_path):
        """音声ファイル保存"""
        import os
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "wb") as f:
            f.write(audio_content)
```

### Option B: ElevenLabs統合（代替案）

**理由:**
- 効果音に特化
- 短い音声の品質が高い

**問題点:**
- 新規API認証が必要
- GCP統合の一貫性が失われる

---

## 📋 CLAUDE.md への追加内容

### Phase 1-6 の拡張

```markdown
### Phase 1-6: AIプロンプト生成（画像・音声）

ゲームプロジェクトの場合、以下を生成:

1. IMAGE_PROMPTS.json（画像生成用）
   - プレイヤー、敵、アイテム等のビジュアル

2. AUDIO_PROMPTS.json（音声生成用）← NEW
   - BGM（背景音楽）
   - SFX（効果音）

生成基準:
  プロジェクトタイプ判定:
    - ゲーム → 画像 + 音声
    - Webアプリ → 画像のみ
    - CLI → なし

AUDIO_PROMPTS.json 構造:
  - bgm: 背景音楽リスト（name, prompt, duration, loop, file）
  - sfx: 効果音リスト（name, prompt, duration, file）
```

### Phase 2 の拡張

```markdown
### Phase 2: 実装フェーズ

音声生成が必要な場合（ゲーム等）:

  ⚠️ 最重要: 以下の手順を必ず順番に実行（省略・変更禁止）

  ❌ 禁止事項:
    - AUDIO_PROMPTS.json をスキップして無音
    - API認証を試さずに音声なしで完成
    - コスト削減を理由にAPI使用を回避

  ✅ 必須手順（この順番で実行）:

    1. AUDIO_PROMPTS.json の確認
       - Phase 1-6で生成されているか確認
       - なければPhase 1に戻って生成

    2. use the gcp skill 宣言（必須）
       - 画像生成と同じ認証を使用

    3. GCP認証セットアップ
       - gcp-workflow-key.json 確認（TTS/Imagen と共通）

    4. Vertex AI Lyria API 実行
       - AUDIO_PROMPTS.json のプロンプトを使用
       - BGM生成（各30秒、$0.06/曲）
       - SFX生成（各1-2秒、$0.01-0.02/音）
       - 2秒待機（クォータ対策）

    5. HTML統合
       - <audio> タグ自動生成
       - ゲームイベントと連動
       - ループ設定（BGM）

    6. 結果記録
       - 成功: 音声ファイル保存、コスト記録
       - 失敗: エラー内容記録、無音で完成（理由明記）

  ⚠️ 音声なし完成の条件:
    - 上記1-4を実行して失敗した場合のみ
    - 失敗理由をREADME.mdに明記
    - 例: "GCP認証エラー", "クォータ超過", "API応答なし"
    - 正規手順を試さずに音声なしは禁止
```

---

## 🎯 実装手順

### Step 1: audio_generator_lyria.py 作成
- Lyria API統合
- AUDIO_PROMPTS.json 読み込み
- BGM/SFX自動生成

### Step 2: documenter_agent.py 拡張
- AUDIO_PROMPTS.json 生成機能追加
- ゲーム判定ロジック

### Step 3: CLAUDE.md 更新
- Phase 1-6 に音声プロンプト生成追加
- Phase 2 に音声生成手順追加

### Step 4: テスト実装
- Space Invaders Clone で検証
- コスト・品質確認

---

## ⚠️ 制約事項

### Lyria API の制約

1. **出力形式:**
   - インストゥルメンタルのみ（ボーカルなし）
   - 30秒単位の生成

2. **効果音の扱い:**
   - 1-2秒の短い音も30秒分の課金
   - プロンプトで "very short, 1 second" と指定
   - 生成後にトリミング必要

3. **ループ処理:**
   - ループはHTML側で実装（<audio loop>）
   - シームレスなループは手動調整必要

### コスト最適化

```yaml
効果音の最適化:
  問題: 1秒の効果音も$0.06課金（30秒単位）

  解決策1: バッチ生成
    - 複数の効果音を1つのプロンプトで生成
    - 例: "3 different 8-bit sound effects: shoot, explosion, coin"
    - 30秒の中に複数の音を含める
    - 生成後に分割

  解決策2: 代替API併用
    - BGM: Lyria（$0.06/30秒）
    - SFX: ElevenLabs（短い音に最適化）
    - 管理は複雑化するが、コスト削減
```

---

## 📊 期待される効果

### ゲーム開発の完全自動化

**Before（音声なし）:**
- ビジュアル: AI生成
- 音声: なし（開発者が後から追加）

**After（音声あり）:**
- ビジュアル: AI生成
- 音声: AI生成
- → 完全なゲーム体験を自動生成

### ポートフォリオの差別化

```
従来のAI生成ゲーム:
  - 見た目のみ（画像）
  - 音声なし

新ワークフロー:
  - 画像 + BGM + 効果音
  - リッチな体験
  - 技術力アピール
```

---

## 🎬 結論

**実装可能性: ✅ 高い**

**推奨実装:**
- Google Cloud Lyria API を使用
- 既存のGCP認証を再利用
- Phase 1-6 に AUDIO_PROMPTS.json 生成追加
- Phase 2 に音声生成手順追加

**コスト:**
- ゲーム1本あたり $0.09（音声）
- 総コスト $0.15/プロジェクト
- 許容範囲内

**次のステップ:**
1. audio_generator_lyria.py 実装
2. CLAUDE.md 更新（Phase 1-6, Phase 2）
3. Space Invaders Clone でテスト
4. ワークフロー検証

---

**作成者**: Claude Code
**日時**: 2025-12-18
