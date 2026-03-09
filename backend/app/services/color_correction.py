"""Color correction using LAB color space histogram matching."""

import cv2
import numpy as np
from PIL import Image


def match_color(source: Image.Image, reference: Image.Image) -> Image.Image:
    """Match the color of source image to reference image using LAB color space.

    Args:
        source: Image to be corrected (RGBA)
        reference: Reference image for color matching (RGBA)

    Returns:
        Color-corrected source image (RGBA, alpha preserved)
    """
    # Extract RGB channels (ignore alpha for color matching)
    src_rgba = np.array(source)
    ref_rgba = np.array(reference)

    # Preserve alpha channel
    src_alpha = src_rgba[:, :, 3].copy() if src_rgba.shape[2] == 4 else None

    # Get RGB portions only where alpha > 0 for stats, but process all pixels
    src_rgb = src_rgba[:, :, :3]
    ref_rgb = ref_rgba[:, :, :3]

    # Convert to LAB color space
    src_lab = cv2.cvtColor(src_rgb, cv2.COLOR_RGB2LAB).astype(np.float64)
    ref_lab = cv2.cvtColor(ref_rgb, cv2.COLOR_RGB2LAB).astype(np.float64)

    # Create masks for non-transparent pixels
    src_mask = src_alpha > 10 if src_alpha is not None else np.ones(src_lab.shape[:2], dtype=bool)
    ref_mask = ref_rgba[:, :, 3] > 10 if ref_rgba.shape[2] == 4 else np.ones(ref_lab.shape[:2], dtype=bool)

    # Match each LAB channel
    for ch in range(3):
        src_ch = src_lab[:, :, ch]
        ref_ch = ref_lab[:, :, ch]

        # Compute stats only on non-transparent pixels
        src_pixels = src_ch[src_mask]
        ref_pixels = ref_ch[ref_mask]

        if len(src_pixels) == 0 or len(ref_pixels) == 0:
            continue

        src_mean = np.mean(src_pixels)
        src_std = np.std(src_pixels)
        ref_mean = np.mean(ref_pixels)
        ref_std = np.std(ref_pixels)

        # Avoid division by zero
        if src_std < 1e-6:
            src_std = 1e-6

        # Normalize and transfer
        src_lab[:, :, ch] = (src_ch - src_mean) * (ref_std / src_std) + ref_mean

    # Clamp to valid range
    src_lab = np.clip(src_lab, 0, 255).astype(np.uint8)

    # Convert back to RGB
    result_rgb = cv2.cvtColor(src_lab, cv2.COLOR_LAB2RGB)

    # Reconstruct RGBA
    if src_alpha is not None:
        result_rgba = np.dstack([result_rgb, src_alpha])
    else:
        result_rgba = result_rgb

    return Image.fromarray(result_rgba, "RGBA" if src_alpha is not None else "RGB")
