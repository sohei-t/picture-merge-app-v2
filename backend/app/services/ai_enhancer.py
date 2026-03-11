"""AI-powered image enhancement using GFPGAN + OpenCV body enhancement.

Pipeline:
  1. GFPGAN — face detection & restoration (AI model)
  2. OpenCV — full-body enhancement (denoising, CLAHE, sharpening)

Both run on local hardware.  GFPGAN handles faces while OpenCV
enhances the rest of the body (hair, skin, clothes) for an
overall sharper and cleaner result.
"""

from __future__ import annotations

import logging
import os
import time
from pathlib import Path

import cv2
import numpy as np
import torch
from PIL import Image

logger = logging.getLogger(__name__)

# Model weights directory
WEIGHTS_DIR = Path(__file__).parent.parent.parent / "weights"

# Lazy-loaded singleton
_face_enhancer = None

# Max dimension for processing (resize down if larger, restore after)
MAX_PROCESS_DIM = 1024


def _get_device() -> torch.device:
    """Get the best available device (MPS for Apple Silicon, else CPU)."""
    if torch.backends.mps.is_available():
        return torch.device("mps")
    return torch.device("cpu")


def _ensure_weights_dir() -> None:
    """Create weights directory if it doesn't exist."""
    WEIGHTS_DIR.mkdir(parents=True, exist_ok=True)


def _get_face_enhancer():
    """Lazy-load GFPGAN face enhancer (singleton).

    Uses upscale=1 and no background upsampler so it only
    restores face quality without resizing the whole image.
    """
    global _face_enhancer
    if _face_enhancer is not None:
        return _face_enhancer

    from gfpgan import GFPGANer

    _ensure_weights_dir()
    device = _get_device()
    logger.info(f"Loading GFPGAN on device: {device}")

    model_path = str(WEIGHTS_DIR / "GFPGANv1.3.pth")
    if not os.path.exists(model_path):
        model_path = (
            "https://github.com/TencentARC/GFPGAN/releases/"
            "download/v1.3.0/GFPGANv1.3.pth"
        )

    _face_enhancer = GFPGANer(
        model_path=model_path,
        upscale=1,           # Keep original resolution
        arch="clean",
        channel_multiplier=2,
        bg_upsampler=None,   # No heavy Real-ESRGAN upscaler
        device=device,
    )
    logger.info("GFPGAN loaded successfully")
    return _face_enhancer


def _enhance_body(image: Image.Image, alpha: Image.Image | None) -> Image.Image:
    """Enhance the full body using OpenCV (fast, no AI model needed).

    Steps:
      1. Denoise with fastNlMeansDenoisingColored (edge-preserving)
      2. CLAHE on L channel for local contrast boost
      3. Unsharp mask sharpening

    Only processes foreground pixels (where alpha > 0) to avoid
    amplifying noise in transparent areas.
    """
    arr = np.array(image)

    # Build foreground mask from alpha channel
    if alpha is not None:
        mask = np.array(alpha) > 0
    else:
        mask = np.ones(arr.shape[:2], dtype=bool)

    # 1. Denoise (preserve edges, remove grain)
    # Use positional args for OpenCV compatibility (4.13+ changed kwarg names)
    denoised = cv2.fastNlMeansDenoisingColored(arr, None, 6, 6, 7, 21)

    # 2. CLAHE on L channel (local contrast enhancement)
    lab = cv2.cvtColor(denoised, cv2.COLOR_RGB2LAB)
    l_ch, a_ch, b_ch = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=1.5, tileGridSize=(8, 8))
    l_ch = clahe.apply(l_ch)
    enhanced = cv2.merge([l_ch, a_ch, b_ch])
    enhanced = cv2.cvtColor(enhanced, cv2.COLOR_LAB2RGB)

    # 3. Unsharp mask sharpening
    blurred = cv2.GaussianBlur(enhanced, (0, 0), sigmaX=1.0)
    sharpened = cv2.addWeighted(enhanced, 1.4, blurred, -0.4, 0)
    sharpened = np.clip(sharpened, 0, 255).astype(np.uint8)

    # Apply only to foreground pixels
    result = arr.copy()
    result[mask] = sharpened[mask]

    return Image.fromarray(result, "RGB")


def ai_enhance(image: Image.Image) -> tuple[Image.Image, dict]:
    """Apply AI face restoration + full-body enhancement.

    Pipeline:
    1. Extract RGB and alpha channel
    2. Resize down if too large (for speed)
    3. Run GFPGAN (face detection + restoration, paste back)
    4. Resize back to original dimensions if needed
    5. Full-body enhancement (denoise, CLAHE contrast, sharpening)
    6. Restore alpha channel

    Args:
        image: RGBA PIL Image (segmented person)

    Returns:
        Tuple of (enhanced RGBA image, info dict with timing/details)
    """
    start = time.time()
    info = {"method": "gfpgan+body", "scale": 1}

    orig_w, orig_h = image.size

    # Extract channels
    rgba = np.array(image)
    has_alpha = rgba.shape[2] == 4
    if has_alpha:
        alpha_pil = Image.fromarray(rgba[:, :, 3])
        rgb_arr = rgba[:, :, :3]
    else:
        alpha_pil = None
        rgb_arr = rgba[:, :, :3]

    # Resize down for processing speed if image is large
    max_side = max(orig_w, orig_h)
    if max_side > MAX_PROCESS_DIM:
        scale_down = MAX_PROCESS_DIM / max_side
        proc_w = int(orig_w * scale_down)
        proc_h = int(orig_h * scale_down)
        rgb_pil = Image.fromarray(rgb_arr, "RGB").resize(
            (proc_w, proc_h), Image.LANCZOS
        )
        rgb_bgr = cv2.cvtColor(np.array(rgb_pil), cv2.COLOR_RGB2BGR)
        was_resized = True
    else:
        rgb_bgr = cv2.cvtColor(rgb_arr, cv2.COLOR_RGB2BGR)
        was_resized = False

    # Run GFPGAN
    face_enhancer = _get_face_enhancer()
    try:
        _, _, output = face_enhancer.enhance(
            rgb_bgr,
            has_aligned=False,
            only_center_face=False,
            paste_back=True,
        )
    except RuntimeError as e:
        logger.warning(f"GFPGAN failed ({e}), applying fallback enhancement")
        # Fallback: just sharpen with OpenCV
        output = rgb_bgr.copy()
        blurred = cv2.GaussianBlur(output, (0, 0), sigmaX=1.5)
        output = cv2.addWeighted(output, 1.5, blurred, -0.5, 0)
        output = np.clip(output, 0, 255).astype(np.uint8)
        info["method"] = "sharpen-fallback"

    # Convert back to RGB
    output_rgb = cv2.cvtColor(output, cv2.COLOR_BGR2RGB)

    # Resize back to original if we resized down
    if was_resized:
        result = Image.fromarray(output_rgb, "RGB").resize(
            (orig_w, orig_h), Image.LANCZOS
        )
    else:
        result = Image.fromarray(output_rgb, "RGB")

    # --- Full-body enhancement (OpenCV) ---
    result = _enhance_body(result, alpha_pil)

    # Restore alpha channel
    if has_alpha and alpha_pil is not None:
        result = result.convert("RGBA")
        result.putalpha(alpha_pil)

    elapsed = time.time() - start
    info["processing_time_ms"] = int(elapsed * 1000)
    info["output_size"] = {"width": result.width, "height": result.height}
    logger.info(
        f"AI enhancement complete: {image.size} → {result.size} "
        f"in {info['processing_time_ms']}ms ({info['method']})"
    )
    return result, info
