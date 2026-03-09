# 📱 スマートフォン傾き操作ゲーム実装ガイド

## 🎮 概要

スマートフォンの傾きセンサー（ジャイロ/加速度センサー）を使用した直感的なゲーム操作の実装仕様。
横画面（ランドスケープ）での操作に特化し、デバイスの傾きを自然な動きに変換します。

## 🎯 基本仕様

### デバイス設定
- **画面向き**: 横向き（ランドスケープモード）必須
- **操作方式**: デバイスの傾き（DeviceOrientation API）
- **対応デバイス**: iOS/Android スマートフォン・タブレット

### 操作マッピング（横画面時）

```javascript
// 横画面での直感的な操作対応
// ユーザーがデバイスを横に持った状態での動き
const tiltMapping = {
  right: 'moveUp',    // 右に傾ける → キャラが上へ
  left: 'moveDown',   // 左に傾ける → キャラが下へ
  forward: 'moveRight', // 前に傾ける → キャラが右へ
  back: 'moveLeft'    // 手前に傾ける → キャラが左へ
};
```

## 🔧 技術実装

### 1. DeviceOrientation API の初期化

```javascript
class TiltController {
  constructor() {
    this.beta = 0;  // 前後の傾き（-180〜180度）
    this.gamma = 0; // 左右の傾き（-90〜90度）
    this.sensitivity = 2.0;
    this.deadZone = 5;
    this.maxTilt = 30;
    this.isLandscape = false;
    this.permissionGranted = false;
  }

  async init() {
    // iOS 13+ の権限処理
    if (typeof DeviceOrientationEvent.requestPermission === 'function') {
      try {
        const permission = await DeviceOrientationEvent.requestPermission();
        this.permissionGranted = (permission === 'granted');
      } catch (error) {
        console.warn('傾きセンサーの権限が取得できません:', error);
        this.enableFallbackControls();
      }
    } else {
      // Android や古いiOSは権限不要
      this.permissionGranted = true;
    }

    if (this.permissionGranted) {
      this.setupTiltControls();
    }
  }

  setupTiltControls() {
    window.addEventListener('deviceorientation', (event) => {
      this.handleTilt(event);
    });

    // 画面向き検出
    window.addEventListener('resize', () => {
      this.checkOrientation();
    });
    this.checkOrientation();
  }

  checkOrientation() {
    this.isLandscape = window.innerWidth > window.innerHeight;
    if (!this.isLandscape) {
      this.showRotatePrompt();
    }
  }

  handleTilt(event) {
    if (!this.isLandscape) return;

    const { beta, gamma } = event;

    // デッドゾーン処理
    const adjustedBeta = Math.abs(beta) < this.deadZone ? 0 : beta;
    const adjustedGamma = Math.abs(gamma) < this.deadZone ? 0 : gamma;

    // 横画面時の軸変換（重要！）
    // Beta → X軸（左右移動）
    // Gamma → Y軸（上下移動）
    this.tiltX = (adjustedBeta / this.maxTilt) * this.sensitivity;
    this.tiltY = -(adjustedGamma / this.maxTilt) * this.sensitivity;

    // 値を-1〜1の範囲にクランプ
    this.tiltX = Math.max(-1, Math.min(1, this.tiltX));
    this.tiltY = Math.max(-1, Math.min(1, this.tiltY));
  }

  getTiltInput() {
    return {
      x: this.tiltX || 0,
      y: this.tiltY || 0
    };
  }
}
```

### 2. タッチ操作の統合

```javascript
class TouchController {
  constructor(canvas) {
    this.canvas = canvas;
    this.touches = new Map();
    this.setupTouchEvents();
  }

  setupTouchEvents() {
    // タップで攻撃
    this.canvas.addEventListener('touchstart', (e) => {
      e.preventDefault();
      const touchCount = e.touches.length;

      if (touchCount === 1) {
        this.onPrimaryAction(); // 通常攻撃
      } else if (touchCount === 2) {
        this.onSecondaryAction(); // 特殊攻撃
      }

      // タッチ位置を記録
      for (let touch of e.touches) {
        this.touches.set(touch.identifier, {
          x: touch.clientX,
          y: touch.clientY,
          startTime: Date.now()
        });
      }
    });

    // 連続攻撃の処理
    this.canvas.addEventListener('touchmove', (e) => {
      e.preventDefault();
      // 必要に応じてドラッグ操作を実装
    });

    this.canvas.addEventListener('touchend', (e) => {
      e.preventDefault();
      for (let touch of e.changedTouches) {
        this.touches.delete(touch.identifier);
      }
    });
  }

  onPrimaryAction() {
    // ゲームロジックにイベントを送信
    game.player.shoot();
  }

  onSecondaryAction() {
    // 特殊攻撃の実行
    game.player.specialAttack();
  }
}
```

### 3. フォールバック操作

```javascript
class FallbackController {
  constructor(canvas) {
    this.canvas = canvas;
    this.virtualJoystick = null;
  }

  enable() {
    // センサーが使えない場合の代替操作
    this.createVirtualJoystick();
    this.createTouchZones();
  }

  createVirtualJoystick() {
    // バーチャルジョイスティックの実装
    const joystick = document.createElement('div');
    joystick.className = 'virtual-joystick';
    joystick.innerHTML = `
      <div class="joystick-base">
        <div class="joystick-stick"></div>
      </div>
    `;
    document.body.appendChild(joystick);

    // タッチイベントでジョイスティックを操作
    this.setupJoystickEvents(joystick);
  }

  createTouchZones() {
    // 画面を6分割したタップエリア
    const zones = [
      { x: 0, y: 0, w: 0.33, h: 0.5, action: 'upLeft' },
      { x: 0.33, y: 0, w: 0.34, h: 0.5, action: 'up' },
      { x: 0.67, y: 0, w: 0.33, h: 0.5, action: 'upRight' },
      { x: 0, y: 0.5, w: 0.33, h: 0.5, action: 'downLeft' },
      { x: 0.33, y: 0.5, w: 0.34, h: 0.5, action: 'down' },
      { x: 0.67, y: 0.5, w: 0.33, h: 0.5, action: 'downRight' }
    ];

    // タッチゾーンのビジュアル表示（デバッグ用）
    if (DEBUG_MODE) {
      this.showTouchZones(zones);
    }
  }
}
```

### 4. 統合実装例

```javascript
class MobileTiltGame {
  constructor() {
    this.canvas = document.getElementById('gameCanvas');
    this.tiltController = new TiltController();
    this.touchController = new TouchController(this.canvas);
    this.fallbackController = new FallbackController(this.canvas);
    this.player = null;
    this.isRunning = false;
  }

  async init() {
    // 画面設定
    this.setupCanvas();

    // 傾き操作の初期化
    await this.tiltController.init();

    // 権限が得られなかった場合はフォールバック
    if (!this.tiltController.permissionGranted) {
      this.fallbackController.enable();
    }

    // 操作説明の表示
    this.showTutorial();

    // ゲーム開始
    setTimeout(() => {
      this.start();
    }, 3000);
  }

  setupCanvas() {
    // 横画面を強制
    if ('orientation' in screen && screen.orientation.lock) {
      screen.orientation.lock('landscape').catch(err => {
        console.log('画面回転のロックはサポートされていません');
      });
    }

    // キャンバスサイズ調整
    this.resizeCanvas();
    window.addEventListener('resize', () => this.resizeCanvas());
  }

  resizeCanvas() {
    this.canvas.width = window.innerWidth;
    this.canvas.height = window.innerHeight;
  }

  showTutorial() {
    const tutorial = document.createElement('div');
    tutorial.className = 'tutorial-overlay';
    tutorial.innerHTML = `
      <div class="tutorial-content">
        <h2>📱 操作方法</h2>
        <div class="tilt-demo">
          <img src="tilt-animation.gif" alt="傾き操作">
          <p>デバイスを傾けて移動</p>
        </div>
        <div class="tap-demo">
          <img src="tap-animation.gif" alt="タップ操作">
          <p>画面タップで攻撃</p>
        </div>
        <p class="start-hint">3秒後に開始します...</p>
      </div>
    `;
    document.body.appendChild(tutorial);

    setTimeout(() => {
      tutorial.remove();
    }, 3000);
  }

  start() {
    this.isRunning = true;
    this.gameLoop();
  }

  gameLoop() {
    if (!this.isRunning) return;

    // 傾き入力を取得
    const tiltInput = this.tiltController.getTiltInput();

    // プレイヤー移動
    if (this.player) {
      this.player.move(tiltInput.x, tiltInput.y);
    }

    // 描画とアップデート
    this.update();
    this.render();

    requestAnimationFrame(() => this.gameLoop());
  }

  update() {
    // ゲームロジックの更新
  }

  render() {
    // 描画処理
    const ctx = this.canvas.getContext('2d');

    // 傾きインジケーター表示
    if (DEBUG_MODE) {
      this.renderTiltIndicator(ctx);
    }
  }

  renderTiltIndicator(ctx) {
    // 現在の傾きを視覚的に表示
    const tiltInput = this.tiltController.getTiltInput();
    const centerX = 50;
    const centerY = 50;
    const radius = 30;

    ctx.save();
    ctx.strokeStyle = 'rgba(255, 255, 255, 0.5)';
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.arc(centerX, centerY, radius, 0, Math.PI * 2);
    ctx.stroke();

    // 傾き方向を点で表示
    ctx.fillStyle = 'red';
    ctx.beginPath();
    ctx.arc(
      centerX + tiltInput.x * radius,
      centerY + tiltInput.y * radius,
      5, 0, Math.PI * 2
    );
    ctx.fill();
    ctx.restore();
  }
}

// ゲーム起動
const game = new MobileTiltGame();
game.init();
```

## 📋 実装チェックリスト

### 必須機能
- [ ] DeviceOrientation APIの権限処理（iOS 13+）
- [ ] 横画面検出と対応
- [ ] 軸変換（Beta/Gamma → X/Y）
- [ ] デッドゾーン処理
- [ ] 感度調整
- [ ] タッチ操作の統合
- [ ] フォールバック操作

### UX要素
- [ ] 操作チュートリアル（初回3秒表示）
- [ ] 傾きインジケーター
- [ ] 画面回転プロンプト
- [ ] キャリブレーション機能

### テスト項目
- [ ] iOS Safari動作確認
- [ ] Android Chrome動作確認
- [ ] 権限拒否時のフォールバック
- [ ] 画面回転時の挙動
- [ ] バックグラウンド復帰
- [ ] パフォーマンス（60FPS維持）

## ⚠️ 注意事項

### 1. 軸の混乱を避ける
横画面では Beta と Gamma の意味が変わるため、必ず変換処理を実装すること。

### 2. ブラウザ差異
Safari と Chrome で DeviceOrientation の値が異なる場合があるため、実機テストは必須。

### 3. パフォーマンス
deviceorientation イベントは高頻度で発火するため、スロットリングやデバウンスを検討。

```javascript
// スロットリングの例
let lastUpdate = 0;
const UPDATE_INTERVAL = 16; // 60FPS

window.addEventListener('deviceorientation', (event) => {
  const now = Date.now();
  if (now - lastUpdate < UPDATE_INTERVAL) return;
  lastUpdate = now;
  handleTilt(event);
});
```

## 🎮 推奨パラメータ

```javascript
const RECOMMENDED_SETTINGS = {
  sensitivity: 2.0,      // 感度（1.0〜3.0）
  deadZone: 5,          // デッドゾーン（度）
  maxTilt: 30,          // 最大傾き角度（度）
  smoothing: 0.2,       // スムージング係数（0〜1）
  invertX: false,       // X軸反転
  invertY: false        // Y軸反転
};
```