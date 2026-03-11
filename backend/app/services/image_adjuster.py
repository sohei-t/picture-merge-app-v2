"""Manual image adjustment service.

Applies user-controlled adjustments to segmented person images:
brightness, contrast, saturation, color temperature, sharpness.
All operations work on RGBA images preserving the alpha channel.
"""

from __future__ import annotations

import logging

import cv2
import numpy as np
from PIL import Image, ImageEnhance

logger = logging.getLogger(__name__)


def adjust_image(
    image: Image.Image,
    brightness: float = 0.0,
    contrast: float = 0.0,
    saturation: float = 0.0,
    temperature: float = 0.0,
    sharpness: float = 0.0,
) -> Image.Image:
    """Apply manual adjustments to an image.

    All parameters are in [-1.0, 1.0] range where 0.0 = no change.

    Args:
        image: RGBA PIL Image
        brightness: -1.0 (darker) to 1.0 (brighter)
        contrast: -1.0 (flat) to 1.0 (high contrast)
        saturation: -1.0 (desaturated) to 1.0 (vivid)
        temperature: -1.0 (cool/blue) to 1.0 (warm/yellow)
        sharpness: -1.0 (softer) to 1.0 (sharper)

    Returns:
        Adjusted RGBA PIL Image
    """
    # Separate alpha
    has_alpha = image.mode == "RGBA"
    if has_alpha:
        alpha = image.split()[3]
        rgb = image.convert("RGB")
    else:
        alpha = None
        rgb = image if image.mode == "RGB" else image.convert("RGB")

    # Apply PIL-based adjustments (simpler, well-tested)
    if brightness != 0.0:
        # PIL factor: 1.0 = original, 0.0 = black, 2.0 = 2x bright
        factor = 1.0 + brightness  # maps [-1,1] to [0,2]
        rgb = ImageEnhance.Brightness(rgb).enhance(factor)

    if contrast != 0.0:
        factor = 1.0 + contrast
        rgb = ImageEnhance.Contrast(rgb).enhance(factor)

    if saturation != 0.0:
        factor = 1.0 + saturation
        rgb = ImageEnhance.Color(rgb).enhance(factor)

    if sharpness != 0.0:
        # PIL sharpness: 0=blurred, 1=original, 2=sharpened
        factor = 1.0 + sharpness
        rgb = ImageEnhance.Sharpness(rgb).enhance(factor)

    # Temperature requires OpenCV LAB manipulation
    if temperature != 0.0:
        rgb = _adjust_temperature(rgb, temperature)

    # Restore alpha
    if has_alpha and alpha is not None:
        rgb = rgb.convert("RGBA")
        rgb.putalpha(alpha)

    return rgb


def _adjust_temperature(image: Image.Image, temp: float) -> Image.Image:
    """Adjust color temperature via LAB a/b channels.

    Positive temp = warmer (more yellow/red)
    Negative temp = cooler (more blue)
    """
    arr = np.array(image)
    lab = cv2.cvtColor(arr, cv2.COLOR_RGB2LAB).astype(np.float32)

    # Adjust b channel (blue-yellow axis)
    # Warm = increase b, Cool = decrease b
    shift = temp * 15  # Scale factor for visible effect
    lab[:, :, 2] = np.clip(lab[:, :, 2] + shift, 0, 255)

    # Slight a channel shift for natural warmth
    lab[:, :, 1] = np.clip(lab[:, :, 1] + shift * 0.3, 0, 255)

    lab = lab.astype(np.uint8)
    result = cv2.cvtColor(lab, cv2.COLOR_LAB2RGB)
    return Image.fromarray(result, "RGB")
