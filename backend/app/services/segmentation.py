"""Segmentation service using rembg."""

from __future__ import annotations

import logging
import time
import uuid

import cv2
import numpy as np
from PIL import Image

from app.services.cache import SegmentedOutput, segmentation_cache
from app.utils.image_utils import compute_bbox

logger = logging.getLogger(__name__)

# Global state for rembg model
_rembg_session = None
_rembg_loaded = False

# Import rembg.remove at module level (allows mocking in tests)
try:
    from rembg import remove
except ImportError:
    remove = None  # Will be set/mocked in tests


def preload_rembg() -> None:
    """Preload rembg model at startup."""
    global _rembg_session, _rembg_loaded
    try:
        from rembg import new_session

        _rembg_session = new_session("u2net")
        _rembg_loaded = True
        logger.info("rembg model loaded successfully")
    except Exception as e:
        logger.warning(f"Failed to preload rembg model: {e}")
        _rembg_loaded = False


def is_rembg_loaded() -> bool:
    """Check if rembg model is loaded."""
    return _rembg_loaded


def segment_image(image: Image.Image, original_size: tuple[int, int]) -> tuple[str, SegmentedOutput]:
    """Run segmentation on an image.

    Args:
        image: PIL Image (RGB or RGBA)
        original_size: Original image size before any resizing (width, height)

    Returns:
        Tuple of (segmentation_id, SegmentedOutput)

    Raises:
        ValueError: If no foreground is detected
        RuntimeError: If rembg processing fails
    """
    global _rembg_session, _rembg_loaded

    try:
        # Use module-level remove (can be mocked in tests)
        result = remove(image, session=_rembg_session)

        if not _rembg_loaded:
            _rembg_loaded = True

    except Exception as e:
        raise RuntimeError(f"rembg processing failed: {e}")

    # Ensure RGBA
    if result.mode != "RGBA":
        result = result.convert("RGBA")

    # Get alpha channel
    alpha = np.array(result)[:, :, 3]

    # Check if any foreground was detected
    if np.max(alpha) == 0:
        raise ValueError("No foreground detected by rembg: alpha channel is entirely transparent")

    # Alpha matte refinement: Gaussian blur for smooth edges
    alpha_refined = cv2.GaussianBlur(alpha, (5, 5), 1.5)

    # Apply refined alpha back to image
    result_array = np.array(result)
    result_array[:, :, 3] = alpha_refined
    result = Image.fromarray(result_array, "RGBA")

    # Compute bounding box
    bbox = compute_bbox(alpha_refined)
    if bbox is None:
        raise ValueError("No foreground detected by rembg: alpha channel is entirely transparent")

    x, y, w, h = bbox
    foot_y = y + h

    # Generate unique ID
    seg_id = f"seg_{uuid.uuid4().hex[:8]}"

    # Create output
    output = SegmentedOutput(
        image=result,
        bbox=bbox,
        foot_y=foot_y,
        original_size=original_size,
    )

    # Store in cache
    segmentation_cache.put(seg_id, output)

    return seg_id, output
