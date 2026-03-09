# SPEC.md - Picture Merge App v2 詳細仕様書

## 1. 機能一覧（優先度付き）

### P0: 必須（リリースブロッカー）

| ID | 機能名 | 概要 |
|----|--------|------|
| F1 | 写真入力（2枚） | D&D/ファイル選択で2枚の人物写真を入力。JPEG/PNG/WebP対応。最大20MB/枚 |
| F2 | 人物セグメンテーション | バックエンドrembg(U2Net)による自動背景除去。透過PNG+BBox+足元座標を返却 |
| F5 | 合成プレビュー | REST APIベースのプレビュー。パラメータ変更時にPOSTリクエストで低解像度プレビューを取得 |
| F6 | 出力・ダウンロード | フル解像度PNG出力。`merged_{timestamp}.png`形式 |

### P1: 重要（初回リリースに含める）

| ID | 機能名 | 概要 |
|----|--------|------|
| F3 | 合成設定パネル | 背景色、出力サイズ、位置、スケール、影、色調補正のパラメータUI |
| F4 | 自動スケール調整 | BBox高さ比較によるインテリジェントスケール自動調整（0.8-1.2倍） |
| F1-HEIC | HEIC/HEIF対応 | pillow-heifによるiPhone写真ネイティブサポート |
| F3-COLOR | 色調補正 | OpenCVヒストグラムマッチングによる色温度・明るさ統一 |
| F5-DRAG | Canvas直接操作 | Canvas上で人物をドラッグして位置調整 |

### P2: Phase 2以降

| ID | 機能名 | 概要 |
|----|--------|------|
| F7 | バッチ処理 | 固定人物1枚+複数写真の一括合成。ZIP出力 |
| F1-PASTE | クリップボード入力 | ペーストによる画像入力 |
| F2-CACHE | セグメンテーションキャッシュ | ハッシュベースの再処理回避 |

---

## 2. 画面遷移図

```
┌──────────────────┐
│   初期状態        │  写真未入力
│   (IDLE)          │  D&Dゾーン2つ表示
└────────┬─────────┘
         │ 写真1をドロップ/選択
         ▼
┌──────────────────┐
│   写真1入力済み    │  写真1サムネイル表示
│   (ONE_UPLOADED)  │  写真2 D&Dゾーン表示
└────────┬─────────┘
         │ 写真2をドロップ/選択
         ▼
┌──────────────────┐
│   セグメンテーション中 │  ローディングスピナー
│   (SEGMENTING)       │  2枚同時に処理
└────────┬─────────────┘
         │ 処理完了
         ▼
┌──────────────────┐
│   プレビュー表示    │  合成プレビュー + 設定パネル
│   (PREVIEW)        │  Canvas操作可能
│                    │  ◀──── パラメータ変更 ────▶
└────────┬─────────┘       (自身にループ)
         │ ダウンロードボタン押下
         ▼
┌──────────────────┐
│   フル解像度合成中  │  ローディング表示
│   (MERGING)        │
└────────┬─────────┘
         │ 完了
         ▼
┌──────────────────┐
│   ダウンロード完了  │  ブラウザのダウンロードダイアログ
│   (COMPLETE)       │  「もう1枚作る」でIDLEに戻る
└──────────────────┘

※ どの状態からも [リセット] ボタンで IDLE に戻れる
```

### 状態一覧

| 状態 | 説明 | UI表示 |
|------|------|--------|
| IDLE | 初期状態。写真未入力 | 2つの空のD&Dゾーン |
| ONE_UPLOADED | 写真1枚入力済み | 1枚のサムネイル + 1つの空D&Dゾーン |
| SEGMENTING | セグメンテーション処理中 | スピナー + プログレス表示 |
| PREVIEW | プレビュー表示中 | Canvas合成プレビュー + 設定パネル |
| MERGING | フル解像度合成中 | スピナー |
| COMPLETE | ダウンロード完了 | 成功メッセージ + リセットボタン |
| ERROR | エラー発生 | エラーメッセージ + リトライ/リセット |

---

## 3. データフロー図

```
[ユーザー操作]
     │
     │  画像ファイル（JPEG/PNG/WebP）
     ▼
┌──────────────────────────────────────────────────┐
│  フロントエンド (React + TypeScript)               │
│                                                    │
│  ┌───────────┐   ┌───────────┐   ┌────────────┐  │
│  │ ImageInput │──▶│FileReader │──▶│ base64変換  │  │
│  │ Component  │   │ API       │   │            │  │
│  └───────────┘   └───────────┘   └──────┬─────┘  │
│                                          │         │
│                          multipart/form-data       │
│                                          │         │
│  ┌───────────────────────────────────────┼────┐   │
│  │  REST API Client (fetch)              │    │   │
│  │                                       │    │   │
│  │  POST /api/segment ◀─────────────────┘    │   │
│  │       ↓ response                           │   │
│  │  segmented_image (base64) + bbox + foot_y  │   │
│  │                                            │   │
│  │  POST /api/merge (preview_mode=true)       │   │
│  │       ↓ response                           │   │
│  │  preview_image (base64, 512x512)           │   │
│  │                                            │   │
│  │  POST /api/merge (preview_mode=false)      │   │
│  │       ↓ response                           │   │
│  │  merged_image (base64, full resolution)    │   │
│  └────────────────────────────────────────────┘   │
│                                                    │
│  ┌─────────────┐    ┌──────────────────────┐      │
│  │ Canvas       │    │ Settings Panel       │      │
│  │ (プレビュー) │◀──▶│ (パラメータ調整)     │      │
│  │ ドラッグ操作 │    │ スライダー/カラー    │      │
│  └─────────────┘    └──────────────────────┘      │
└──────────────────────────────────────────────────┘
         │ HTTP (localhost)
         ▼
┌──────────────────────────────────────────────────┐
│  バックエンド (Python FastAPI :8000)                │
│                                                    │
│  POST /api/segment                                 │
│  ┌─────────┐   ┌──────────┐   ┌───────────────┐  │
│  │ 画像     │──▶│ rembg    │──▶│ 透過PNG       │  │
│  │ デコード │   │ (U2Net)  │   │ + BBox算出    │  │
│  │ +リサイズ│   │          │   │ + 足元座標    │  │
│  └─────────┘   └──────────┘   └───────────────┘  │
│                                                    │
│  POST /api/merge                                   │
│  ┌─────────┐   ┌──────────┐   ┌───────────────┐  │
│  │ パラメータ│──▶│ 合成     │──▶│ 合成画像     │  │
│  │ + 画像   │   │ パイプ   │   │ (PNG base64)  │  │
│  │ デコード │   │ ライン   │   │              │  │
│  └─────────┘   └──────────┘   └───────────────┘  │
│                                                    │
│  合成パイプライン詳細:                              │
│  色調補正 → スケール計算 → 影生成 → 合成 → 出力    │
└──────────────────────────────────────────────────┘
```

### 入出力定義

#### フロントエンド → バックエンド

| エンドポイント | 入力 | 出力 |
|---------------|------|------|
| POST /api/segment | 画像ファイル (multipart) | segmented_image, bbox, foot_y, original_size, processing_time_ms |
| POST /api/merge | image1, image2 (base64), settings (JSON) | merged_image (base64), processing_time_ms |
| GET /api/health | なし | status, rembg_loaded, version |

---

## 4. API仕様詳細

### 4.1 POST /api/segment — 人物セグメンテーション

**Request**: `multipart/form-data`

| フィールド | 型 | 必須 | 説明 |
|-----------|-----|------|------|
| image | File | Yes | 画像ファイル (JPEG/PNG/WebP/HEIC) |

**バリデーション**:
- Content-Type: image/jpeg, image/png, image/webp, image/heic, image/heif
- ファイルサイズ: 最大20MB
- 画像解像度: 長辺4000pxを超える場合はサーバー側でリサイズ

**Response**: `200 OK` — `application/json`
```json
{
  "segmented_image": "data:image/png;base64,{base64データ}",
  "bbox": {
    "x": 50,
    "y": 10,
    "width": 400,
    "height": 900
  },
  "foot_y": 900,
  "original_size": {
    "width": 1200,
    "height": 1600
  },
  "processing_time_ms": 2100
}
```

**エラーレスポンス**:
```json
// 400 Bad Request
{
  "error": "invalid_image",
  "message": "対応していない画像形式です。JPEG/PNG/WebPファイルを使用してください。",
  "detail": "Unsupported content type: application/pdf"
}

// 413 Payload Too Large
{
  "error": "file_too_large",
  "message": "ファイルサイズが20MBを超えています。",
  "max_size_mb": 20
}

// 422 Unprocessable Entity
{
  "error": "segmentation_failed",
  "message": "人物を検出できませんでした。人物が写った写真を使用してください。",
  "detail": "No foreground detected by rembg"
}
```

### 4.2 POST /api/merge — 合成実行

**Request**: `application/json`

```json
{
  "image1_id": "seg_abc123",
  "image2_id": "seg_def456",
  "settings": {
    "background_color": "#FFFFFF",
    "output_width": 1024,
    "output_height": 1024,
    "person1": {
      "x": 0.3,
      "y_offset": 0,
      "scale": 1.0
    },
    "person2": {
      "x": 0.7,
      "y_offset": 0,
      "scale": 1.0
    },
    "shadow": {
      "enabled": true,
      "intensity": 0.5
    },
    "color_correction": true
  },
  "preview_mode": true
}
```

| フィールド | 型 | 必須 | 説明 |
|-----------|-----|------|------|
| image1_id | string | Yes | セグメンテーション結果ID（/api/segmentの返却値） |
| image2_id | string | Yes | セグメンテーション結果ID |
| settings.background_color | string | No | 背景色 (hex)。デフォルト: "#FFFFFF" |
| settings.output_width | int | No | 出力幅 (px)。デフォルト: 1024 |
| settings.output_height | int | No | 出力高さ (px)。デフォルト: 1024 |
| settings.person1.x | float | No | 人物1の水平位置 (0.0-1.0)。デフォルト: 0.3 |
| settings.person1.y_offset | int | No | 人物1のY方向オフセット (px)。デフォルト: 0 |
| settings.person1.scale | float | No | 人物1のスケール (0.5-2.0)。デフォルト: 1.0 |
| settings.person2.x | float | No | 人物2の水平位置 (0.0-1.0)。デフォルト: 0.7 |
| settings.person2.y_offset | int | No | 人物2のY方向オフセット (px)。デフォルト: 0 |
| settings.person2.scale | float | No | 人物2のスケール (0.5-2.0)。デフォルト: 1.0 |
| settings.shadow.enabled | bool | No | 影の表示。デフォルト: true |
| settings.shadow.intensity | float | No | 影の強度 (0.0-1.0)。デフォルト: 0.5 |
| settings.color_correction | bool | No | 色調補正。デフォルト: true |
| preview_mode | bool | No | trueで低解像度プレビュー (512x512)。デフォルト: false |

**Response**: `200 OK` — `application/json`
```json
{
  "merged_image": "data:image/png;base64,{base64データ}",
  "processing_time_ms": 450,
  "output_size": {
    "width": 1024,
    "height": 1024
  }
}
```

**preview_modeによる挙動差**:
| 項目 | preview_mode=true | preview_mode=false |
|------|------------------|-------------------|
| 出力解像度 | 512x512 固定 | settings指定値 |
| 処理時間目標 | 200ms以内 | 1秒以内 |
| 画像フォーマット | JPEG (quality=70) | PNG |
| 用途 | Canvas上のリアルタイムプレビュー | 最終ダウンロード |

### 4.3 GET /api/health — ヘルスチェック

**Response**: `200 OK`
```json
{
  "status": "ok",
  "rembg_loaded": true,
  "version": "2.0.0"
}
```

### 4.4 セグメンテーション結果の管理

セグメンテーション結果はサーバーサイドのインメモリストアに一時保持する。

- `/api/segment` 成功時にユニークIDを返却（`seg_{uuid4[:8]}`）
- `/api/merge` はIDで参照（base64の再送を回避し帯域を節約）
- サーバー再起動時にクリア（永続化不要）
- 最大保持数: 10件（LRU方式で古いものを削除）

**Response拡張（/api/segment）**:
```json
{
  "id": "seg_abc123",
  "segmented_image": "data:image/png;base64,...",
  "bbox": { "x": 50, "y": 10, "width": 400, "height": 900 },
  "foot_y": 900,
  "original_size": { "width": 1200, "height": 1600 },
  "processing_time_ms": 2100
}
```

---

## 5. フロントエンド Canvas操作仕様

### 5.1 Canvasコンポーネント構成

```
<MergeCanvas>
  ├── 背景レイヤー（単色 or 画像）
  ├── 影レイヤー（person1の影、person2の影）
  ├── 人物レイヤー1（ドラッグ可能）
  └── 人物レイヤー2（ドラッグ可能）
```

### 5.2 Canvas表示仕様

| 項目 | 仕様 |
|------|------|
| Canvas表示サイズ | 親コンテナ幅に合わせて可変（max 640px） |
| 内部解像度 | バックエンドから受け取ったプレビュー画像そのまま |
| 描画方式 | バックエンドが合成した画像をCanvasに描画 |
| 更新タイミング | パラメータ変更時にPOSTしてプレビュー画像を取得・再描画 |

### 5.3 ドラッグ操作仕様（P1）

Canvas上で人物の位置をドラッグ操作で微調整する。

| 操作 | 動作 |
|------|------|
| mousedown on 人物領域 | ドラッグ開始。対象人物をハイライト |
| mousemove (dragging) | 人物のx位置をリアルタイム更新（Canvas上のローカル描画） |
| mouseup | ドラッグ終了。新しいx位置をsettingsに反映し、POST /api/merge (preview) を発行 |

**ドラッグ中の描画**:
- ドラッグ中は最後に取得したプレビュー画像上で、ドラッグ中の人物のみオーバーレイ表示位置を移動
- mouseup時にサーバーに新座標をPOSTし、正確な合成プレビューを取得

**ヒットテスト**:
- 各人物のBBox（バックエンドから取得済み）をCanvas座標に変換
- BBox内のクリックで対象人物を選択
- BBox外のクリックは選択解除

### 5.4 パラメータ変更時のプレビュー更新

```
ユーザーがスライダー/カラーピッカーを操作
    ↓
デバウンス 300ms（連続操作を束ねる）
    ↓
POST /api/merge (preview_mode=true) を発行
    ↓
レスポンス受信（200ms以内目標）
    ↓
Canvas再描画
```

**デバウンス仕様**:
- スライダー操作: 300ms デバウンス
- カラーピッカー: 500ms デバウンス（変更頻度が高いため）
- ドラッグ操作: mouseupイベントのみでPOST（ドラッグ中はローカル描画のみ）

---

## 6. 合成パイプライン詳細

### 6.1 処理フロー

```
入力: segmented_image1, segmented_image2, settings
    ↓
[Step 1] 画像デコード
    - base64 → PIL Image（RGBA）
    - BBoxでクロップ（不要な透明領域を除去）
    ↓
[Step 2] 色調補正 (settings.color_correction = true の場合)
    - LAB色空間でのヒストグラムマッチング
    - 人物1を基準に人物2の色温度・明るさを補正
    ↓
[Step 3] スケール計算
    - 自動スケール: BBox高さ比率 → 0.8-1.2倍にクランプ
    - 手動スケール: settings.personN.scale を優先
    - 出力キャンバスサイズに対する相対スケール算出
    ↓
[Step 4] 位置計算
    - X位置: settings.personN.x × output_width
    - Y位置: 足元を出力キャンバス下端から80%の位置に配置
    - Y_offset: settings.personN.y_offset で微調整
    ↓
[Step 5] 影生成 (settings.shadow.enabled = true の場合)
    - 足元位置にガウシアンブラー楕円
    - 影の幅: 人物幅の80%
    - 影の高さ: 人物幅の15%
    - 不透明度: settings.shadow.intensity
    ↓
[Step 6] 最終合成
    - 背景キャンバス生成（settings.background_color）
    - 影レイヤー合成
    - 人物1配置（アルファブレンディング）
    - 人物2配置（アルファブレンディング）
    ↓
[Step 7] 出力
    - preview_mode=true: 512x512リサイズ → JPEG (quality=70)
    - preview_mode=false: 指定サイズ → PNG
    - base64エンコードして返却
```

### 6.2 色調補正アルゴリズム

```
入力: source_image（補正対象）, reference_image（基準）
    ↓
[1] BGR → LAB変換
[2] 各チャンネル(L,A,B)ごとに:
    - source_mean, source_std を計算
    - reference_mean, reference_std を計算
    - normalized = (pixel - source_mean) * (reference_std / source_std) + reference_mean
    - 0-255にクランプ
[3] LAB → BGR変換
    ↓
出力: 色調補正済み画像
```

### 6.3 影生成アルゴリズム

```
入力: canvas, foot_x, foot_y, person_width, intensity
    ↓
[1] 影レイヤー（全透明）を作成
[2] 楕円描画:
    - 中心: (foot_x, foot_y)
    - 幅: person_width * 0.8
    - 高さ: person_width * 0.15
    - 色: 黒 (0, 0, 0)
[3] ガウシアンブラー適用 (kernel=21, sigma=10)
[4] canvas に影レイヤーを重畳（不透明度 = intensity * 0.6）
    ↓
出力: 影付きcanvas
```

---

## 7. 制約条件

### 7.1 パフォーマンス制約

| 指標 | 目標値 | 測定条件 |
|------|--------|----------|
| セグメンテーション処理 | 3秒以内/枚 | M4チップ、2000x3000px入力 |
| プレビュー合成 | 200ms以内 | 512x512出力 |
| フル解像度合成 | 1秒以内 | 1024x1024出力 |
| E2E（入力〜プレビュー表示） | 10秒以内 | 2枚入力〜プレビュー表示 |
| メモリ使用量 | 4GB以内 | Pythonサーバー + Reactアプリ合計 |
| フロントエンド LCP | 2秒以内 | Vite dev server経由 |
| 画像入力リサイズ | 長辺4000px | サーバー側で自動リサイズ |

### 7.2 セキュリティ制約

| 項目 | 仕様 |
|------|------|
| 実行環境 | ローカルのみ（外部通信なし） |
| ファイルアクセス | アップロード画像のサニタイズ（Content-Type検証 + マジックバイト検証） |
| CORS | localhost:5173 → localhost:8000 のみ許可 |
| ファイルサイズ制限 | 20MB/枚（サーバー側で強制） |
| 一時ファイル | サーバーメモリ上のみ（ディスク書き込みなし） |
| 入力値検証 | 全APIパラメータにバリデーション（Pydantic） |

### 7.3 UX制約

| 項目 | 仕様 |
|------|------|
| 対応ブラウザ | Chrome / Edge（最新版） |
| 対応デバイス | デスクトップ専用（モバイル対応不要） |
| 最小解像度 | 1280x720 |
| 操作ステップ | 最小2ステップ（写真2枚入力 → 自動合成） |
| デフォルト品質 | 設定変更なしで十分な品質 |
| エラー表示 | 日本語のユーザーフレンドリーなメッセージ |
| 処理状態 | 明確な状態表示（スピナー + テキスト） |

### 7.4 技術制約

| 項目 | 仕様 |
|------|------|
| 外部API | 不使用（$0運用） |
| ハードウェア | Mac mini M4 24GB で快適動作 |
| 対象 | 人物写真に特化（1回2人まで） |
| Python | 3.11+ |
| Node.js | 18+ |
| パッケージ管理 | pip (requirements.txt) + npm (package.json) |

---

## 8. 出力サイズプリセット

| プリセット名 | サイズ | 用途 |
|-------------|--------|------|
| 正方形 | 1024x1024 | SNS投稿、動画AI入力（デフォルト） |
| 横長 16:9 | 1280x720 | YouTube サムネイル |
| 縦長 9:16 | 720x1280 | TikTok / Instagram Stories |
| カスタム | 任意 | ユーザー指定（最大4096x4096） |

---

## 9. エラーハンドリング方針

### フロントエンド

| エラー種別 | ユーザーへの表示 | アクション |
|-----------|----------------|-----------|
| ファイル形式不正 | 「対応していないファイル形式です」 | ファイル選択に戻る |
| ファイルサイズ超過 | 「ファイルサイズが20MBを超えています」 | ファイル選択に戻る |
| サーバー未起動 | 「サーバーに接続できません。起動を確認してください」 | リトライボタン表示 |
| セグメンテーション失敗 | 「人物を検出できませんでした」 | 別の写真を使うよう案内 |
| 合成処理エラー | 「合成処理中にエラーが発生しました」 | リトライボタン表示 |

### バックエンド

| エラー種別 | HTTPステータス | 対応 |
|-----------|---------------|------|
| バリデーションエラー | 400 | Pydanticによる自動バリデーション |
| ファイルサイズ超過 | 413 | ミドルウェアでチェック |
| 人物未検出 | 422 | rembg出力の透明度チェック |
| 内部エラー | 500 | ログ出力 + 汎用エラーメッセージ |

---

## 10. 非機能設計

### 10.1 ログ設計

| レベル | 用途 |
|--------|------|
| INFO | API呼び出し、処理時間 |
| WARNING | 非推奨パラメータ、リサイズ発生 |
| ERROR | 処理失敗、例外 |

### 10.2 起動手順

```bash
# launch_app.command で自動起動
# 1. Python仮想環境の作成・有効化
# 2. pip install -r requirements.txt
# 3. uvicorn server:app --host 0.0.0.0 --port 8000
# 4. npm install && npm run dev
# 5. ブラウザでhttp://localhost:5173 を自動オープン
```
