"""Eraser endpoints for removing unwanted regions from segmented images."""

import logging
import time

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Optional

from app.models.schemas import BBoxModel, ErrorResponse
from app.services.cache import SegmentedOutput, segmentation_cache
from app.services.region_detector import detect_regions, erase_regions, erase_manual
from app.utils.image_utils import compute_bbox, image_to_base64

logger = logging.getLogger(__name__)

router = APIRouter()

# Temporary storage for region detection results (labels + label_map)
# Keyed by seg_id, cleared when regions are erased
_detection_cache: dict[str, dict] = {}


class RegionInfo(BaseModel):
    """A detected foreground region."""

    region_id: int
    bbox: BBoxModel
    area: int
    center: dict
    thumbnail: str
    is_main: bool


class DetectRegionsResponse(BaseModel):
    """Response for POST /api/detect-regions."""

    seg_id: str
    region_count: int
    regions: list[RegionInfo]
    processing_time_ms: int


class EraseRegionsRequest(BaseModel):
    """Request for POST /api/erase-regions."""

    seg_id: str = Field(..., description="Segmentation result ID")
    region_ids: list[int] = Field(..., description="Region IDs to erase")


class BrushStroke(BaseModel):
    """A single brush stroke point."""

    x: float = Field(..., description="X coordinate in display space")
    y: float = Field(..., description="Y coordinate in display space")
    radius: float = Field(..., ge=1, le=200, description="Brush radius in display pixels")


class EraseManualRequest(BaseModel):
    """Request for POST /api/erase-manual."""

    seg_id: str = Field(..., description="Segmentation result ID")
    strokes: list[BrushStroke] = Field(..., description="Brush stroke points")
    display_width: int = Field(..., ge=1, description="Display width of image in UI")
    display_height: int = Field(..., ge=1, description="Display height of image in UI")


class EraseResponse(BaseModel):
    """Response for erase operations."""

    seg_id: str
    segmented_image: str
    bbox: BBoxModel
    foot_y: int
    processing_time_ms: int


@router.post("/api/detect-regions/{seg_id}", response_model=DetectRegionsResponse)
async def detect_regions_endpoint(seg_id: str) -> DetectRegionsResponse | JSONResponse:
    """Detect independent foreground regions in a segmented image."""
    start_time = time.time()

    entry = segmentation_cache.get(seg_id)
    if entry is None:
        return JSONResponse(
            status_code=404,
            content=ErrorResponse(
                error="invalid_segment_id",
                message="セグメンテーション結果が見つかりません。写真を再入力してください。",
                detail=f"Segment ID not found: {seg_id}",
            ).model_dump(),
        )

    try:
        regions_data, labels, label_map = detect_regions(entry.image)
    except Exception as e:
        logger.error(f"Region detection failed: {e}")
        return JSONResponse(
            status_code=500,
            content=ErrorResponse(
                error="internal_error",
                message="領域検出に失敗しました。",
                detail=str(e),
            ).model_dump(),
        )

    # Cache detection results for subsequent erase operation
    _detection_cache[seg_id] = {
        "labels": labels,
        "label_map": label_map,
    }

    regions = [
        RegionInfo(
            region_id=r["region_id"],
            bbox=BBoxModel(
                x=r["bbox"]["x"],
                y=r["bbox"]["y"],
                width=r["bbox"]["width"],
                height=r["bbox"]["height"],
            ),
            area=r["area"],
            center=r["center"],
            thumbnail=r["thumbnail"],
            is_main=r["is_main"],
        )
        for r in regions_data
    ]

    processing_time_ms = int((time.time() - start_time) * 1000)

    return DetectRegionsResponse(
        seg_id=seg_id,
        region_count=len(regions),
        regions=regions,
        processing_time_ms=processing_time_ms,
    )


@router.post("/api/erase-regions", response_model=EraseResponse)
async def erase_regions_endpoint(request: EraseRegionsRequest) -> EraseResponse | JSONResponse:
    """Erase specified regions from a segmented image."""
    start_time = time.time()

    entry = segmentation_cache.get(request.seg_id)
    if entry is None:
        return JSONResponse(
            status_code=404,
            content=ErrorResponse(
                error="invalid_segment_id",
                message="セグメンテーション結果が見つかりません。写真を再入力してください。",
                detail=f"Segment ID not found: {request.seg_id}",
            ).model_dump(),
        )

    detection = _detection_cache.get(request.seg_id)
    if detection is None:
        return JSONResponse(
            status_code=400,
            content=ErrorResponse(
                error="validation_error",
                message="先に領域検出を実行してください。",
                detail="No detection results found. Call /api/detect-regions first.",
            ).model_dump(),
        )

    try:
        erased_image = erase_regions(
            entry.image,
            detection["labels"],
            detection["label_map"],
            request.region_ids,
        )
    except Exception as e:
        logger.error(f"Region erase failed: {e}")
        return JSONResponse(
            status_code=500,
            content=ErrorResponse(
                error="internal_error",
                message="領域消去に失敗しました。",
                detail=str(e),
            ).model_dump(),
        )

    # Update cache with erased image
    import numpy as np

    alpha = np.array(erased_image)[:, :, 3]
    bbox = compute_bbox(alpha)
    if bbox is None:
        return JSONResponse(
            status_code=422,
            content=ErrorResponse(
                error="segmentation_failed",
                message="すべての領域が消去されました。少なくとも1つの領域を残してください。",
                detail="All foreground was erased",
            ).model_dump(),
        )

    x, y, w, h = bbox
    foot_y = y + h

    updated = SegmentedOutput(
        image=erased_image,
        bbox=bbox,
        foot_y=foot_y,
        original_size=entry.original_size,
    )
    segmentation_cache.put(request.seg_id, updated)

    # Clean up detection cache
    _detection_cache.pop(request.seg_id, None)

    segmented_base64 = image_to_base64(erased_image, fmt="PNG")
    processing_time_ms = int((time.time() - start_time) * 1000)

    return EraseResponse(
        seg_id=request.seg_id,
        segmented_image=segmented_base64,
        bbox=BBoxModel(x=x, y=y, width=w, height=h),
        foot_y=foot_y,
        processing_time_ms=processing_time_ms,
    )


@router.post("/api/erase-manual", response_model=EraseResponse)
async def erase_manual_endpoint(request: EraseManualRequest) -> EraseResponse | JSONResponse:
    """Erase regions using manually drawn brush strokes."""
    start_time = time.time()

    entry = segmentation_cache.get(request.seg_id)
    if entry is None:
        return JSONResponse(
            status_code=404,
            content=ErrorResponse(
                error="invalid_segment_id",
                message="セグメンテーション結果が見つかりません。写真を再入力してください。",
                detail=f"Segment ID not found: {request.seg_id}",
            ).model_dump(),
        )

    try:
        erased_image = erase_manual(
            entry.image,
            [s.model_dump() for s in request.strokes],
            request.display_width,
            request.display_height,
        )
    except Exception as e:
        logger.error(f"Manual erase failed: {e}")
        return JSONResponse(
            status_code=500,
            content=ErrorResponse(
                error="internal_error",
                message="手動消去に失敗しました。",
                detail=str(e),
            ).model_dump(),
        )

    # Update cache
    import numpy as np

    alpha = np.array(erased_image)[:, :, 3]
    bbox = compute_bbox(alpha)
    if bbox is None:
        return JSONResponse(
            status_code=422,
            content=ErrorResponse(
                error="segmentation_failed",
                message="すべての領域が消去されました。",
                detail="All foreground was erased",
            ).model_dump(),
        )

    x, y, w, h = bbox
    foot_y = y + h

    updated = SegmentedOutput(
        image=erased_image,
        bbox=bbox,
        foot_y=foot_y,
        original_size=entry.original_size,
    )
    segmentation_cache.put(request.seg_id, updated)

    segmented_base64 = image_to_base64(erased_image, fmt="PNG")
    processing_time_ms = int((time.time() - start_time) * 1000)

    return EraseResponse(
        seg_id=request.seg_id,
        segmented_image=segmented_base64,
        bbox=BBoxModel(x=x, y=y, width=w, height=h),
        foot_y=foot_y,
        processing_time_ms=processing_time_ms,
    )
