"""Segmentation endpoint."""

import logging
import time

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import JSONResponse

from app.models.schemas import (
    BBoxModel,
    ErrorResponse,
    ImageSizeModel,
    SegmentResponse,
)
from app.services.segmentation import segment_image
from app.utils.image_utils import (
    MAX_FILE_SIZE,
    SUPPORTED_CONTENT_TYPES,
    decode_image,
    image_to_base64,
    resize_if_needed,
    validate_magic_bytes,
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/api/segment", response_model=SegmentResponse)
async def segment(image: UploadFile = File(...)) -> SegmentResponse | JSONResponse:
    """Segment a person from an uploaded image."""
    start_time = time.time()

    # Validate content type
    content_type = image.content_type or ""
    if content_type not in SUPPORTED_CONTENT_TYPES:
        return JSONResponse(
            status_code=400,
            content=ErrorResponse(
                error="invalid_image",
                message="対応していない画像形式です。JPEG/PNG/WebPファイルを使用してください。",
                detail=f"Unsupported content type: {content_type}",
            ).model_dump(),
        )

    # Read file data
    data = await image.read()

    # Validate file size
    if len(data) > MAX_FILE_SIZE:
        size_mb = round(len(data) / (1024 * 1024), 1)
        return JSONResponse(
            status_code=413,
            content=ErrorResponse(
                error="file_too_large",
                message="ファイルサイズが20MBを超えています。",
                detail=f"File size: {size_mb}MB, max: 20MB",
            ).model_dump(),
        )

    # Validate magic bytes
    if not validate_magic_bytes(data):
        return JSONResponse(
            status_code=400,
            content=ErrorResponse(
                error="invalid_image",
                message="対応していない画像形式です。JPEG/PNG/WebPファイルを使用してください。",
                detail="Magic bytes validation failed",
            ).model_dump(),
        )

    # Decode image
    try:
        pil_image = decode_image(data)
    except Exception as e:
        return JSONResponse(
            status_code=400,
            content=ErrorResponse(
                error="invalid_image",
                message="対応していない画像形式です。JPEG/PNG/WebPファイルを使用してください。",
                detail=f"Failed to decode image: {str(e)}",
            ).model_dump(),
        )

    original_size = pil_image.size  # (width, height)

    # Resize if needed
    pil_image, was_resized = resize_if_needed(pil_image)
    if was_resized:
        logger.warning(
            f"Image resized from {original_size} to {pil_image.size} (max dimension: 4000px)"
        )

    # Run segmentation
    try:
        seg_id, output = segment_image(pil_image, original_size)
    except ValueError as e:
        return JSONResponse(
            status_code=422,
            content=ErrorResponse(
                error="segmentation_failed",
                message="人物を検出できませんでした。人物が写った写真を使用してください。",
                detail=str(e),
            ).model_dump(),
        )
    except RuntimeError as e:
        logger.error(f"Segmentation failed: {e}")
        return JSONResponse(
            status_code=500,
            content=ErrorResponse(
                error="internal_error",
                message="サーバー内部エラーが発生しました。",
                detail=str(e),
            ).model_dump(),
        )

    # Encode segmented image
    segmented_base64 = image_to_base64(output.image, fmt="PNG")

    processing_time_ms = int((time.time() - start_time) * 1000)

    x, y, w, h = output.bbox
    return SegmentResponse(
        id=seg_id,
        segmented_image=segmented_base64,
        bbox=BBoxModel(x=x, y=y, width=w, height=h),
        foot_y=output.foot_y,
        original_size=ImageSizeModel(width=original_size[0], height=original_size[1]),
        processing_time_ms=processing_time_ms,
    )
