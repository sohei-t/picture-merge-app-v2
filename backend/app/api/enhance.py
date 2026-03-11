"""API endpoints for image enhancement and manual adjustment."""

from __future__ import annotations

import logging

import numpy as np
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services.ai_enhancer import ai_enhance
from app.services.cache import segmentation_cache
from app.services.image_adjuster import adjust_image
from app.utils.image_utils import compute_bbox, image_to_base64

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["enhance"])


# ---- AI Enhancement ----


class AiEnhanceResponse(BaseModel):
    seg_id: str
    segmented_image: str
    bbox: dict
    foot_y: int
    processing_time_ms: int
    method: str
    scale: int
    output_size: dict


@router.post("/ai-enhance/{seg_id}", response_model=AiEnhanceResponse)
async def ai_enhance_endpoint(seg_id: str):
    """Apply AI super-resolution + face restoration to a segmented image."""
    entry = segmentation_cache.get(seg_id)
    if entry is None:
        raise HTTPException(
            status_code=404,
            detail={"error": "invalid_segment_id", "message": "セグメントIDが見つかりません。"},
        )

    # Save original before first modification
    _save_original(seg_id)

    enhanced, info = ai_enhance(entry.image)

    # Recompute bbox and foot_y
    alpha = np.array(enhanced)[:, :, 3]
    bbox_tuple = compute_bbox(alpha)
    if bbox_tuple:
        x, y, w, h = bbox_tuple
        bbox = {"x": x, "y": y, "width": w, "height": h}
        rows_with_fg = np.where(np.any(alpha > 10, axis=1))[0]
        foot_y = int(rows_with_fg[-1]) if len(rows_with_fg) > 0 else y + h
    else:
        bbox = {"x": 0, "y": 0, "width": enhanced.width, "height": enhanced.height}
        foot_y = enhanced.height

    # Update cache
    from app.services.cache import SegmentedOutput

    entry_new = SegmentedOutput(
        image=enhanced,
        bbox=(bbox["x"], bbox["y"], bbox["width"], bbox["height"]),
        foot_y=foot_y,
        original_size=(enhanced.width, enhanced.height),
    )
    segmentation_cache.put(seg_id, entry_new)

    seg_image_b64 = image_to_base64(enhanced, fmt="PNG")

    return AiEnhanceResponse(
        seg_id=seg_id,
        segmented_image=seg_image_b64,
        bbox=bbox,
        foot_y=foot_y,
        processing_time_ms=info["processing_time_ms"],
        method=info["method"],
        scale=info["scale"],
        output_size=info["output_size"],
    )


# ---- Manual Adjustment ----


class AdjustRequest(BaseModel):
    seg_id: str
    brightness: float = Field(default=0.0, ge=-1.0, le=1.0)
    contrast: float = Field(default=0.0, ge=-1.0, le=1.0)
    saturation: float = Field(default=0.0, ge=-1.0, le=1.0)
    temperature: float = Field(default=0.0, ge=-1.0, le=1.0)
    sharpness: float = Field(default=0.0, ge=-1.0, le=1.0)


class AdjustResponse(BaseModel):
    seg_id: str
    segmented_image: str
    bbox: dict
    foot_y: int


# Store original (pre-enhancement/adjustment) images for reset
_original_images: dict[str, "SegmentedOutput"] = {}


def _save_original(seg_id: str) -> None:
    """Save the original image before any modification (idempotent)."""
    if seg_id in _original_images:
        return
    entry = segmentation_cache.get(seg_id)
    if entry is None:
        return
    from app.services.cache import SegmentedOutput

    _original_images[seg_id] = SegmentedOutput(
        image=entry.image.copy(),
        bbox=entry.bbox,
        foot_y=entry.foot_y,
        original_size=entry.original_size,
    )


class ResetResponse(BaseModel):
    seg_id: str
    segmented_image: str
    bbox: dict
    foot_y: int


@router.post("/reset-image/{seg_id}", response_model=ResetResponse)
async def reset_image_endpoint(seg_id: str):
    """Reset a segmented image to its original state (before any enhancement/adjustment/erasing)."""
    if seg_id not in _original_images:
        raise HTTPException(
            status_code=404,
            detail={"error": "no_original", "message": "元の画像が保存されていません。"},
        )

    from app.services.cache import SegmentedOutput

    original = _original_images[seg_id]
    restored = SegmentedOutput(
        image=original.image.copy(),
        bbox=original.bbox,
        foot_y=original.foot_y,
        original_size=original.original_size,
    )
    segmentation_cache.put(seg_id, restored)

    # Clear the saved original so next modification saves fresh
    del _original_images[seg_id]

    x, y, w, h = restored.bbox
    bbox = {"x": x, "y": y, "width": w, "height": h}
    seg_image_b64 = image_to_base64(restored.image, fmt="PNG")

    return ResetResponse(
        seg_id=seg_id,
        segmented_image=seg_image_b64,
        bbox=bbox,
        foot_y=restored.foot_y,
    )


@router.post("/adjust", response_model=AdjustResponse)
async def adjust_endpoint(req: AdjustRequest):
    """Apply manual adjustments (brightness, contrast, etc.) to a segmented image.

    Always adjusts from the original (pre-adjustment) image so sliders
    can be moved freely without cumulative degradation.
    """
    from app.services.cache import SegmentedOutput

    # Save original on first adjustment
    _save_original(req.seg_id)
    if req.seg_id not in _original_images:
        raise HTTPException(
            status_code=404,
            detail={"error": "invalid_segment_id", "message": "セグメントIDが見つかりません。"},
        )

    original = _original_images[req.seg_id]

    # Check if all adjustments are zero (reset)
    is_reset = all(
        getattr(req, f) == 0.0
        for f in ("brightness", "contrast", "saturation", "temperature", "sharpness")
    )

    if is_reset:
        adjusted = original.image.copy()
    else:
        adjusted = adjust_image(
            original.image,
            brightness=req.brightness,
            contrast=req.contrast,
            saturation=req.saturation,
            temperature=req.temperature,
            sharpness=req.sharpness,
        )

    # Recompute bbox/foot_y
    alpha = np.array(adjusted)[:, :, 3]
    bbox_tuple = compute_bbox(alpha)
    if bbox_tuple:
        x, y, w, h = bbox_tuple
        bbox = {"x": x, "y": y, "width": w, "height": h}
        rows = np.where(np.any(alpha > 10, axis=1))[0]
        foot_y = int(rows[-1]) if len(rows) > 0 else y + h
    else:
        bbox = {"x": 0, "y": 0, "width": adjusted.width, "height": adjusted.height}
        foot_y = adjusted.height

    # Update cache
    entry_new = SegmentedOutput(
        image=adjusted,
        bbox=(bbox["x"], bbox["y"], bbox["width"], bbox["height"]),
        foot_y=foot_y,
        original_size=original.original_size,
    )
    segmentation_cache.put(req.seg_id, entry_new)

    seg_image_b64 = image_to_base64(adjusted, fmt="PNG")

    return AdjustResponse(
        seg_id=req.seg_id,
        segmented_image=seg_image_b64,
        bbox=bbox,
        foot_y=foot_y,
    )
