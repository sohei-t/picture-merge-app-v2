# 🎨 AI画像生成システム仕様書

## 🎯 概要

ゲーム開発において、キャラクターや背景などのビジュアルアセットを、AI画像生成APIを使用して自動生成するシステム。
Google Imagen API（Vertex AI）を中心に、ゲーム仕様から適切な画像を生成し、即座にゲームに組み込める形式で提供します。

## 🏗️ システムアーキテクチャ

### コア要件
1. **ゲーム仕様理解** → 必要な画像リストの自動生成
2. **プロンプト最適化** → 一貫性のあるビジュアル生成
3. **API統合** → Google Imagen API の活用
4. **後処理** → 背景透過、スプライトシート化
5. **ゲーム統合** → 即座に使用可能な形式で出力

## 🤖 エージェント構成

### 1. Visual Design Coordinator（統括エージェント）
```javascript
class VisualDesignCoordinator {
  constructor() {
    this.gameSpec = null;
    this.styleGuide = null;
    this.assetList = [];
    this.generatedAssets = new Map();
  }

  async orchestrateGeneration(gameSpec) {
    // 1. ゲーム仕様を解析
    const requirements = await this.analyzeGameRequirements(gameSpec);

    // 2. ビジュアルスタイルを決定
    this.styleGuide = await this.determineVisualStyle(requirements);

    // 3. 必要なアセットリストを生成
    this.assetList = await this.generateAssetList(requirements);

    // 4. 各アセットを生成
    for (const asset of this.assetList) {
      const generated = await this.generateAsset(asset);
      this.generatedAssets.set(asset.id, generated);
    }

    // 5. 後処理とパッケージング
    return await this.packageAssets();
  }
}
```

### 2. Character Design Agent
```javascript
class CharacterDesignAgent {
  generateCharacterSpec(gameSpec, role) {
    // ゲームジャンルに応じたキャラクターデザイン
    const designs = {
      'shooting': {
        'player': {
          description: 'futuristic space pilot',
          style: 'anime-inspired, clean lines',
          poses: ['idle', 'moving', 'shooting'],
          size: '64x64',
          colors: 'bright, heroic'
        },
        'enemy': {
          description: 'alien creature',
          style: 'menacing but cartoonish',
          poses: ['idle', 'attacking'],
          size: '48x48',
          colors: 'dark, contrasting'
        }
      },
      'puzzle': {
        'player': {
          description: 'cute mascot character',
          style: 'kawaii, rounded shapes',
          poses: ['idle', 'thinking', 'celebrating'],
          size: '64x64',
          colors: 'pastel, friendly'
        }
      }
    };

    return designs[gameSpec.genre]?.[role] || this.generateDefault(role);
  }
}
```

### 3. Prompt Optimizer Agent
```javascript
class PromptOptimizerAgent {
  constructor() {
    this.basePrompt = {
      format: "transparent background PNG",
      quality: "high quality, professional game asset",
      consistency: "consistent art style",
      technical: "clean edges, no artifacts"
    };
  }

  optimizePrompt(characterSpec, styleGuide) {
    // プロンプトのテンプレート
    const template = `
      ${characterSpec.description},
      ${styleGuide.artStyle},
      ${characterSpec.pose} pose,
      ${this.basePrompt.format},
      ${this.basePrompt.quality},
      game sprite, 2D character,
      ${styleGuide.colorPalette},
      ${this.basePrompt.technical},
      simple background for easy removal,
      ${characterSpec.size} pixel art style
    `.trim().replace(/\s+/g, ' ');

    // ネガティブプロンプト
    const negative = `
      complex background,
      realistic photo,
      blurry,
      low quality,
      text,
      watermark,
      extra limbs,
      distorted proportions
    `.trim().replace(/\s+/g, ' ');

    return { prompt: template, negative };
  }

  generateBatchPrompts(characterSpec, styleGuide) {
    // 複数ポーズのプロンプトを一括生成
    const prompts = [];

    for (const pose of characterSpec.poses) {
      prompts.push(this.optimizePrompt(
        { ...characterSpec, pose },
        styleGuide
      ));
    }

    return prompts;
  }
}
```

### 4. Google Imagen Integration Agent
```javascript
class GoogleImagenAgent {
  constructor() {
    this.projectId = process.env.GOOGLE_CLOUD_PROJECT;
    this.location = 'us-central1';
    this.apiEndpoint = `https://${this.location}-aiplatform.googleapis.com`;
  }

  async initialize() {
    // Google Cloud 認証
    const { GoogleAuth } = require('google-auth-library');
    this.auth = new GoogleAuth({
      scopes: ['https://www.googleapis.com/auth/cloud-platform']
    });

    this.client = await this.auth.getClient();
  }

  async generateImage(prompt, options = {}) {
    const request = {
      instances: [{
        prompt: prompt.prompt,
        negativePrompt: prompt.negative,
      }],
      parameters: {
        sampleCount: options.count || 1,
        aspectRatio: options.aspectRatio || "1:1",
        personGeneration: "dont_allow",
        addWatermark: false,
        seed: options.seed || Math.floor(Math.random() * 1000000)
      }
    };

    try {
      const url = `${this.apiEndpoint}/v1/projects/${this.projectId}/locations/${this.location}/publishers/google/models/imagen-3.0-generate-001:predict`;

      const response = await this.client.request({
        url,
        method: 'POST',
        data: request,
        headers: {
          'Content-Type': 'application/json'
        }
      });

      // Base64画像をBufferに変換
      const images = response.data.predictions.map(pred =>
        Buffer.from(pred.bytesBase64Encoded, 'base64')
      );

      return images;
    } catch (error) {
      console.error('Imagen API Error:', error);
      throw error;
    }
  }

  async generateCharacterSet(character, styleGuide) {
    const results = new Map();

    // 各ポーズごとに生成
    for (const pose of character.poses) {
      const prompt = this.promptOptimizer.optimizePrompt(
        { ...character, pose },
        styleGuide
      );

      const images = await this.generateImage(prompt, {
        count: 3, // 3つの候補を生成
        aspectRatio: "1:1"
      });

      // 最適な画像を選択（将来的にはAI判定）
      results.set(pose, images[0]);
    }

    return results;
  }
}
```

### 5. Sprite Processor Agent
```javascript
class SpriteProcessorAgent {
  constructor() {
    this.sharp = require('sharp');
    this.spritesmith = require('spritesmith');
  }

  async processGameAssets(generatedAssets) {
    const processed = new Map();

    for (const [assetId, imageData] of generatedAssets) {
      // 1. 背景透過処理
      const transparent = await this.removeBackground(imageData);

      // 2. サイズ正規化
      const resized = await this.resizeToGameSpec(transparent);

      // 3. 最適化
      const optimized = await this.optimizeForGame(resized);

      processed.set(assetId, optimized);
    }

    // 4. スプライトシート生成
    const spriteSheet = await this.createSpriteSheet(processed);

    return spriteSheet;
  }

  async removeBackground(imageBuffer) {
    // sharp を使った背景除去
    // または remove.bg API を併用
    const image = sharp(imageBuffer);

    // アルファチャンネル処理
    const processed = await image
      .ensureAlpha()
      .flatten({ background: { r: 0, g: 0, b: 0, alpha: 0 } })
      .toBuffer();

    return processed;
  }

  async createSpriteSheet(images) {
    return new Promise((resolve, reject) => {
      const sprites = Array.from(images.entries()).map(([id, buffer]) => ({
        src: buffer,
        id: id
      }));

      this.spritesmith.run({ src: sprites }, (err, result) => {
        if (err) reject(err);

        // スプライトシートとメタデータを返す
        resolve({
          image: result.image,
          coordinates: result.coordinates,
          properties: result.properties
        });
      });
    });
  }

  generateAtlasJson(spriteData) {
    // Phaser/Unity用のアトラス形式
    const atlas = {
      frames: {},
      meta: {
        app: "AI Game Asset Generator",
        version: "1.0",
        image: "spritesheet.png",
        size: spriteData.properties,
        scale: 1
      }
    };

    for (const [id, coords] of Object.entries(spriteData.coordinates)) {
      atlas.frames[id] = {
        frame: coords,
        rotated: false,
        trimmed: false,
        spriteSourceSize: coords,
        sourceSize: coords
      };
    }

    return atlas;
  }
}
```

## 🔧 Google Cloud 設定

### 必要なAPIと設定

```bash
# 1. Vertex AI API を有効化
gcloud services enable aiplatform.googleapis.com

# 2. サービスアカウント作成
gcloud iam service-accounts create game-asset-generator \
  --display-name="Game Asset Generator"

# 3. 権限付与
gcloud projects add-iam-policy-binding PROJECT_ID \
  --member="serviceAccount:game-asset-generator@PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/aiplatform.user"

# 4. キー生成
gcloud iam service-accounts keys create \
  ./_workflow/credentials/imagen-key.json \
  --iam-account=game-asset-generator@PROJECT_ID.iam.gserviceaccount.com
```

### 環境変数設定

```javascript
// .env
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_APPLICATION_CREDENTIALS=./_workflow/credentials/imagen-key.json
IMAGEN_API_ENDPOINT=https://us-central1-aiplatform.googleapis.com
```

## 📊 コスト最適化戦略

### APIコスト管理

```javascript
class CostOptimizer {
  constructor() {
    this.costPerImage = {
      'imagen-3.0': 0.020,  // $0.02 per image
      'imagen-2.0': 0.015,  // $0.015 per image
    };

    this.quotas = {
      daily: 100,
      monthly: 2000
    };

    this.usage = {
      today: 0,
      month: 0
    };
  }

  selectModel(priority) {
    // 優先度に応じてモデル選択
    if (priority === 'quality') {
      return 'imagen-3.0';
    } else if (this.usage.today < 50) {
      return 'imagen-3.0';
    } else {
      return 'imagen-2.0';
    }
  }

  estimateCost(assetList) {
    const imageCount = assetList.reduce((sum, asset) =>
      sum + asset.poses.length, 0
    );

    const estimatedCost = imageCount * this.costPerImage['imagen-3.0'];

    return {
      imageCount,
      estimatedCost,
      recommendation: estimatedCost > 10 ?
        'Consider reducing poses or using cached assets' :
        'Within budget'
    };
  }
}
```

## 🎮 ゲームジャンル別設定

### シューティングゲーム

```javascript
const SHOOTING_GAME_ASSETS = {
  player: {
    style: "sci-fi anime character, pilot suit",
    poses: ["idle", "left_tilt", "right_tilt", "shooting"],
    size: "64x64",
    priority: "high"
  },
  enemies: [
    {
      type: "small_alien",
      style: "cute but menacing alien creature",
      poses: ["idle", "attacking"],
      size: "32x32",
      count: 3,  // 3種類のバリエーション
      priority: "medium"
    },
    {
      type: "boss",
      style: "large mechanical alien boss",
      poses: ["idle", "attacking", "damaged"],
      size: "128x128",
      priority: "high"
    }
  ],
  projectiles: {
    player_bullet: "energy beam, blue glow",
    enemy_bullet: "plasma orb, red",
    special_weapon: "missile with trail effect"
  },
  backgrounds: [
    "space nebula with stars",
    "alien planet surface",
    "space station interior"
  ]
};
```

### パズルゲーム

```javascript
const PUZZLE_GAME_ASSETS = {
  character: {
    style: "kawaii mascot, big eyes, pastel colors",
    poses: ["idle", "thinking", "happy", "sad"],
    size: "64x64",
    priority: "high"
  },
  blocks: {
    style: "colorful geometric shapes with faces",
    types: ["square", "circle", "triangle", "star"],
    colors: ["red", "blue", "green", "yellow"],
    size: "32x32",
    priority: "high"
  },
  backgrounds: [
    "cute cloud pattern",
    "rainbow gradient"
  ]
};
```

## 📋 実装チェックリスト

### 必須機能
- [ ] Google Imagen API 統合
- [ ] プロンプト最適化システム
- [ ] 背景透過処理
- [ ] スプライトシート生成
- [ ] アトラスJSON生成
- [ ] スタイル一貫性保持
- [ ] コスト管理

### 品質保証
- [ ] 生成画像の品質チェック
- [ ] サイズ正規化
- [ ] 色調統一
- [ ] ポーズの一貫性

### 最適化
- [ ] キャッシュシステム
- [ ] バッチ処理
- [ ] 並列生成

## ⚠️ 制限事項と対策

### Google Imagen API の制限

1. **レート制限**
   - 60 requests/minute
   - → バッチ処理とキューイング実装

2. **コンテンツポリシー**
   - 人物生成は制限
   - → ゲームキャラは stylized/cartoon 指定

3. **解像度制限**
   - 最大 1024x1024
   - → ゲーム用途には十分

### 対策実装

```javascript
class RateLimiter {
  constructor() {
    this.queue = [];
    this.processing = false;
    this.requestsPerMinute = 60;
    this.interval = 60000 / this.requestsPerMinute;
  }

  async addRequest(request) {
    return new Promise((resolve, reject) => {
      this.queue.push({ request, resolve, reject });
      this.processQueue();
    });
  }

  async processQueue() {
    if (this.processing || this.queue.length === 0) return;

    this.processing = true;
    const { request, resolve, reject } = this.queue.shift();

    try {
      const result = await request();
      resolve(result);
    } catch (error) {
      reject(error);
    }

    setTimeout(() => {
      this.processing = false;
      this.processQueue();
    }, this.interval);
  }
}
```