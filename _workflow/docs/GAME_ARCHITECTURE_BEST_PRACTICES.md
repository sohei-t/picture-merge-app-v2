# 🏗️ ゲームアーキテクチャ ベストプラクティス

## 📋 開発失敗から学んだ教訓

### よくある失敗パターン
1. **複雑すぎる設計** → 修復不可能
2. **衝突判定の後付け** → バグの温床
3. **デバッグ機能なし** → 問題特定が困難
4. **パフォーマンス無視** → プレイ不可能
5. **エフェクト後回し** → 統合困難

## 🎯 5つの必須要件とその実装

### 1. シンプルで保守しやすい設計

#### ❌ 悪い例
```javascript
// すべてを1つのクラスに詰め込む
class Game {
  constructor() {
    this.player = {...};
    this.enemies = [...];
    this.bullets = [...];
    // 1000行以上のコンストラクタ...
  }

  update() {
    // 500行以上の更新処理...
  }
}
```

#### ✅ 良い例
```javascript
// シンプルなコンポーネントシステム
class GameCore {
  constructor() {
    this.systems = {
      input: new InputSystem(),
      physics: new PhysicsSystem(),
      render: new RenderSystem(),
      collision: new CollisionSystem()
    };

    this.entities = new EntityManager();
  }

  update(deltaTime) {
    // 各システムを順番に更新（5行で完結）
    Object.values(this.systems).forEach(system => {
      system.update(this.entities, deltaTime);
    });
  }
}

// 各システムは単一責任
class CollisionSystem {
  update(entities, deltaTime) {
    // 衝突判定のみに集中
  }
}
```

#### 設計原則
```yaml
必須ルール:
  - 単一責任の原則（各クラスは1つの仕事）
  - 依存性注入（テストしやすい）
  - イベント駆動（疎結合）

禁止事項:
  - グローバル変数
  - 循環参照
  - 500行を超えるファイル
```

### 2. 最初から正しい衝突判定システム

#### ❌ 悪い例
```javascript
// 後付けの雑な衝突判定
if (player.x < enemy.x + enemy.width &&
    player.x + player.width > enemy.x) {
  // なんか当たった...
}
```

#### ✅ 良い例
```javascript
// 専用の衝突判定システム
class CollisionSystem {
  constructor() {
    this.quadTree = new QuadTree(0, 0, 800, 600);
    this.collisionPairs = new Map();
  }

  // 衝突判定を登録
  registerCollisionPair(typeA, typeB, callback) {
    const key = `${typeA}-${typeB}`;
    this.collisionPairs.set(key, callback);
  }

  update(entities) {
    // 空間分割で高速化
    this.quadTree.clear();
    entities.forEach(entity => {
      this.quadTree.insert(entity);
    });

    // 近くのエンティティのみチェック
    entities.forEach(entity => {
      const nearby = this.quadTree.retrieve(entity);
      nearby.forEach(other => {
        if (this.checkCollision(entity, other)) {
          this.handleCollision(entity, other);
        }
      });
    });
  }

  checkCollision(a, b) {
    // AABB衝突判定（Axis-Aligned Bounding Box）
    return !(a.right < b.left ||
             a.left > b.right ||
             a.bottom < b.top ||
             a.top > b.bottom);
  }

  handleCollision(a, b) {
    const key = `${a.type}-${b.type}`;
    const callback = this.collisionPairs.get(key);
    if (callback) {
      callback(a, b);
    }
  }
}

// 使用例
collision.registerCollisionPair('player', 'enemy', (player, enemy) => {
  player.takeDamage(enemy.damage);
});

collision.registerCollisionPair('bullet', 'enemy', (bullet, enemy) => {
  enemy.takeDamage(bullet.damage);
  bullet.destroy();
});
```

### 3. デバッグ可能な構造

#### 必須のデバッグ機能
```javascript
class DebugSystem {
  constructor() {
    this.enabled = true;
    this.showCollisionBoxes = false;
    this.showFPS = true;
    this.showEntityCount = true;
    this.logs = [];
  }

  // デバッグ情報の描画
  render(ctx, game) {
    if (!this.enabled) return;

    // FPS表示
    if (this.showFPS) {
      ctx.fillStyle = 'white';
      ctx.font = '16px monospace';
      ctx.fillText(`FPS: ${game.fps}`, 10, 20);
    }

    // エンティティ数
    if (this.showEntityCount) {
      ctx.fillText(`Entities: ${game.entities.length}`, 10, 40);
      ctx.fillText(`Bullets: ${game.bullets.length}`, 10, 60);
    }

    // 衝突ボックス表示
    if (this.showCollisionBoxes) {
      ctx.strokeStyle = 'red';
      game.entities.forEach(entity => {
        ctx.strokeRect(
          entity.x - entity.width/2,
          entity.y - entity.height/2,
          entity.width,
          entity.height
        );
      });
    }

    // ログ表示
    this.logs.slice(-5).forEach((log, i) => {
      ctx.fillText(log, 10, 100 + i * 20);
    });
  }

  // キーボードショートカット
  setupKeyboardShortcuts() {
    document.addEventListener('keydown', (e) => {
      switch(e.key) {
        case 'F1':
          this.enabled = !this.enabled;
          break;
        case 'F2':
          this.showCollisionBoxes = !this.showCollisionBoxes;
          break;
        case 'F3':
          this.pauseGame();
          break;
        case 'F4':
          this.stepFrame();
          break;
      }
    });
  }

  log(message, type = 'info') {
    const timestamp = performance.now().toFixed(2);
    const logMessage = `[${timestamp}] ${type}: ${message}`;
    this.logs.push(logMessage);
    console.log(logMessage);
  }
}
```

### 4. パフォーマンスの最適化

#### オブジェクトプール
```javascript
class ObjectPool {
  constructor(createFn, resetFn, initialSize = 10) {
    this.createFn = createFn;
    this.resetFn = resetFn;
    this.pool = [];
    this.active = [];

    // 初期プール作成
    for (let i = 0; i < initialSize; i++) {
      this.pool.push(this.createFn());
    }
  }

  acquire() {
    let obj;
    if (this.pool.length > 0) {
      obj = this.pool.pop();
    } else {
      obj = this.createFn();
      console.warn('Pool exhausted, creating new object');
    }
    this.active.push(obj);
    return obj;
  }

  release(obj) {
    const index = this.active.indexOf(obj);
    if (index !== -1) {
      this.active.splice(index, 1);
      this.resetFn(obj);
      this.pool.push(obj);
    }
  }

  releaseAll() {
    this.active.forEach(obj => {
      this.resetFn(obj);
      this.pool.push(obj);
    });
    this.active = [];
  }
}

// 使用例：弾丸プール
const bulletPool = new ObjectPool(
  () => new Bullet(),
  (bullet) => bullet.reset(),
  100 // 最大100個の弾丸を事前作成
);
```

#### レンダリング最適化
```javascript
class RenderOptimizer {
  constructor() {
    this.offscreenCanvas = document.createElement('canvas');
    this.offscreenCtx = this.offscreenCanvas.getContext('2d');
    this.layerCanvases = new Map();
  }

  // レイヤー別レンダリング
  renderLayer(layerName, drawFn) {
    if (!this.layerCanvases.has(layerName)) {
      const canvas = document.createElement('canvas');
      canvas.width = 800;
      canvas.height = 600;
      this.layerCanvases.set(layerName, {
        canvas,
        ctx: canvas.getContext('2d'),
        dirty: true
      });
    }

    const layer = this.layerCanvases.get(layerName);
    if (layer.dirty) {
      layer.ctx.clearRect(0, 0, 800, 600);
      drawFn(layer.ctx);
      layer.dirty = false;
    }

    return layer.canvas;
  }

  // ビューポートカリング
  isInViewport(entity, viewport) {
    return entity.x + entity.width > viewport.x &&
           entity.x < viewport.x + viewport.width &&
           entity.y + entity.height > viewport.y &&
           entity.y < viewport.y + viewport.height;
  }
}
```

### 5. ビジュアルエフェクトの統合

#### エフェクトシステム
```javascript
class EffectSystem {
  constructor() {
    this.effects = [];
    this.particlePools = new Map();
  }

  // エフェクト登録
  registerEffect(name, config) {
    this.particlePools.set(name, {
      pool: new ObjectPool(
        () => new Particle(),
        (p) => p.reset(),
        config.poolSize || 50
      ),
      config
    });
  }

  // エフェクト生成
  spawn(effectName, x, y, options = {}) {
    const effectConfig = this.particlePools.get(effectName);
    if (!effectConfig) {
      console.warn(`Effect ${effectName} not found`);
      return;
    }

    const effect = {
      name: effectName,
      x, y,
      particles: [],
      lifetime: 0,
      maxLifetime: effectConfig.config.duration || 1000
    };

    // パーティクル生成
    for (let i = 0; i < effectConfig.config.particleCount; i++) {
      const particle = effectConfig.pool.pool.acquire();
      this.initializeParticle(particle, effectConfig.config, x, y);
      effect.particles.push(particle);
    }

    this.effects.push(effect);
    return effect;
  }

  update(deltaTime) {
    this.effects = this.effects.filter(effect => {
      effect.lifetime += deltaTime;

      // パーティクル更新
      effect.particles = effect.particles.filter(particle => {
        particle.update(deltaTime);
        return particle.alive;
      });

      // エフェクト終了判定
      return effect.lifetime < effect.maxLifetime &&
             effect.particles.length > 0;
    });
  }

  render(ctx) {
    // ブレンドモード設定
    ctx.save();
    ctx.globalCompositeOperation = 'lighter';

    this.effects.forEach(effect => {
      effect.particles.forEach(particle => {
        particle.render(ctx);
      });
    });

    ctx.restore();
  }
}

// 事前定義エフェクト
effectSystem.registerEffect('explosion', {
  particleCount: 30,
  duration: 1000,
  speed: { min: 50, max: 200 },
  size: { min: 2, max: 8 },
  color: ['#ff6600', '#ffcc00', '#ff0000'],
  fadeOut: true
});

effectSystem.registerEffect('hit', {
  particleCount: 10,
  duration: 300,
  speed: { min: 20, max: 60 },
  size: { min: 1, max: 3 },
  color: ['#ffffff', '#ffff00']
});
```

## 📊 アーキテクチャ全体図

```javascript
// main.js - エントリーポイント
class Game {
  constructor() {
    // コアシステム
    this.systems = {
      input: new InputSystem(),
      physics: new PhysicsSystem(),
      collision: new CollisionSystem(),
      effect: new EffectSystem(),
      render: new RenderSystem(),
      debug: new DebugSystem()
    };

    // マネージャー
    this.entityManager = new EntityManager();
    this.stateManager = new StateManager();

    // オブジェクトプール
    this.pools = {
      bullets: new ObjectPool(() => new Bullet(), b => b.reset(), 100),
      enemies: new ObjectPool(() => new Enemy(), e => e.reset(), 50),
      particles: new ObjectPool(() => new Particle(), p => p.reset(), 200)
    };

    // パフォーマンスモニター
    this.performance = new PerformanceMonitor();
  }

  init() {
    // 初期化は順序が重要
    this.systems.collision.init();
    this.systems.effect.init();
    this.systems.render.init();
    this.systems.debug.setupKeyboardShortcuts();

    // 衝突ペア登録
    this.registerCollisions();
  }

  registerCollisions() {
    const c = this.systems.collision;
    c.registerPair('player', 'enemy', this.onPlayerEnemyCollision.bind(this));
    c.registerPair('bullet', 'enemy', this.onBulletEnemyCollision.bind(this));
    c.registerPair('player', 'powerup', this.onPlayerPowerupCollision.bind(this));
  }

  update(deltaTime) {
    this.performance.startFrame();

    // 固定順序で更新
    this.systems.input.update();
    this.entityManager.update(deltaTime);
    this.systems.physics.update(this.entityManager.entities, deltaTime);
    this.systems.collision.update(this.entityManager.entities);
    this.systems.effect.update(deltaTime);

    this.performance.endFrame();
  }

  render() {
    const ctx = this.canvas.getContext('2d');

    // レイヤー別レンダリング
    this.systems.render.clear(ctx);
    this.systems.render.renderBackground(ctx);
    this.systems.render.renderEntities(ctx, this.entityManager.entities);
    this.systems.render.renderEffects(ctx, this.systems.effect);
    this.systems.render.renderUI(ctx);

    // デバッグ情報（最前面）
    this.systems.debug.render(ctx, this);
  }
}
```

## ✅ チェックリスト

### 設計段階
- [ ] クラス図を作成
- [ ] システム間の依存関係を明確化
- [ ] 各クラスが500行以内

### 実装段階
- [ ] 衝突判定システムが最初から組み込まれている
- [ ] デバッグ機能が有効
- [ ] オブジェクトプールを使用
- [ ] エフェクトシステムが統合されている

### テスト段階
- [ ] 60FPSで安定動作
- [ ] メモリリークがない
- [ ] デバッグ機能で問題特定可能

## 📝 エージェントへの具体的な指示

```
【必須要件】
1. GameCoreクラスは200行以内
2. 各システムは独立したファイル
3. 衝突判定は専用システムとして実装
4. デバッグ機能を最初から含める
5. エフェクトシステムを統合

【禁止事項】
- グローバル変数の使用
- 1000行を超えるファイル
- 衝突判定の後付け
- デバッグ機能なしでのリリース
```