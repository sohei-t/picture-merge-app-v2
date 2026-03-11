"""Region detection service using connected component analysis.

Detects independent foreground regions in a segmented RGBA image
to identify multiple people or objects that can be individually removed.
"""

from __future__ import annotations

import logging

import cv2
import numpy as np
from PIL import Image

from app.utils.image_utils import compute_bbox, image_to_base64

logger = logging.getLogger(__name__)

# Minimum region area as fraction of total foreground area
MIN_REGION_RATIO = 0.02  # Ignore regions smaller than 2% of total foreground


def detect_regions(image: Image.Image) -> list[dict]:
    """Detect independent foreground regions in a segmented RGBA image.

    Uses connected component analysis on the alpha channel to find
    spatially separated foreground blobs.

    Args:
        image: RGBA PIL Image from segmentation

    Returns:
        List of region dicts sorted by area (largest first):
        [
            {
                "region_id": 0,
                "bbox": {"x": int, "y": int, "width": int, "height": int},
                "area": int,
                "center": {"x": int, "y": int},
                "thumbnail": "data:image/png;base64,...",
                "is_main": bool,  # True for the largest region
            },
            ...
        ]
    """
    rgba = np.array(image)
    alpha = rgba[:, :, 3]

    # Threshold alpha to get binary foreground mask
    _, binary = cv2.threshold(alpha, 10, 255, cv2.THRESH_BINARY)

    # Morphological close to bridge small gaps within a single person
    # (e.g., gaps between arm and body)
    kernel = np.ones((15, 15), np.uint8)
    closed = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)

    # Connected component analysis
    num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(
        closed, connectivity=8
    )

    # Total foreground area (excluding background label 0)
    total_fg_area = int(np.sum(binary > 0))
    if total_fg_area == 0:
        empty_labels = np.zeros(alpha.shape, dtype=np.int32)
        return [], empty_labels, {}

    min_area = max(500, int(total_fg_area * MIN_REGION_RATIO))

    regions: list[dict] = []

    for label_id in range(1, num_labels):  # Skip background (label 0)
        area = int(stats[label_id, cv2.CC_STAT_AREA])
        if area < min_area:
            continue

        x = int(stats[label_id, cv2.CC_STAT_LEFT])
        y = int(stats[label_id, cv2.CC_STAT_TOP])
        w = int(stats[label_id, cv2.CC_STAT_WIDTH])
        h = int(stats[label_id, cv2.CC_STAT_HEIGHT])
        cx = int(centroids[label_id][0])
        cy = int(centroids[label_id][1])

        # Create thumbnail: crop the region from original RGBA using actual alpha
        # (not the morphologically closed version)
        region_mask = (labels == label_id).astype(np.uint8) * 255

        # Combine with original alpha to get actual pixels for this region
        region_alpha = np.minimum(alpha, region_mask)
        region_rgba = rgba.copy()
        region_rgba[:, :, 3] = region_alpha

        # Crop to bbox
        cropped = region_rgba[y : y + h, x : x + w]
        thumb_img = Image.fromarray(cropped, "RGBA")

        # Scale thumbnail to max 100px
        max_side = max(w, h)
        if max_side > 100:
            scale = 100 / max_side
            thumb_img = thumb_img.resize(
                (max(1, int(w * scale)), max(1, int(h * scale))),
                Image.LANCZOS,
            )

        thumbnail = image_to_base64(thumb_img, fmt="PNG")

        regions.append(
            {
                "region_id": len(regions),
                "bbox": {"x": x, "y": y, "width": w, "height": h},
                "area": area,
                "center": {"x": cx, "y": cy},
                "thumbnail": thumbnail,
                "is_main": False,  # Will be set below
                "_label_id": label_id,  # Internal use, removed before return
                "_labels": None,  # Placeholder
            }
        )

    # Sort by area descending, mark largest as main
    regions.sort(key=lambda r: r["area"], reverse=True)
    if regions:
        regions[0]["is_main"] = True

    # Re-assign region_id after sorting
    for i, r in enumerate(regions):
        r["region_id"] = i

    # Store label mapping for erasing
    label_map = {}
    for r in regions:
        label_map[r["region_id"]] = r.pop("_label_id")
        r.pop("_labels", None)

    return regions, labels, label_map


def erase_regions(
    image: Image.Image,
    labels: np.ndarray,
    label_map: dict[int, int],
    region_ids_to_erase: list[int],
) -> Image.Image:
    """Erase specified regions from the image by setting their alpha to 0.

    Args:
        image: RGBA PIL Image
        labels: Label array from connectedComponentsWithStats
        label_map: Mapping from region_id to label_id
        region_ids_to_erase: List of region_ids to remove

    Returns:
        Modified RGBA PIL Image with erased regions
    """
    rgba = np.array(image)

    # Build mask of pixels to erase
    erase_mask = np.zeros(rgba.shape[:2], dtype=bool)
    for rid in region_ids_to_erase:
        if rid in label_map:
            lid = label_map[rid]
            erase_mask |= labels == lid

    # Set alpha to 0 for erased pixels
    rgba[erase_mask, 3] = 0

    return Image.fromarray(rgba, "RGBA")


def erase_manual(
    image: Image.Image,
    mask_data: list[dict],
    image_display_width: int,
    image_display_height: int,
) -> Image.Image:
    """Erase regions using manually drawn brush strokes.

    Args:
        image: RGBA PIL Image
        mask_data: List of brush stroke dicts:
            [{"x": float, "y": float, "radius": float}, ...]
            Coordinates are in display-space (0 to display_width/height).
        image_display_width: Width of the image as displayed in the UI
        image_display_height: Height of the image as displayed in the UI

    Returns:
        Modified RGBA PIL Image with erased regions
    """
    rgba = np.array(image)
    h, w = rgba.shape[:2]

    # Scale factors from display space to actual image space
    sx = w / image_display_width
    sy = h / image_display_height

    # Create erase mask
    mask = np.zeros((h, w), dtype=np.uint8)

    for stroke in mask_data:
        cx = int(stroke["x"] * sx)
        cy = int(stroke["y"] * sy)
        r = max(1, int(stroke["radius"] * max(sx, sy)))
        cv2.circle(mask, (cx, cy), r, 255, -1)

    # Apply Gaussian blur for soft edges
    if mask.any():
        mask = cv2.GaussianBlur(mask, (5, 5), 2)

    # Erase: reduce alpha where mask is active
    alpha = rgba[:, :, 3].astype(np.float32)
    erase_strength = mask.astype(np.float32) / 255.0
    alpha = alpha * (1.0 - erase_strength)
    rgba[:, :, 3] = alpha.astype(np.uint8)

    return Image.fromarray(rgba, "RGBA")
