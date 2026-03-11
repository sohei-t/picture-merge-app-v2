"""Merge/composition pipeline for combining segmented images."""

from __future__ import annotations

import logging
import time
from typing import Optional

import numpy as np
from PIL import Image

from app.models.schemas import MergeSettingsModel
from app.services.cache import SegmentedOutput, segmentation_cache
from app.services.color_correction import match_color
from app.services.shadow_generator import generate_shadow
from app.utils.image_utils import image_to_base64

logger = logging.getLogger(__name__)


def _crop_to_bbox(output: SegmentedOutput) -> tuple[Image.Image, int]:
    """Crop segmented image to its bounding box.

    Returns:
        Tuple of (cropped_image, foot_y_relative)
    """
    x, y, w, h = output.bbox
    cropped = output.image.crop((x, y, x + w, y + h))
    foot_y_relative = output.foot_y - y
    return cropped, foot_y_relative


def _compute_auto_scale(
    person1_height: int,
    person2_height: int,
) -> float:
    """Compute auto scale ratio clamped to 0.8-1.2.

    Returns the ratio to apply to person2 relative to person1.
    """
    if person2_height == 0:
        return 1.0
    height_ratio = person1_height / person2_height
    return max(0.8, min(1.2, height_ratio))


def merge_images(
    seg1: SegmentedOutput,
    seg2: SegmentedOutput,
    settings: MergeSettingsModel,
    preview_mode: bool = False,
    output_format: str = "PNG",
    crop: dict | None = None,
) -> tuple[str, int, tuple[int, int]]:
    """Execute the merge pipeline.

    Args:
        seg1: Person 1 segmentation result
        seg2: Person 2 segmentation result
        settings: Merge settings
        preview_mode: If True, output 512x512 JPEG

    Returns:
        Tuple of (base64_image, processing_time_ms, (width, height))
    """
    start_time = time.time()

    canvas_width = settings.output_width
    canvas_height = settings.output_height

    # Step 1: Crop to bounding box
    person1_img, person1_foot_rel = _crop_to_bbox(seg1)
    person2_img, person2_foot_rel = _crop_to_bbox(seg2)

    # Step 2: Color correction (person1 is reference, person2 is corrected)
    if settings.color_correction:
        person2_img = match_color(person2_img, person1_img)

    # Step 3: Scale calculation
    p1_h = person1_img.height
    p2_h = person2_img.height

    # Target height is 70% of canvas
    target_height = canvas_height * 0.7

    # Auto scale ratio
    auto_ratio = _compute_auto_scale(p1_h, p2_h)

    # Compute scale factors
    if p1_h > 0:
        scale1 = (target_height / p1_h) * settings.person1.scale
    else:
        scale1 = settings.person1.scale

    if p2_h > 0:
        scale2 = (target_height / p2_h) * auto_ratio * settings.person2.scale
    else:
        scale2 = settings.person2.scale

    # Resize persons
    new_w1 = max(1, int(person1_img.width * scale1))
    new_h1 = max(1, int(person1_img.height * scale1))
    person1_scaled = person1_img.resize((new_w1, new_h1), Image.LANCZOS)

    new_w2 = max(1, int(person2_img.width * scale2))
    new_h2 = max(1, int(person2_img.height * scale2))
    person2_scaled = person2_img.resize((new_w2, new_h2), Image.LANCZOS)

    # Step 3b: Apply rotation & flip transforms
    person1_scaled = _apply_transforms(
        person1_scaled, settings.person1.rotation,
        settings.person1.flip_h, settings.person1.flip_v,
    )
    person2_scaled = _apply_transforms(
        person2_scaled, settings.person2.rotation,
        settings.person2.flip_h, settings.person2.flip_v,
    )
    # Update dimensions after transforms (rotation may change size)
    new_w1, new_h1 = person1_scaled.size
    new_w2, new_h2 = person2_scaled.size

    # Step 4: Position calculation
    foot_line_y = int(canvas_height * 0.8)

    # Person 1 position
    p1_center_x = int(canvas_width * settings.person1.x)
    p1_left = p1_center_x - new_w1 // 2
    p1_foot_scaled = int(person1_foot_rel * scale1)
    p1_top = foot_line_y - p1_foot_scaled + settings.person1.y_offset

    # Person 2 position
    p2_center_x = int(canvas_width * settings.person2.x)
    p2_left = p2_center_x - new_w2 // 2
    p2_foot_scaled = int(person2_foot_rel * scale2)
    p2_top = foot_line_y - p2_foot_scaled + settings.person2.y_offset

    # Step 5: Create background canvas
    bg_color = _hex_to_rgb(settings.background_color)
    canvas = Image.new("RGBA", (canvas_width, canvas_height), (*bg_color, 255))

    # Step 6: Shadow generation
    if settings.shadow.enabled and settings.shadow.intensity > 0:
        # Person 1 shadow
        shadow1 = generate_shadow(
            canvas_width,
            canvas_height,
            foot_x=p1_center_x,
            foot_y=foot_line_y + settings.person1.y_offset,
            person_width=new_w1,
            intensity=settings.shadow.intensity,
        )
        # Person 2 shadow
        shadow2 = generate_shadow(
            canvas_width,
            canvas_height,
            foot_x=p2_center_x,
            foot_y=foot_line_y + settings.person2.y_offset,
            person_width=new_w2,
            intensity=settings.shadow.intensity,
        )
        # Combine shadows
        combined_shadow = np.maximum(shadow1, shadow2)
        shadow_img = Image.fromarray(combined_shadow, "RGBA")
        canvas = Image.alpha_composite(canvas, shadow_img)

    # Step 7: Composite persons onto canvas (layer order determines who is in front)
    if settings.layer_order == "person2_back":
        canvas = _paste_with_alpha(canvas, person2_scaled, p2_left, p2_top)
        canvas = _paste_with_alpha(canvas, person1_scaled, p1_left, p1_top)
    else:
        canvas = _paste_with_alpha(canvas, person1_scaled, p1_left, p1_top)
        canvas = _paste_with_alpha(canvas, person2_scaled, p2_left, p2_top)

    # Step 8: Server-side crop (if requested)
    if crop:
        x1 = max(0.0, min(1.0, crop.get("x1", 0)))
        y1 = max(0.0, min(1.0, crop.get("y1", 0)))
        x2 = max(0.0, min(1.0, crop.get("x2", 1)))
        y2 = max(0.0, min(1.0, crop.get("y2", 1)))
        cx = int(x1 * canvas_width)
        cy = int(y1 * canvas_height)
        cw = max(1, int((x2 - x1) * canvas_width))
        ch = max(1, int((y2 - y1) * canvas_height))
        canvas = canvas.crop((cx, cy, cx + cw, cy + ch))

    # Step 9: Output
    if preview_mode:
        # Scale down proportionally for preview, max 768px on longest side
        max_preview = 768
        pw, ph = canvas.size
        if max(pw, ph) > max_preview:
            ratio = max_preview / max(pw, ph)
            preview_w = int(pw * ratio)
            preview_h = int(ph * ratio)
        else:
            preview_w, preview_h = pw, ph
        canvas = canvas.resize((preview_w, preview_h), Image.LANCZOS)
        output_image = image_to_base64(canvas, fmt="JPEG", quality=80)
        output_size = (preview_w, preview_h)
    else:
        fmt = output_format.upper() if output_format else "PNG"
        if fmt == "JPEG":
            output_image = image_to_base64(canvas, fmt="JPEG", quality=95)
        else:
            output_image = image_to_base64(canvas, fmt="PNG")
        output_size = canvas.size

    processing_time_ms = int((time.time() - start_time) * 1000)

    return output_image, processing_time_ms, output_size


def _apply_transforms(
    img: Image.Image,
    rotation: float,
    flip_h: bool,
    flip_v: bool,
) -> Image.Image:
    """Apply rotation and flip transforms to a person image.

    Args:
        img: RGBA person image
        rotation: Rotation angle in degrees (positive = counter-clockwise)
        flip_h: Horizontal flip
        flip_v: Vertical flip

    Returns:
        Transformed RGBA image
    """
    if flip_h:
        img = img.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
    if flip_v:
        img = img.transpose(Image.Transpose.FLIP_TOP_BOTTOM)
    if rotation != 0:
        # expand=True to avoid clipping corners; fillcolor transparent
        img = img.rotate(rotation, expand=True, fillcolor=(0, 0, 0, 0), resample=Image.BICUBIC)
    return img


def _hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    """Convert hex color string to RGB tuple."""
    hex_color = hex_color.lstrip("#")
    return tuple(int(hex_color[i : i + 2], 16) for i in (0, 2, 4))


def _paste_with_alpha(
    canvas: Image.Image, overlay: Image.Image, x: int, y: int
) -> Image.Image:
    """Paste an RGBA overlay onto canvas at position (x, y) with alpha blending.

    Handles cases where overlay extends beyond canvas bounds.
    """
    canvas_w, canvas_h = canvas.size
    ov_w, ov_h = overlay.size

    # Calculate source and destination regions
    src_x = max(0, -x)
    src_y = max(0, -y)
    dst_x = max(0, x)
    dst_y = max(0, y)

    paste_w = min(ov_w - src_x, canvas_w - dst_x)
    paste_h = min(ov_h - src_y, canvas_h - dst_y)

    if paste_w <= 0 or paste_h <= 0:
        return canvas

    # Crop overlay to the visible portion
    cropped = overlay.crop((src_x, src_y, src_x + paste_w, src_y + paste_h))

    # Create a temporary canvas-sized RGBA image
    temp = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    temp.paste(cropped, (dst_x, dst_y))

    return Image.alpha_composite(canvas, temp)
