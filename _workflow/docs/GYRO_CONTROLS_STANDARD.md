# ジャイロ（傾き）操作の標準実装ガイド v2.0

## 概要
iOS 18以降でも確実に動作するジャイロセンサー操作の実装ガイド。メニュー画面でもゲーム中でも、ユーザージェスチャー内なら許可ポップアップを表示可能。

## 🎯 成功実装の核心ポイント

### 1. **ユーザージェスチャー内での許可取得が必須**
- **clickまたはtouchendイベント内で直接**`requestPermission()`を呼ぶ
- メニュー画面でもゲーム中でも、ユーザーのタップ/クリック内なら動作
- GyroControlsクラス経由ではなく、UIイベントハンドラから直接呼び出す
- ❌ touchstartイベントは使用不可（touchendまたはclickを使用）

### 2. **許可取得のタイミング選択肢**
- **Option A**: メニュー画面に専用の許可ボタンを配置
- **Option B**: ゲーム中の操作モード切り替えで許可取得
- **Option C**: 初回起動時のチュートリアルで許可取得
- いずれも技術的に可能、UXデザインの選択

## 📝 AIへの実装依頼プロンプト

```
以下の仕様でスマートフォンの傾き操作機能を実装してください：

### 必須要件
1. iOS 18対応のDeviceOrientationEvent許可取得
2. Android/PCでの自動検出と対応
3. 横向き・縦向きの両方に対応
4. ユーザーのタップ/クリックイベント内で許可要求
5. touchendまたはclickイベントを使用（touchstartは不可）

### 実装構成

#### 1. GyroControls.js の作成
以下の機能を持つクラスを実装：

```javascript
export class GyroControls {
  constructor() {
    this.enabled = false;
    this.permissionGranted = false; // 外部からアクセス可能

    // 傾き値 (-1 ~ 1)
    this.tiltX = 0;
    this.tiltY = 0;

    // 感度設定（最適化済み）
    this.sensitivity = 3.5;  // 高感度
    this.deadZone = 2;       // 小さいデッドゾーン
    this.maxTilt = 20;       // 必要な傾き角度を抑制

    this.isAvailable = window.DeviceOrientationEvent !== undefined;
  }

  async init() {
    if (!this.isAvailable) return false;

    // Android/古いiOSは自動許可
    if (typeof DeviceOrientationEvent.requestPermission !== 'function') {
      this.permissionGranted = true;
      this.enable();
      return true;
    }

    // iOS 13+はUIから呼ぶのでここでは何もしない
    return false;
  }

  enable() {
    if (!this.permissionGranted) return;
    this.enabled = true;
    window.addEventListener('deviceorientation', this.handleOrientation.bind(this));
  }

  handleOrientation(event) {
    const { beta, gamma } = event;
    if (beta === null || gamma === null) return;

    const isLandscape = window.innerWidth > window.innerHeight;

    // デッドゾーン適用
    let adjustedBeta = Math.abs(beta) > this.deadZone ? beta : 0;
    let adjustedGamma = Math.abs(gamma) > this.deadZone ? gamma : 0;

    // 最大傾き制限
    adjustedBeta = Math.max(-this.maxTilt, Math.min(this.maxTilt, adjustedBeta));
    adjustedGamma = Math.max(-this.maxTilt, Math.min(this.maxTilt, adjustedGamma));

    if (isLandscape) {
      // 横向き：軸の入れ替えと反転
      this.tiltX = (adjustedBeta / this.maxTilt) * this.sensitivity;
      this.tiltY = -(adjustedGamma / this.maxTilt) * this.sensitivity;
    } else {
      // 縦向き：通常マッピング
      this.tiltX = (adjustedGamma / this.maxTilt) * this.sensitivity;
      this.tiltY = -(adjustedBeta / this.maxTilt) * this.sensitivity;
    }

    // 最終値をクランプ
    this.tiltX = Math.max(-1, Math.min(1, this.tiltX));
    this.tiltY = Math.max(-1, Math.min(1, this.tiltY));
  }

  getAxis() {
    return { x: this.tiltX, y: this.tiltY };
  }
}
```

#### 2. 実装パターンA: メニュー画面での許可取得

```javascript
// MenuScreen.js - タイトル画面での実装
export class MenuScreen {
  constructor() {
    this.gyroButton = null;
  }

  createGyroPermissionButton() {
    const button = document.createElement('button');
    button.className = 'gyro-permission-btn';
    button.innerHTML = '📱 傾き操作を有効にする';
    button.style.cssText = `
      padding: 20px 40px;
      font-size: 18px;
      background: #FFD700;
      border: none;
      border-radius: 10px;
      cursor: pointer;
      animation: pulse 2s infinite;
    `;

    // 重要: clickイベント内で直接requestPermissionを呼ぶ
    button.addEventListener('click', async () => {
      if (typeof DeviceOrientationEvent.requestPermission === 'function') {
        try {
          // iOS 13+: ユーザージェスチャー内で直接呼び出す
          const permission = await DeviceOrientationEvent.requestPermission();

          if (permission === 'granted') {
            button.innerHTML = '✅ 傾き操作 ON';
            button.style.background = '#4CAF50';
            // GyroControlsを有効化
            window.gyroControls.permissionGranted = true;
            window.gyroControls.enable();
          } else {
            button.innerHTML = '❌ 拒否されました';
            this.showPermissionHelp();
          }
        } catch (error) {
          console.error('Permission error:', error);
        }
      } else {
        // Android/PC: 自動的に有効
        window.gyroControls.init();
        button.innerHTML = '✅ 傾き操作対応';
      }
    });

    return button;
  }

  showPermissionHelp() {
    const helpText = `
      傾き操作を有効にするには：
      1. Safari設定 → プライバシーとセキュリティ
      2. モーションと向きのアクセス → オン
      3. ページをリロード
    `;
    // ヘルプ表示処理
  }
}
```

#### 3. 実装パターンB: ゲーム中の操作モード切り替え

```javascript
// InputSystem.js - ゲーム中での実装
export class InputSystem {
  constructor(canvas) {
    this.canvas = canvas;
    this.gyroControls = new GyroControls();
    this.touchZoneControls = new TouchZoneControls(canvas);
    this.mobileControlMode = 'touchZone'; // 初期値はタッチ操作
    this.isMobile = this.detectMobile();
  }

  init() {
    if (this.isMobile) {
      this.touchZoneControls.enable();

      // Android/古いiOSはジャイロを自動初期化
      this.gyroControls.init().then(success => {
        if (success) {
          console.log('Gyro available - user can switch');
        }
      });
    }
  }

  // タッチエンドイベントでの操作モード切り替え
  handleControlModeTap(x, y) {
    // 切り替えボタンの領域判定
    const switcherY = 50;
    const modes = ['gyro', 'touchZone'];

    if (y >= switcherY - 15 && y <= switcherY + 15) {
      modes.forEach((mode, i) => {
        const buttonX = this.canvas.width - 140 + (i * 90);

        if (x >= buttonX - 40 && x <= buttonX + 40) {
          if (mode === 'gyro') {
            // iOS向け：タップイベント内で直接許可要求
            this.requestGyroPermission();
          } else {
            this.switchToTouchMode();
          }
        }
      });
    }
  }

  async requestGyroPermission() {
    // iOS 13+の場合、ここで直接許可を要求
    if (typeof DeviceOrientationEvent.requestPermission === 'function') {
      try {
        // タップイベントのコンテキスト内で直接呼ぶ（重要！）
        const permission = await DeviceOrientationEvent.requestPermission();

        if (permission === 'granted') {
          // 許可成功
          this.gyroControls.permissionGranted = true;
          this.gyroControls.enable();
          this.touchZoneControls.disable();
          this.mobileControlMode = 'gyro';
          this.showMessage('✅ 傾き操作ON');
        } else {
          // 拒否された場合
          this.showMessage('❌ 許可が必要です\\nSafari設定をリセットしてください');
        }
      } catch (error) {
        console.error('Permission error:', error);
      }
    } else {
      // Android/PCは即座に切り替え
      if (this.gyroControls.permissionGranted) {
        this.gyroControls.enable();
        this.touchZoneControls.disable();
        this.mobileControlMode = 'gyro';
      }
    }
  }

  // 操作モード切り替えボタンのレンダリング
  renderControlModeSwitcher(ctx) {
    if (!this.isMobile || !this.isInGame()) return;

    const y = 50;
    const modes = ['gyro', 'touchZone'];
    const labels = ['🎯 傾き操作', '👆 タッチ操作'];

    // タイトル
    ctx.fillStyle = 'rgba(255, 255, 255, 0.8)';
    ctx.font = 'bold 14px Arial';
    ctx.fillText('操作モード:', this.canvas.width - 120, y - 20);

    // モード切り替えボタン
    modes.forEach((mode, i) => {
      const x = this.canvas.width - 140 + (i * 90);
      const isActive = this.mobileControlMode === mode;

      // ボタン背景
      ctx.fillStyle = isActive ? 'rgba(0, 255, 100, 0.5)' : 'rgba(0, 0, 0, 0.5)';
      ctx.fillRect(x - 40, y - 15, 80, 30);

      // ボーダー
      ctx.strokeStyle = isActive ? '#00FF00' : '#666666';
      ctx.lineWidth = 2;
      ctx.strokeRect(x - 40, y - 15, 80, 30);

      // ラベル
      ctx.font = isActive ? 'bold 12px Arial' : '12px Arial';
      ctx.fillStyle = isActive ? '#00FF00' : '#CCCCCC';
      ctx.textAlign = 'center';
      ctx.fillText(labels[i], x, y);
    });
  }
}
```

#### 3. 初回起動時のガイダンス表示

GyroControlsクラスに初回メッセージを追加：

```javascript
renderDebug(ctx) {
  if (!this.enabled) return;

  // 初回のみ操作説明を表示
  if (this.showInitialMessage) {
    ctx.fillStyle = 'rgba(0, 0, 0, 0.7)';
    ctx.fillRect(ctx.canvas.width/2 - 150, ctx.canvas.height/2 - 60, 300, 120);

    ctx.fillStyle = 'rgba(255, 255, 255, 0.9)';
    ctx.font = 'bold 16px Arial';
    ctx.textAlign = 'center';
    ctx.fillText('🎮 傾き操作モード', ctx.canvas.width/2, ctx.canvas.height/2 - 30);
    ctx.fillText('デバイスを傾けて移動', ctx.canvas.width/2, ctx.canvas.height/2);
    ctx.fillText('タップで攻撃', ctx.canvas.width/2, ctx.canvas.height/2 + 20);

    setTimeout(() => {
      this.showInitialMessage = false;
    }, 3000);
  }

  // デバッグ情報（小さく表示）
  ctx.fillStyle = 'rgba(255, 255, 255, 0.5)';
  ctx.font = '10px Arial';
  ctx.fillText(`X: ${this.tiltX.toFixed(2)} Y: ${this.tiltY.toFixed(2)}`, 10, 30);
}
```

### 重要な実装ポイント

#### ✅ 成功の鍵
1. **ユーザーのタップ/クリックイベント内で直接**`requestPermission()`を呼ぶ
2. `touchend`または`click`イベントを使用（`touchstart`は不可）
3. イベントハンドラの**最初に同期的に**呼び出す
4. Android/PCは自動検出して有効化
5. メニュー画面でもゲーム中でも、ユーザージェスチャー内なら動作

#### ❌ 避けるべき実装
1. ページロード時の自動実行
2. GyroControlsクラス内での許可要求（非同期処理チェーンが深い）
3. `setTimeout`や`Promise`チェーンの深い階層での実行
4. `touchstart`イベントでの許可要求

### テスト確認項目
- [ ] iPhone（iOS 18）で許可ポップアップが表示される（メニュー/ゲーム中どちらでも）
- [ ] 許可後、傾き操作が正常に動作する
- [ ] Androidでは自動的にジャイロが利用可能になる
- [ ] 横向き・縦向きの両方で正しく動作する
- [ ] 操作モード切り替えがスムーズに行える
- [ ] 拒否後の再要求時の案内が表示される
```

## 🔧 トラブルシューティング

### iOS 18でポップアップが出ない場合

1. **原因**: ユーザージェスチャー外での`requestPermission()`呼び出し
   - **解決**: clickまたはtouchendイベントハンドラ内で直接呼び出す

2. **原因**: 非同期処理チェーンの深い階層での呼び出し
   - **解決**: イベントハンドラの最初に同期的に呼び出す

3. **原因**: touchstartイベントの使用
   - **解決**: touchendまたはclickイベントを使用する

### 一度拒否すると再度許可できない

**解決手順**:
1. Safari設定 → プライバシーとセキュリティ
2. モーションと向きのアクセス → オフ→オン
3. または、Safari設定 → 詳細 → Webサイトデータを削除

### 横向きで操作が逆になる

**原因**: デバイスの座標系が回転に対応していない
**解決**: `isLandscape`判定して軸マッピングを切り替える（上記コード参照）

## 📊 実装の違い比較

| 項目 | 失敗する実装 | 成功する実装 |
|------|-------------|-------------|
| 許可要求タイミング | ページロード時/初期化時 | ユーザーのタップ/クリック時 |
| イベントタイプ | touchstart | touchend/click |
| 許可要求方法 | GyroControls.init()内 | UIイベントハンドラで直接 |
| 実装場所 | クラス内部/非同期チェーン | イベントハンドラの最初 |
| メニュー画面対応 | × (誤解) | ✓ (ユーザージェスチャー内なら可能) |
| iOS 18対応 | × | ✓ |

## 🕹️ バーチャルジョイスティック・フォールバック実装

### 概要
ジャイロ許可が取得できない場合の完璧なフォールバック戦略として、画面右端にバーチャルジョイスティックを表示します。

### 実装要件

#### 1. VirtualJoystick.js の作成

```javascript
export class VirtualJoystick {
  constructor(canvas) {
    this.canvas = canvas;
    this.enabled = false;

    // ジョイスティック位置（右端）
    this.baseX = canvas.width - 80;  // 右端から80px
    this.baseY = canvas.height - 100; // 下から100px
    this.baseRadius = 40;

    // スティック位置
    this.stickX = this.baseX;
    this.stickY = this.baseY;
    this.stickRadius = 20;
    this.maxDistance = 35;

    // 入力値
    this.inputX = 0;
    this.inputY = 0;

    // タッチ状態
    this.touchId = null;
    this.touching = false;
  }

  enable() {
    this.enabled = true;
    this.canvas.addEventListener('touchstart', this.handleTouchStart.bind(this));
    this.canvas.addEventListener('touchmove', this.handleTouchMove.bind(this));
    this.canvas.addEventListener('touchend', this.handleTouchEnd.bind(this));
  }

  disable() {
    this.enabled = false;
    this.touching = false;
    this.inputX = 0;
    this.inputY = 0;
    // イベントリスナー削除
    this.canvas.removeEventListener('touchstart', this.handleTouchStart.bind(this));
    this.canvas.removeEventListener('touchmove', this.handleTouchMove.bind(this));
    this.canvas.removeEventListener('touchend', this.handleTouchEnd.bind(this));
  }

  handleTouchStart(e) {
    if (!this.enabled) return;

    const touch = e.touches[0];
    const rect = this.canvas.getBoundingClientRect();
    const x = touch.clientX - rect.left;
    const y = touch.clientY - rect.top;

    // ジョイスティックベース範囲内か判定
    const distance = Math.hypot(x - this.baseX, y - this.baseY);

    if (distance <= this.baseRadius + 20) {
      this.touchId = touch.identifier;
      this.touching = true;
      this.updateStickPosition(x, y);
      e.preventDefault();
    }
  }

  handleTouchMove(e) {
    if (!this.enabled || !this.touching) return;

    for (let touch of e.touches) {
      if (touch.identifier === this.touchId) {
        const rect = this.canvas.getBoundingClientRect();
        const x = touch.clientX - rect.left;
        const y = touch.clientY - rect.top;
        this.updateStickPosition(x, y);
        e.preventDefault();
        break;
      }
    }
  }

  handleTouchEnd(e) {
    if (!this.enabled || !this.touching) return;

    // 該当するタッチが終了したか確認
    let found = false;
    for (let touch of e.touches) {
      if (touch.identifier === this.touchId) {
        found = true;
        break;
      }
    }

    if (!found) {
      this.touching = false;
      this.touchId = null;
      this.stickX = this.baseX;
      this.stickY = this.baseY;
      this.inputX = 0;
      this.inputY = 0;
    }
  }

  updateStickPosition(x, y) {
    const dx = x - this.baseX;
    const dy = y - this.baseY;
    const distance = Math.hypot(dx, dy);

    if (distance <= this.maxDistance) {
      this.stickX = x;
      this.stickY = y;
    } else {
      const angle = Math.atan2(dy, dx);
      this.stickX = this.baseX + Math.cos(angle) * this.maxDistance;
      this.stickY = this.baseY + Math.sin(angle) * this.maxDistance;
    }

    // 入力値を計算 (-1 ~ 1)
    this.inputX = (this.stickX - this.baseX) / this.maxDistance;
    this.inputY = (this.stickY - this.baseY) / this.maxDistance;
  }

  getAxis() {
    return { x: this.inputX, y: this.inputY };
  }

  render(ctx) {
    if (!this.enabled) return;

    // ベース（半透明の円）
    ctx.fillStyle = 'rgba(255, 255, 255, 0.3)';
    ctx.beginPath();
    ctx.arc(this.baseX, this.baseY, this.baseRadius, 0, Math.PI * 2);
    ctx.fill();

    ctx.strokeStyle = 'rgba(255, 255, 255, 0.5)';
    ctx.lineWidth = 2;
    ctx.stroke();

    // スティック（色付き円）
    const color = this.touching ? 'rgba(0, 255, 100, 0.8)' : 'rgba(255, 255, 255, 0.6)';
    ctx.fillStyle = color;
    ctx.beginPath();
    ctx.arc(this.stickX, this.stickY, this.stickRadius, 0, Math.PI * 2);
    ctx.fill();

    ctx.strokeStyle = this.touching ? 'rgba(0, 255, 100, 1)' : 'rgba(255, 255, 255, 0.8)';
    ctx.lineWidth = 3;
    ctx.stroke();

    // 方向指示線（タッチ中のみ）
    if (this.touching) {
      ctx.strokeStyle = 'rgba(0, 255, 100, 0.4)';
      ctx.lineWidth = 2;
      ctx.beginPath();
      ctx.moveTo(this.baseX, this.baseY);
      ctx.lineTo(this.stickX, this.stickY);
      ctx.stroke();
    }
  }
}
```

#### 2. InputSystem.js での統合

```javascript
export class InputSystem {
  constructor(canvas) {
    this.canvas = canvas;
    this.gyroControls = new GyroControls();
    this.virtualJoystick = new VirtualJoystick(canvas);
    this.mobileControlMode = 'joystick'; // 初期値はジョイスティック
    this.isMobile = this.detectMobile();
  }

  init() {
    if (this.isMobile) {
      // モバイルの場合、デフォルトでバーチャルジョイスティックを有効化
      this.virtualJoystick.enable();

      // Android/古いiOSはジャイロを自動初期化（バックグラウンド）
      this.gyroControls.init().then(success => {
        if (success) {
          console.log('✅ Gyro available - user can switch to gyro mode');
        }
      });
    }
  }

  getInput() {
    if (this.isMobile) {
      if (this.mobileControlMode === 'gyro' && this.gyroControls.isEnabled()) {
        return this.gyroControls.getAxis();
      } else {
        // ジャイロ無効時はバーチャルジョイスティック
        return this.virtualJoystick.getAxis();
      }
    } else {
      // PC: キーボード入力
      return this.getKeyboardInput();
    }
  }

  // ジャイロ許可要求（ゲーム中のボタンから呼び出し）
  async requestGyroPermission() {
    if (typeof DeviceOrientationEvent.requestPermission === 'function') {
      try {
        const permission = await DeviceOrientationEvent.requestPermission();

        if (permission === 'granted') {
          // 許可成功 → ジャイロに切り替え
          this.gyroControls.permissionGranted = true;
          this.gyroControls.enable();
          this.virtualJoystick.disable();
          this.mobileControlMode = 'gyro';
          this.showMessage('✅ 傾き操作ON');
          return true;
        } else {
          // 拒否された → ジョイスティックのまま
          this.showMessage('❌ 傾き許可が拒否されました\\nジョイスティックで操作します');
          return false;
        }
      } catch (error) {
        console.error('Gyro permission error:', error);
        return false;
      }
    } else {
      // Android/PCは即座に切り替え
      if (this.gyroControls.permissionGranted) {
        this.gyroControls.enable();
        this.virtualJoystick.disable();
        this.mobileControlMode = 'gyro';
        return true;
      }
    }
    return false;
  }

  // ジョイスティックに戻す
  switchToJoystick() {
    this.gyroControls.disable();
    this.virtualJoystick.enable();
    this.mobileControlMode = 'joystick';
    this.showMessage('🕹️ ジョイスティック操作');
  }

  // レンダリング（ゲームループから呼び出し）
  render(ctx) {
    // モバイルの場合のみ
    if (this.isMobile) {
      // ジョイスティックを描画
      this.virtualJoystick.render(ctx);

      // 操作モード切り替えボタン
      this.renderControlModeSwitcher(ctx);
    }
  }

  renderControlModeSwitcher(ctx) {
    if (!this.isInGame()) return;

    const y = 50;
    const modes = ['gyro', 'joystick'];
    const labels = ['🎯 傾き', '🕹️ スティック'];

    ctx.fillStyle = 'rgba(255, 255, 255, 0.8)';
    ctx.font = 'bold 12px Arial';
    ctx.fillText('操作:', this.canvas.width - 140, y - 20);

    modes.forEach((mode, i) => {
      const x = this.canvas.width - 140 + (i * 70);
      const isActive = this.mobileControlMode === mode;

      ctx.fillStyle = isActive ? 'rgba(0, 255, 100, 0.5)' : 'rgba(0, 0, 0, 0.5)';
      ctx.fillRect(x - 30, y - 12, 60, 24);

      ctx.strokeStyle = isActive ? '#00FF00' : '#666666';
      ctx.lineWidth = 2;
      ctx.strokeRect(x - 30, y - 12, 60, 24);

      ctx.font = isActive ? 'bold 10px Arial' : '10px Arial';
      ctx.fillStyle = isActive ? '#00FF00' : '#CCCCCC';
      ctx.textAlign = 'center';
      ctx.fillText(labels[i], x, y + 2);
    });
  }
}
```

### フォールバック戦略

#### シナリオ1: ジャイロ許可成功（理想）
```
1. メニュー画面で「📱 傾き操作を有効にする」ボタン表示
2. ユーザーがタップ → iOS許可ポップアップ
3. 許可 → ジャイロ操作でゲームプレイ
4. バーチャルジョイスティックは非表示
```

#### シナリオ2: ジャイロ許可拒否（フォールバック）
```
1. メニュー画面で「📱 傾き操作を有効にする」ボタン表示
2. ユーザーがタップ → iOS許可ポップアップ
3. 拒否 → 自動的にバーチャルジョイスティックに切り替え
4. 右端にジョイスティック表示
5. 問題なくゲームプレイ可能
```

#### シナリオ3: ジャイロ許可スキップ
```
1. メニュー画面で「スタート」ボタンのみタップ（ジャイロボタンを無視）
2. ゲーム開始時、自動的にバーチャルジョイスティックを表示
3. 右端にジョイスティック表示
4. 問題なくゲームプレイ可能
5. ゲーム中の切り替えボタンで後からジャイロ許可可能
```

### UX設計の推奨事項

1. **初期状態**: バーチャルジョイスティックを常に用意
2. **ジャイロはオプション**: 「より快適な操作」として提案
3. **シームレスな切り替え**: ゲーム中でも操作モード変更可能
4. **明確なフィードバック**: 現在の操作モードを常に表示

### テスト確認項目
- [ ] ジャイロ許可成功時、ジョイスティックが非表示になる
- [ ] ジャイロ許可拒否時、ジョイスティックが表示される
- [ ] ジョイスティックの操作が滑らか（-1〜1の範囲）
- [ ] ゲーム中の操作モード切り替えが動作する
- [ ] 右端配置でゲーム画面を邪魔しない

## 参考実装
- 成功例: `/Users/tsujisouhei/Desktop/AI-Apps/monster-battles-agent/docs/src/systems/`
- InputSystem.js (handleControlModeTap メソッド)
- GyroControls.js (横向き対応版)