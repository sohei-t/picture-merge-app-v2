# data_models.md - Picture Merge App v2 データモデル定義

## 1. フロントエンド状態管理モデル（React State）

### 1.1 アプリケーション全体の状態

```typescript
// ===== アプリケーション状態 =====

type AppPhase =
  | "IDLE"           // 初期状態
  | "ONE_UPLOADED"   // 写真1枚入力済み
  | "SEGMENTING"     // セグメンテーション処理中
  | "PREVIEW"        // プレビュー表示中
  | "MERGING"        // フル解像度合成中
  | "COMPLETE"       // ダウンロード完了
  | "ERROR";         // エラー発生

interface AppState {
  phase: AppPhase;
  error: AppError | null;
  serverStatus: ServerStatus;
}

interface ServerStatus {
  connected: boolean;
  rembgLoaded: boolean;
  version: string;
  lastChecked: Date | null;
}

interface AppError {
  type: "validation" | "network" | "segmentation" | "merge" | "unknown";
  message: string;        // ユーザー向けメッセージ（日本語）
  detail?: string;        // 技術詳細（デバッグ用）
  retryable: boolean;
}
```

### 1.2 画像入力の状態

```typescript
// ===== 入力画像の状態 =====

interface InputImage {
  file: File;
  objectUrl: string;          // URL.createObjectURL で生成
  thumbnail: string;          // 表示用サムネイル (data URL)
  originalSize: ImageSize;
}

interface ImageSize {
  width: number;
  height: number;
}

interface ImageInputState {
  image1: InputImage | null;
  image2: InputImage | null;
}
```

### 1.3 セグメンテーション結果の状態

```typescript
// ===== セグメンテーション結果 =====

interface SegmentationResult {
  id: string;                  // サーバー発行のID (seg_{uuid})
  segmentedImage: string;      // data:image/png;base64,...
  bbox: BoundingBox;
  footY: number;               // 足元のY座標
  originalSize: ImageSize;
  processingTimeMs: number;
}

interface BoundingBox {
  x: number;
  y: number;
  width: number;
  height: number;
}

interface SegmentationState {
  person1: SegmentationResult | null;
  person2: SegmentationResult | null;
  isProcessing: boolean;
  progress: number;            // 0-100 (0: 未開始, 50: 1枚完了, 100: 2枚完了)
}
```

### 1.4 合成設定の状態

```typescript
// ===== 合成設定 =====

interface MergeSettings {
  backgroundColor: string;     // hex (#FFFFFF)
  outputSize: OutputSize;
  person1: PersonSettings;
  person2: PersonSettings;
  shadow: ShadowSettings;
  colorCorrection: boolean;
}

interface OutputSize {
  width: number;               // px (64-4096)
  height: number;              // px (64-4096)
  preset: OutputPreset;
}

type OutputPreset = "square" | "landscape" | "portrait" | "custom";

// プリセット定義
const OUTPUT_PRESETS: Record<OutputPreset, { width: number; height: number; label: string }> = {
  square:    { width: 1024, height: 1024, label: "正方形 (1024x1024)" },
  landscape: { width: 1280, height: 720,  label: "横長 16:9 (1280x720)" },
  portrait:  { width: 720,  height: 1280, label: "縦長 9:16 (720x1280)" },
  custom:    { width: 1024, height: 1024, label: "カスタム" },
};

interface PersonSettings {
  x: number;                   // 水平位置 (0.0-1.0)
  yOffset: number;             // Y方向オフセット (px)
  scale: number;               // スケール (0.5-2.0)
  autoScale: boolean;          // 自動スケール使用フラグ
}

interface ShadowSettings {
  enabled: boolean;
  intensity: number;           // 0.0-1.0
}

// デフォルト設定
const DEFAULT_MERGE_SETTINGS: MergeSettings = {
  backgroundColor: "#FFFFFF",
  outputSize: { width: 1024, height: 1024, preset: "square" },
  person1: { x: 0.3, yOffset: 0, scale: 1.0, autoScale: true },
  person2: { x: 0.7, yOffset: 0, scale: 1.0, autoScale: true },
  shadow: { enabled: true, intensity: 0.5 },
  colorCorrection: true,
};
```

### 1.5 プレビューの状態

```typescript
// ===== プレビュー =====

interface PreviewState {
  image: string | null;        // data:image/jpeg;base64,... (プレビュー画像)
  isLoading: boolean;
  lastUpdated: Date | null;
  processingTimeMs: number | null;
}
```

### 1.6 Canvas操作の状態

```typescript
// ===== Canvas操作 =====

interface CanvasState {
  isDragging: boolean;
  dragTarget: "person1" | "person2" | null;
  dragStartX: number;
  dragCurrentX: number;
  canvasRect: DOMRect | null;   // Canvasの画面上の位置・サイズ
}
```

### 1.7 ルートState（全体統合）

```typescript
// ===== ルートState =====

interface RootState {
  app: AppState;
  images: ImageInputState;
  segmentation: SegmentationState;
  settings: MergeSettings;
  preview: PreviewState;
  canvas: CanvasState;
}
```

---

## 2. バックエンドのリクエスト/レスポンスモデル（Pydantic）

### 2.1 セグメンテーションAPI

```python
# ===== POST /api/segment =====

from pydantic import BaseModel, Field
from typing import Optional
from fastapi import UploadFile

# Request: multipart/form-data (FastAPIのUploadFileで受け取り)
# - image: UploadFile

# Response
class BBoxModel(BaseModel):
    x: int = Field(..., description="左上X座標 (px)")
    y: int = Field(..., description="左上Y座標 (px)")
    width: int = Field(..., ge=1, description="幅 (px)")
    height: int = Field(..., ge=1, description="高さ (px)")

class ImageSizeModel(BaseModel):
    width: int = Field(..., ge=1, description="幅 (px)")
    height: int = Field(..., ge=1, description="高さ (px)")

class SegmentResponse(BaseModel):
    id: str = Field(..., description="セグメンテーション結果ID (seg_{uuid})")
    segmented_image: str = Field(..., description="切り抜き画像 (data:image/png;base64,...)")
    bbox: BBoxModel
    foot_y: int = Field(..., description="足元のY座標 (px)")
    original_size: ImageSizeModel
    processing_time_ms: int = Field(..., ge=0, description="処理時間 (ms)")
```

### 2.2 合成API

```python
# ===== POST /api/merge =====

class PersonSettingsModel(BaseModel):
    x: float = Field(default=0.5, ge=0.0, le=1.0, description="水平位置 (0.0-1.0)")
    y_offset: int = Field(default=0, description="Y方向オフセット (px)")
    scale: float = Field(default=1.0, ge=0.5, le=2.0, description="スケール (0.5-2.0)")

class ShadowSettingsModel(BaseModel):
    enabled: bool = Field(default=True, description="影の表示")
    intensity: float = Field(default=0.5, ge=0.0, le=1.0, description="影の強度 (0.0-1.0)")

class MergeSettingsModel(BaseModel):
    background_color: str = Field(
        default="#FFFFFF",
        pattern=r"^#[0-9A-Fa-f]{6}$",
        description="背景色 (hex)"
    )
    output_width: int = Field(default=1024, ge=64, le=4096, description="出力幅 (px)")
    output_height: int = Field(default=1024, ge=64, le=4096, description="出力高さ (px)")
    person1: PersonSettingsModel = Field(default_factory=lambda: PersonSettingsModel(x=0.3))
    person2: PersonSettingsModel = Field(default_factory=lambda: PersonSettingsModel(x=0.7))
    shadow: ShadowSettingsModel = Field(default_factory=ShadowSettingsModel)
    color_correction: bool = Field(default=True, description="色調補正の適用")

class MergeRequest(BaseModel):
    image1_id: str = Field(..., description="人物1のセグメンテーション結果ID")
    image2_id: str = Field(..., description="人物2のセグメンテーション結果ID")
    settings: MergeSettingsModel = Field(default_factory=MergeSettingsModel)
    preview_mode: bool = Field(default=False, description="プレビューモード (512x512 JPEG)")

class MergeResponse(BaseModel):
    merged_image: str = Field(..., description="合成画像 (data:image/{format};base64,...)")
    processing_time_ms: int = Field(..., ge=0, description="処理時間 (ms)")
    output_size: ImageSizeModel
```

### 2.3 ヘルスチェックAPI

```python
# ===== GET /api/health =====

class HealthResponse(BaseModel):
    status: str = Field(default="ok", description="サーバーステータス")
    rembg_loaded: bool = Field(..., description="rembgモデルのロード状態")
    version: str = Field(default="2.0.0", description="APIバージョン")
```

### 2.4 エラーレスポンス

```python
# ===== エラーレスポンス =====

class ErrorResponse(BaseModel):
    error: str = Field(..., description="エラーコード (snake_case)")
    message: str = Field(..., description="ユーザー向けメッセージ（日本語）")
    detail: Optional[str] = Field(None, description="技術詳細（デバッグ用）")

# エラーコード一覧
ERROR_CODES = {
    "invalid_image": "対応していない画像形式です。JPEG/PNG/WebPファイルを使用してください。",
    "file_too_large": "ファイルサイズが20MBを超えています。",
    "segmentation_failed": "人物を検出できませんでした。人物が写った写真を使用してください。",
    "invalid_segment_id": "セグメンテーション結果が見つかりません。写真を再入力してください。",
    "merge_failed": "合成処理中にエラーが発生しました。もう一度お試しください。",
    "internal_error": "サーバー内部エラーが発生しました。",
}
```

---

## 3. 画像処理パイプラインの中間データ構造

### 3.1 セグメンテーションパイプライン

```python
# ===== セグメンテーション中間データ =====

from dataclasses import dataclass, field
from typing import Optional
import numpy as np
from PIL import Image

@dataclass
class RawInput:
    """生の入力画像"""
    image: Image.Image          # PILイメージ (RGB/RGBA)
    original_width: int
    original_height: int
    content_type: str           # "image/jpeg", "image/png", etc.
    was_resized: bool = False   # 長辺4000px超でリサイズされたか

@dataclass
class SegmentedOutput:
    """セグメンテーション出力"""
    image: Image.Image          # PILイメージ (RGBA, 透過付き)
    alpha_mask: np.ndarray      # アルファマスク (H x W, 0-255)
    bbox: tuple[int, int, int, int]  # (x, y, width, height)
    foot_y: int                 # 足元Y座標
    person_height: int          # 人物の高さ (bbox.height)
    person_width: int           # 人物の幅 (bbox.width)

@dataclass
class SegmentationCache:
    """セグメンテーション結果のキャッシュエントリ"""
    id: str                     # seg_{uuid}
    output: SegmentedOutput
    created_at: float           # time.time()
    original_size: tuple[int, int]  # (width, height)
```

### 3.2 合成パイプライン

```python
# ===== 合成パイプライン中間データ =====

@dataclass
class CroppedPerson:
    """BBoxでクロップ済みの人物画像"""
    image: Image.Image          # RGBA (クロップ済み)
    foot_y_relative: int        # クロップ後の相対足元Y座標
    original_bbox: tuple[int, int, int, int]

@dataclass
class ColorCorrectedPerson:
    """色調補正済みの人物画像"""
    image: Image.Image          # RGBA (色調補正済み)
    foot_y_relative: int

@dataclass
class ScaledPerson:
    """スケール・位置計算済みの人物"""
    image: Image.Image          # RGBA (スケール適用済み)
    canvas_x: int               # キャンバス上のX位置 (左上)
    canvas_y: int               # キャンバス上のY位置 (左上)
    foot_x: int                 # キャンバス上の足元X位置 (中央)
    foot_y: int                 # キャンバス上の足元Y位置
    width: int                  # スケール後の幅
    height: int                 # スケール後の高さ
    scale_applied: float        # 適用されたスケール値

@dataclass
class ShadowLayer:
    """影レイヤー"""
    image: np.ndarray           # RGBA numpy配列
    # 影は合成キャンバス全体のサイズ

@dataclass
class MergeContext:
    """合成パイプライン全体のコンテキスト"""
    # 入力
    person1_segmented: SegmentedOutput
    person2_segmented: SegmentedOutput
    settings: "MergeSettingsModel"  # Pydanticモデル参照
    preview_mode: bool

    # 中間状態（パイプラインの各ステップで更新）
    person1_cropped: Optional[CroppedPerson] = None
    person2_cropped: Optional[CroppedPerson] = None
    person1_color_corrected: Optional[ColorCorrectedPerson] = None
    person2_color_corrected: Optional[ColorCorrectedPerson] = None
    person1_scaled: Optional[ScaledPerson] = None
    person2_scaled: Optional[ScaledPerson] = None
    shadow: Optional[ShadowLayer] = None

    # 出力
    canvas_width: int = 1024
    canvas_height: int = 1024
    result: Optional[Image.Image] = None
    processing_times: dict = field(default_factory=dict)
    # {"crop": 5, "color_correct": 30, "scale": 10, "shadow": 20, "compose": 50}
```

### 3.3 自動スケール計算の中間データ

```python
# ===== 自動スケール計算 =====

@dataclass
class AutoScaleResult:
    """自動スケール算出結果"""
    person1_scale: float        # 人物1に適用するスケール
    person2_scale: float        # 人物2に適用するスケール
    height_ratio: float         # 元の高さ比率 (person1 / person2)
    was_clamped: bool           # 0.8-1.2範囲にクランプされたか
    person1_x: float            # 推奨X位置 (0.0-1.0)
    person2_x: float            # 推奨X位置 (0.0-1.0)
    gap_pixels: int             # 2人の間の間隔 (px)
```

### 3.4 サーバーサイドのストア構造

```python
# ===== インメモリストア =====

from collections import OrderedDict

class SegmentationStore:
    """セグメンテーション結果のインメモリLRUストア"""

    MAX_ENTRIES = 10

    def __init__(self):
        self._store: OrderedDict[str, SegmentationCache] = OrderedDict()

    def put(self, entry: SegmentationCache) -> None:
        """結果を保存（LRU方式で古いものを削除）"""
        if entry.id in self._store:
            self._store.move_to_end(entry.id)
        self._store[entry.id] = entry
        while len(self._store) > self.MAX_ENTRIES:
            self._store.popitem(last=False)

    def get(self, id: str) -> Optional[SegmentationCache]:
        """IDで結果を取得"""
        if id in self._store:
            self._store.move_to_end(id)
            return self._store[id]
        return None

    def clear(self) -> None:
        """全結果をクリア"""
        self._store.clear()
```

---

## 4. データフロー要約

```
[入力画像 File]
    ↓ multipart/form-data
[RawInput]
    ↓ rembg + アルファマット後処理
[SegmentedOutput] → [SegmentationCache] (サーバー保持, LRU 10件)
    ↓ ID参照
[MergeContext] 生成
    ↓ Step 1: crop
[CroppedPerson] x 2
    ↓ Step 2: color_correct
[ColorCorrectedPerson] x 2
    ↓ Step 3: scale + position
[ScaledPerson] x 2 + [AutoScaleResult]
    ↓ Step 4: shadow
[ShadowLayer]
    ↓ Step 5: compose
[PIL.Image] → base64 → JSON Response
```
