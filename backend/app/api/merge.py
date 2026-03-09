"""Merge endpoint."""

import logging

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.models.schemas import (
    ErrorResponse,
    ImageSizeModel,
    MergeRequest,
    MergeResponse,
)
from app.services.cache import segmentation_cache
from app.services.compositor import merge_images

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/api/merge", response_model=MergeResponse)
async def merge(request: MergeRequest) -> MergeResponse | JSONResponse:
    """Merge two segmented images."""
    # Retrieve segmentation results from cache
    seg1 = segmentation_cache.get(request.image1_id)
    if seg1 is None:
        return JSONResponse(
            status_code=404,
            content=ErrorResponse(
                error="invalid_segment_id",
                message="セグメンテーション結果が見つかりません。写真を再入力してください。",
                detail=f"Segment ID '{request.image1_id}' not found in cache",
            ).model_dump(),
        )

    seg2 = segmentation_cache.get(request.image2_id)
    if seg2 is None:
        return JSONResponse(
            status_code=404,
            content=ErrorResponse(
                error="invalid_segment_id",
                message="セグメンテーション結果が見つかりません。写真を再入力してください。",
                detail=f"Segment ID '{request.image2_id}' not found in cache",
            ).model_dump(),
        )

    # Execute merge pipeline
    try:
        merged_base64, processing_time_ms, output_size = merge_images(
            seg1, seg2, request.settings, request.preview_mode
        )
    except Exception as e:
        logger.error(f"Merge failed: {e}")
        return JSONResponse(
            status_code=500,
            content=ErrorResponse(
                error="merge_failed",
                message="合成処理中にエラーが発生しました。もう一度お試しください。",
                detail=str(e),
            ).model_dump(),
        )

    return MergeResponse(
        merged_image=merged_base64,
        processing_time_ms=processing_time_ms,
        output_size=ImageSizeModel(width=output_size[0], height=output_size[1]),
    )
