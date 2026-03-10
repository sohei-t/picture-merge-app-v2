"""Pydantic models for API request/response schemas."""

from typing import Optional

from pydantic import BaseModel, Field


class BBoxModel(BaseModel):
    """Bounding box model."""

    x: int = Field(..., description="Left X coordinate (px)")
    y: int = Field(..., description="Top Y coordinate (px)")
    width: int = Field(..., ge=1, description="Width (px)")
    height: int = Field(..., ge=1, description="Height (px)")


class ImageSizeModel(BaseModel):
    """Image size model."""

    width: int = Field(..., ge=1, description="Width (px)")
    height: int = Field(..., ge=1, description="Height (px)")


class SegmentResponse(BaseModel):
    """Response for POST /api/segment."""

    id: str = Field(..., description="Segmentation result ID (seg_{uuid})")
    segmented_image: str = Field(
        ..., description="Segmented image (data:image/png;base64,...)"
    )
    bbox: BBoxModel
    foot_y: int = Field(..., description="Foot Y coordinate (px)")
    original_size: ImageSizeModel
    processing_time_ms: int = Field(..., ge=0, description="Processing time (ms)")
    enhanced: bool = Field(default=False, description="Whether image was enhanced")
    enhancement_scale: int = Field(default=1, description="Enhancement scale factor")


class PersonSettingsModel(BaseModel):
    """Person position/scale settings."""

    x: float = Field(
        default=0.5, ge=0.0, le=1.0, description="Horizontal position (0.0-1.0)"
    )
    y_offset: int = Field(default=0, ge=-500, le=500, description="Y offset (px)")
    scale: float = Field(
        default=1.0, ge=0.5, le=2.0, description="Scale (0.5-2.0)"
    )


class ShadowSettingsModel(BaseModel):
    """Shadow settings."""

    enabled: bool = Field(default=True, description="Shadow enabled")
    intensity: float = Field(
        default=0.5, ge=0.0, le=1.0, description="Shadow intensity (0.0-1.0)"
    )


class MergeSettingsModel(BaseModel):
    """Merge settings."""

    background_color: str = Field(
        default="#FFFFFF",
        pattern=r"^#[0-9A-Fa-f]{6}$",
        description="Background color (hex)",
    )
    output_width: int = Field(
        default=1440, ge=64, le=4096, description="Output width (px)"
    )
    output_height: int = Field(
        default=2559, ge=64, le=4096, description="Output height (px)"
    )
    person1: PersonSettingsModel = Field(
        default_factory=lambda: PersonSettingsModel(x=0.3)
    )
    person2: PersonSettingsModel = Field(
        default_factory=lambda: PersonSettingsModel(x=0.7)
    )
    shadow: ShadowSettingsModel = Field(default_factory=ShadowSettingsModel)
    color_correction: bool = Field(default=True, description="Apply color correction")
    layer_order: str = Field(
        default="person1_back",
        pattern=r"^(person1_back|person2_back)$",
        description="Layer order: person1_back (person1 behind) or person2_back",
    )


class MergeRequest(BaseModel):
    """Request for POST /api/merge."""

    image1_id: str = Field(..., description="Person 1 segmentation result ID")
    image2_id: str = Field(..., description="Person 2 segmentation result ID")
    settings: MergeSettingsModel = Field(default_factory=MergeSettingsModel)
    preview_mode: bool = Field(
        default=False, description="Preview mode (scaled JPEG)"
    )
    output_format: str = Field(
        default="PNG",
        pattern=r"^(PNG|JPEG)$",
        description="Output format: PNG (lossless) or JPEG (fast)",
    )
    crop: Optional[dict] = Field(
        default=None,
        description="Crop region as ratios: {x1, y1, x2, y2} (0.0-1.0)",
    )


class MergeResponse(BaseModel):
    """Response for POST /api/merge."""

    merged_image: str = Field(
        ..., description="Merged image (data:image/{format};base64,...)"
    )
    processing_time_ms: int = Field(..., ge=0, description="Processing time (ms)")
    output_size: ImageSizeModel


class HealthResponse(BaseModel):
    """Response for GET /api/health."""

    status: str = Field(default="ok", description="Server status")
    rembg_loaded: bool = Field(..., description="rembg model loaded status")
    version: str = Field(default="2.0.0", description="API version")


class ErrorResponse(BaseModel):
    """Error response model."""

    error: str = Field(..., description="Error code (snake_case)")
    message: str = Field(..., description="User-facing message (Japanese)")
    detail: Optional[str] = Field(None, description="Technical detail (debug)")


# Error code to message mapping
ERROR_MESSAGES = {
    "invalid_image": "対応していない画像形式です。JPEG/PNG/WebPファイルを使用してください。",
    "file_too_large": "ファイルサイズが20MBを超えています。",
    "segmentation_failed": "人物を検出できませんでした。人物が写った写真を使用してください。",
    "invalid_segment_id": "セグメンテーション結果が見つかりません。写真を再入力してください。",
    "validation_error": "入力パラメータが不正です。",
    "merge_failed": "合成処理中にエラーが発生しました。もう一度お試しください。",
    "internal_error": "サーバー内部エラーが発生しました。",
}
