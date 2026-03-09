# API_DESIGN.md - Picture Merge App v2 API仕様書

## 1. API概要

| 項目 | 値 |
|------|-----|
| プロトコル | HTTP (REST) |
| ベースURL | `http://localhost:8000` |
| データ形式 | JSON / multipart/form-data |
| 認証 | なし（ローカル実行のみ） |
| CORS | `http://localhost:5173` のみ許可 |
| APIドキュメント | `http://localhost:8000/docs` (Swagger UI 自動生成) |

---

## 2. エンドポイント一覧

| メソッド | パス | 概要 | 優先度 |
|---------|------|------|--------|
| POST | `/api/segment` | 人物セグメンテーション（背景除去） | P0 |
| POST | `/api/merge` | 合成実行（プレビュー/フル解像度） | P0 |
| GET | `/api/health` | ヘルスチェック | P0 |

---

## 3. POST /api/segment — 人物セグメンテーション

### 3.1 概要

アップロードされた画像からrembg (U2Net) で人物を切り抜き、透過PNG + メタデータを返却する。
セグメンテーション結果はサーバーサイドのLRUキャッシュに保持され、一意のIDが発行される。

### 3.2 リクエスト

**Content-Type:** `multipart/form-data`

| フィールド | 型 | 必須 | 説明 |
|-----------|-----|------|------|
| image | File | Yes | 画像ファイル |

**バリデーションルール:**

| ルール | 条件 | エラー時 |
|--------|------|---------|
| ファイル形式 | Content-Type: image/jpeg, image/png, image/webp, image/heic, image/heif | 400 invalid_image |
| マジックバイト | JPEG(FFD8), PNG(89504E47), WebP(52494646) のヘッダ検証 | 400 invalid_image |
| ファイルサイズ | 最大 20MB | 413 file_too_large |
| 画像解像度 | 長辺 4000px 超過時はサーバー側でリサイズ（アスペクト比維持） | 警告ログ出力のみ |

### 3.3 レスポンス（成功）

**Status:** `200 OK`
**Content-Type:** `application/json`

```json
{
  "id": "seg_a1b2c3d4",
  "segmented_image": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUg...",
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

| フィールド | 型 | 説明 |
|-----------|-----|------|
| id | string | セグメンテーション結果ID (`seg_{uuid4[:8]}`)。mergeリクエストで参照 |
| segmented_image | string | 切り抜き画像 (data URI, PNG base64) |
| bbox | object | 人物のバウンディングボックス (px) |
| bbox.x | int | 左上X座標 |
| bbox.y | int | 左上Y座標 |
| bbox.width | int | 幅 |
| bbox.height | int | 高さ |
| foot_y | int | 足元のY座標 (px)。合成時の足元揃えに使用 |
| original_size | object | 入力画像の元サイズ |
| original_size.width | int | 元の幅 (px) |
| original_size.height | int | 元の高さ (px) |
| processing_time_ms | int | 処理時間 (ミリ秒) |

### 3.4 レスポンス（エラー）

#### 400 Bad Request — 画像形式不正

```json
{
  "error": "invalid_image",
  "message": "対応していない画像形式です。JPEG/PNG/WebPファイルを使用してください。",
  "detail": "Unsupported content type: application/pdf"
}
```

#### 413 Payload Too Large — ファイルサイズ超過

```json
{
  "error": "file_too_large",
  "message": "ファイルサイズが20MBを超えています。",
  "detail": "File size: 25.3MB, max: 20MB"
}
```

#### 422 Unprocessable Entity — 人物未検出

```json
{
  "error": "segmentation_failed",
  "message": "人物を検出できませんでした。人物が写った写真を使用してください。",
  "detail": "No foreground detected by rembg: alpha channel is entirely transparent"
}
```

#### 500 Internal Server Error — サーバー内部エラー

```json
{
  "error": "internal_error",
  "message": "サーバー内部エラーが発生しました。",
  "detail": "rembg processing failed: ..."
}
```

### 3.5 処理フロー

```
1. multipart/form-data からファイル取得
2. Content-Type検証 + マジックバイト検証
3. ファイルサイズ検証 (≤ 20MB)
4. PIL.Image.open() で画像デコード
5. 長辺 > 4000px の場合リサイズ（アスペクト比維持）
6. rembg.remove() でセグメンテーション実行
7. アルファチャンネル検証（全透明 = 人物未検出 → 422）
8. アルファマット後処理（ガウシアンブラーでエッジ平滑化）
9. バウンディングボックス算出（非透明ピクセルの範囲）
10. 足元Y座標算出（バウンディングボックス下端）
11. 結果をLRUキャッシュに保存（ID発行）
12. JSON レスポンス返却
```

---

## 4. POST /api/merge — 合成実行

### 4.1 概要

2つのセグメンテーション結果（ID参照）と合成設定を受け取り、合成画像を返却する。
`preview_mode` パラメータにより、プレビュー用低解像度 (512x512 JPEG) またはフル解像度 (PNG) を切り替える。

### 4.2 リクエスト

**Content-Type:** `application/json`

```json
{
  "image1_id": "seg_a1b2c3d4",
  "image2_id": "seg_e5f6g7h8",
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

**バリデーションルール:**

| フィールド | 型 | 必須 | 制約 | デフォルト |
|-----------|-----|------|------|----------|
| image1_id | string | Yes | `seg_` で始まる8文字ID | — |
| image2_id | string | Yes | `seg_` で始まる8文字ID | — |
| settings | object | No | — | 全デフォルト値適用 |
| settings.background_color | string | No | `^#[0-9A-Fa-f]{6}$` (hex) | `"#FFFFFF"` |
| settings.output_width | int | No | 64 ≤ x ≤ 4096 | 1024 |
| settings.output_height | int | No | 64 ≤ x ≤ 4096 | 1024 |
| settings.person1.x | float | No | 0.0 ≤ x ≤ 1.0 | 0.3 |
| settings.person1.y_offset | int | No | -500 ≤ x ≤ 500 | 0 |
| settings.person1.scale | float | No | 0.5 ≤ x ≤ 2.0 | 1.0 |
| settings.person2.x | float | No | 0.0 ≤ x ≤ 1.0 | 0.7 |
| settings.person2.y_offset | int | No | -500 ≤ x ≤ 500 | 0 |
| settings.person2.scale | float | No | 0.5 ≤ x ≤ 2.0 | 1.0 |
| settings.shadow.enabled | bool | No | — | true |
| settings.shadow.intensity | float | No | 0.0 ≤ x ≤ 1.0 | 0.5 |
| settings.color_correction | bool | No | — | true |
| preview_mode | bool | No | — | false |

### 4.3 レスポンス（成功）

**Status:** `200 OK`
**Content-Type:** `application/json`

#### preview_mode=true（プレビュー）

```json
{
  "merged_image": "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAA...",
  "processing_time_ms": 150,
  "output_size": {
    "width": 512,
    "height": 512
  }
}
```

#### preview_mode=false（フル解像度）

```json
{
  "merged_image": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUg...",
  "processing_time_ms": 800,
  "output_size": {
    "width": 1024,
    "height": 1024
  }
}
```

| フィールド | 型 | 説明 |
|-----------|-----|------|
| merged_image | string | 合成画像 (data URI)。プレビュー: JPEG, フル: PNG |
| processing_time_ms | int | 処理時間 (ミリ秒) |
| output_size | object | 出力画像サイズ |
| output_size.width | int | 幅 (px) |
| output_size.height | int | 高さ (px) |

### 4.4 preview_mode による挙動差

| 項目 | preview_mode=true | preview_mode=false |
|------|------------------|-------------------|
| 出力解像度 | 512x512 固定 | settings指定値 |
| 画像フォーマット | JPEG (quality=70) | PNG |
| 処理時間目標 | 200ms以内 | 1秒以内 |
| 用途 | パラメータ調整中のプレビュー | 最終ダウンロード |
| data URI prefix | `data:image/jpeg;base64,` | `data:image/png;base64,` |

### 4.5 レスポンス（エラー）

#### 400 Bad Request — バリデーションエラー

```json
{
  "error": "validation_error",
  "message": "入力パラメータが不正です。",
  "detail": "settings.person1.scale: value must be >= 0.5 and <= 2.0"
}
```

#### 404 Not Found — セグメンテーション結果が見つからない

```json
{
  "error": "invalid_segment_id",
  "message": "セグメンテーション結果が見つかりません。写真を再入力してください。",
  "detail": "Segment ID 'seg_a1b2c3d4' not found in cache"
}
```

#### 500 Internal Server Error — 合成処理エラー

```json
{
  "error": "merge_failed",
  "message": "合成処理中にエラーが発生しました。もう一度お試しください。",
  "detail": "Color correction failed: ..."
}
```

### 4.6 処理フロー（合成パイプライン）

```
1. image1_id, image2_id でLRUキャッシュから結果取得（見つからない場合 404）
2. Pydanticバリデーション（settings）
3. BBoxでクロップ（不要な透明領域を除去）
4. 色調補正（color_correction=true の場合）
   - LAB色空間でのヒストグラムマッチング
   - person1を基準にperson2を補正
5. スケール計算
   - autoScale: BBox高さ比率 → 0.8-1.2倍にクランプ
   - 手動scale: settings値を優先
6. 位置計算
   - X: settings.personN.x × canvas_width
   - Y: 足元を下端80%位置に配置 + y_offset
7. 影生成（shadow.enabled=true の場合）
   - 足元にガウシアンブラー楕円
8. 最終合成（背景 → 影 → person1 → person2）
9. 出力サイズ調整
   - preview: 512x512リサイズ → JPEG (quality=70)
   - full: 指定サイズ → PNG
10. base64エンコード → JSON返却
```

---

## 5. GET /api/health — ヘルスチェック

### 5.1 概要

サーバーの起動状態とrembgモデルのロード状態を返却する。
フロントエンド初期化時にサーバー接続確認として使用。

### 5.2 リクエスト

パラメータなし。

### 5.3 レスポンス

**Status:** `200 OK`
**Content-Type:** `application/json`

```json
{
  "status": "ok",
  "rembg_loaded": true,
  "version": "2.0.0"
}
```

| フィールド | 型 | 説明 |
|-----------|-----|------|
| status | string | サーバーステータス。正常: `"ok"` |
| rembg_loaded | bool | rembgモデルがロード済みか。初回起動直後はfalseの可能性 |
| version | string | APIバージョン |

### 5.4 レスポンス（サーバー未起動時）

サーバーが起動していない場合、フロントエンドのfetchがネットワークエラーとなる。
フロントエンドで「サーバーに接続できません。起動を確認してください」と表示。

---

## 6. エラーレスポンス共通仕様

### 6.1 エラーレスポンス構造

すべてのエラーレスポンスは以下の共通フォーマットに従う。

```json
{
  "error": "error_code",
  "message": "ユーザー向けメッセージ（日本語）",
  "detail": "技術的な詳細情報（デバッグ用、オプション）"
}
```

### 6.2 エラーコード一覧

| コード | HTTPステータス | ユーザー向けメッセージ |
|--------|---------------|---------------------|
| invalid_image | 400 | 対応していない画像形式です。JPEG/PNG/WebPファイルを使用してください。 |
| file_too_large | 413 | ファイルサイズが20MBを超えています。 |
| segmentation_failed | 422 | 人物を検出できませんでした。人物が写った写真を使用してください。 |
| invalid_segment_id | 404 | セグメンテーション結果が見つかりません。写真を再入力してください。 |
| validation_error | 400 | 入力パラメータが不正です。 |
| merge_failed | 500 | 合成処理中にエラーが発生しました。もう一度お試しください。 |
| internal_error | 500 | サーバー内部エラーが発生しました。 |

---

## 7. セグメンテーション結果のキャッシュ管理

### 7.1 仕様

| 項目 | 値 |
|------|-----|
| ストレージ | サーバーメモリ（インメモリ） |
| 最大保持数 | 10件 |
| 削除方式 | LRU（Least Recently Used） |
| ID形式 | `seg_{uuid4の先頭8文字}` (例: `seg_a1b2c3d4`) |
| 永続化 | なし（サーバー再起動でクリア） |
| 保持データ | セグメンテーション済み画像 (RGBA PIL Image) + BBox + foot_y + original_size |

### 7.2 ライフサイクル

```
POST /api/segment 成功
  → SegmentationCache エントリ作成（ID発行）
  → LRUキャッシュに保存（10件超過で最古を削除）
  → IDをクライアントに返却

POST /api/merge リクエスト
  → image1_id, image2_id でキャッシュから取得
  → 見つからない場合: 404 invalid_segment_id
  → 見つかった場合: LRU順序更新 → 合成実行

サーバー再起動
  → 全キャッシュクリア
  → クライアントは再セグメンテーションが必要
```

### 7.3 キャッシュ枯渇時のフロントエンド対応

`POST /api/merge` で `404 invalid_segment_id` を受け取った場合:
1. 該当する画像の再セグメンテーションを自動実行
2. 新しいIDを取得
3. merge リクエストを再発行

---

## 8. CORS設定

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite dev server
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
```

---

## 9. リクエスト/レスポンス サイズ目安

| 操作 | リクエストサイズ | レスポンスサイズ | 所要時間目標 |
|------|----------------|----------------|-------------|
| segment (2000x3000 JPEG) | ~3-5 MB | ~2-4 MB (base64 PNG) | 1-3秒 |
| merge (preview) | ~200 B (JSON) | ~50-100 KB (base64 JPEG 512x512) | 200ms以内 |
| merge (full, 1024x1024) | ~200 B (JSON) | ~1-3 MB (base64 PNG) | 1秒以内 |
| health | 0 B | ~80 B | 即時 |
