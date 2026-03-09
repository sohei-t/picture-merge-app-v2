"""Image enhancement service for low-resolution photos.

Detects low-resolution images and applies enhancement pipeline:
- Non-local means denoising
- CLAHE contrast enhancement on LAB L-channel
- High-quality LANCZOS upscaling
- Unsharp mask sharpening
"""

from __future__ import annotations

import logging

import cv2
import numpy as np
from PIL import Image

logger = logging.getLogger(__name__)

# Resolution thresholds
VERY_LOW_RES_THRESHOLD = 800   # longest side < 800px → 4x upscale
LOW_RES_THRESHOLD = 1500       # longest side < 1500px → 2x upscale


def detect_resolution_level(image: Image.Image) -> str:
    """Detect resolution level of an image.

    Returns:
        "very_low" (< 800px), "low" (< 1500px), or "normal" (>= 1500px)
    """
    longest = max(image.size)
    if longest < VERY_LOW_RES_THRESHOLD:
        return "very_low"
    elif longest < LOW_RES_THRESHOLD:
        return "low"
    return "normal"


def enhance_image(image: Image.Image) -> tuple[Image.Image, str, int]:
    """Enhance a low-resolution image.

    Auto-detects resolution and applies appropriate enhancement.

    Args:
        image: Input PIL Image (RGB)

    Returns:
        Tuple of (enhanced_image, resolution_level, scale_factor)
        If image is already high-res, returns (original, "normal", 1)
    """
    level = detect_resolution_level(image)

    if level == "normal":
        return image, level, 1

    scale = 4 if level == "very_low" else 2
    logger.info(f"Low-res image detected ({image.size}), applying {scale}x enhancement")

    # Convert to RGB if needed (strip alpha for enhancement)
    orig_mode = image.mode
    if image.mode == "RGBA":
        rgb = image.convert("RGB")
        alpha = image.split()[3]
    else:
        rgb = image if image.mode == "RGB" else image.convert("RGB")
        alpha = None

    arr = np.array(rgb)

    # Step 1: Denoise (Non-local means - good for old photo noise)
    arr = cv2.fastNlMeansDenoisingColored(arr, None, h=6, hColor=6,
                                          templateWindowSize=7,
                                          searchWindowSize=21)

    # Step 2: Contrast enhancement via CLAHE on LAB L-channel
    lab = cv2.cvtColor(arr, cv2.COLOR_RGB2LAB)
    l_ch = lab[:, :, 0]
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    lab[:, :, 0] = clahe.apply(l_ch)
    arr = cv2.cvtColor(lab, cv2.COLOR_LAB2RGB)

    # Step 3: High-quality upscale via PIL LANCZOS
    enhanced = Image.fromarray(arr, "RGB")
    new_w = image.width * scale
    new_h = image.height * scale
    enhanced = enhanced.resize((new_w, new_h), Image.LANCZOS)

    # Step 4: Unsharp mask for sharpening after upscale
    arr_up = np.array(enhanced)
    blurred = cv2.GaussianBlur(arr_up, (0, 0), sigmaX=1.5)
    # sharpened = original + (original - blurred) * amount
    sharpened = cv2.addWeighted(arr_up, 1.5, blurred, -0.5, 0)
    sharpened = np.clip(sharpened, 0, 255).astype(np.uint8)
    enhanced = Image.fromarray(sharpened, "RGB")

    # Restore alpha if present
    if alpha is not None:
        alpha_up = alpha.resize((new_w, new_h), Image.LANCZOS)
        enhanced = enhanced.convert("RGBA")
        enhanced.putalpha(alpha_up)
    elif orig_mode == "RGBA":
        enhanced = enhanced.convert("RGBA")

    logger.info(f"Enhancement complete: {image.size} → {enhanced.size}")
    return enhanced, level, scale
