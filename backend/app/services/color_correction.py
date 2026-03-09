"""Color correction using LAB color space histogram matching.

Only matches chrominance (A, B channels) to unify color temperature
without altering brightness/lightness (L channel).
"""

import cv2
import numpy as np
from PIL import Image


def match_color(
    source: Image.Image,
    reference: Image.Image,
    strength: float = 0.6,
) -> Image.Image:
    """Match the color temperature of source to reference using LAB color space.

    Only adjusts A (green-red) and B (blue-yellow) channels to unify
    color temperature without changing brightness. Uses a blend factor
    to prevent over-correction.

    Args:
        source: Image to be corrected (RGBA)
        reference: Reference image for color matching (RGBA)
        strength: Blend factor 0.0 (no correction) to 1.0 (full). Default 0.6.

    Returns:
        Color-corrected source image (RGBA, alpha preserved)
    """
    src_rgba = np.array(source)
    ref_rgba = np.array(reference)

    # Preserve alpha channel
    src_alpha = src_rgba[:, :, 3].copy() if src_rgba.shape[2] == 4 else None

    src_rgb = src_rgba[:, :, :3]
    ref_rgb = ref_rgba[:, :, :3]

    # Convert to LAB color space
    src_lab = cv2.cvtColor(src_rgb, cv2.COLOR_RGB2LAB).astype(np.float64)
    ref_lab = cv2.cvtColor(ref_rgb, cv2.COLOR_RGB2LAB).astype(np.float64)

    # Create masks for non-transparent pixels (alpha > 128 for better quality)
    src_mask = src_alpha > 128 if src_alpha is not None else np.ones(src_lab.shape[:2], dtype=bool)
    ref_mask = ref_rgba[:, :, 3] > 128 if ref_rgba.shape[2] == 4 else np.ones(ref_lab.shape[:2], dtype=bool)

    # Only match A and B channels (index 1 and 2), SKIP L (lightness, index 0)
    for ch in (1, 2):
        src_ch = src_lab[:, :, ch]
        ref_ch = ref_lab[:, :, ch]

        # Compute stats only on opaque pixels
        src_pixels = src_ch[src_mask]
        ref_pixels = ref_ch[ref_mask]

        if len(src_pixels) == 0 or len(ref_pixels) == 0:
            continue

        src_mean = np.mean(src_pixels)
        src_std = np.std(src_pixels)
        ref_mean = np.mean(ref_pixels)
        ref_std = np.std(ref_pixels)

        if src_std < 1e-6:
            src_std = 1e-6
        if ref_std < 1e-6:
            continue

        # Compute corrected values
        corrected = (src_ch - src_mean) * (ref_std / src_std) + ref_mean

        # Blend with original using strength factor (only on opaque pixels)
        blended = src_ch.copy()
        blended[src_mask] = src_ch[src_mask] * (1 - strength) + corrected[src_mask] * strength
        src_lab[:, :, ch] = blended

    # Clamp to valid range
    src_lab = np.clip(src_lab, 0, 255).astype(np.uint8)

    # Convert back to RGB
    result_rgb = cv2.cvtColor(src_lab, cv2.COLOR_LAB2RGB)

    # Only update RGB for opaque pixels, leave transparent pixels as-is
    if src_alpha is not None:
        result_rgba = src_rgba.copy()
        result_rgba[src_mask, :3] = result_rgb[src_mask]
        return Image.fromarray(result_rgba, "RGBA")
    else:
        return Image.fromarray(result_rgb, "RGB")
