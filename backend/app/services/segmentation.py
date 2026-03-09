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


def _clean_edge_colors(rgba_array: np.ndarray) -> np.ndarray:
    """Clean up semi-transparent edge pixels to remove background color contamination.

    Semi-transparent pixels at the edge of a segmented image often contain
    a mix of foreground and background colors. This function replaces the
    RGB values of semi-transparent pixels with the nearest fully-opaque
    pixel's color, preserving the alpha for smooth blending.
    """
    alpha = rgba_array[:, :, 3]
    rgb = rgba_array[:, :, :3].copy()

    # Identify semi-transparent pixels (10 < alpha < 240)
    semi_mask = (alpha > 10) & (alpha < 240)

    if not np.any(semi_mask):
        return rgba_array

    # Create a mask of fully opaque pixels
    opaque_mask = alpha >= 240

    if not np.any(opaque_mask):
        return rgba_array

    # Use morphological dilation to expand opaque pixel colors into
    # semi-transparent regions
    kernel = np.ones((5, 5), np.uint8)

    for ch in range(3):
        channel = rgb[:, :, ch].copy()
        # Only consider opaque pixels as source
        source = np.where(opaque_mask, channel, 0).astype(np.uint8)
        # Dilate to spread opaque colors outward
        dilated = cv2.dilate(source, kernel, iterations=2)
        # Count mask for proper averaging
        count_src = opaque_mask.astype(np.uint8)
        count_dilated = cv2.dilate(count_src, kernel, iterations=2)
        # Apply dilated colors to semi-transparent pixels
        valid = semi_mask & (count_dilated > 0)
        rgb[valid, ch] = dilated[valid]

    result = rgba_array.copy()
    result[:, :, :3] = rgb
    return result


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
    result_array = np.array(result)
    alpha = result_array[:, :, 3]

    # Check if any foreground was detected
    if np.max(alpha) == 0:
        raise ValueError("No foreground detected by rembg: alpha channel is entirely transparent")

    # Alpha matte refinement:
    # 1. Slight erosion to remove edge artifacts (removes 1px of edge contamination)
    kernel_erode = np.ones((3, 3), np.uint8)
    alpha_eroded = cv2.erode(alpha, kernel_erode, iterations=1)

    # 2. Gentle blur ONLY on the eroded edge (not expanding outward)
    alpha_smooth = cv2.GaussianBlur(alpha_eroded, (3, 3), 0.8)

    # 3. Keep original alpha for clearly opaque pixels, use smoothed for edges
    alpha_refined = np.where(alpha > 240, alpha, alpha_smooth)

    # Apply refined alpha
    result_array[:, :, 3] = alpha_refined

    # Clean up semi-transparent edge colors (remove background contamination)
    result_array = _clean_edge_colors(result_array)

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
