"""AI-powered image enhancement using GFPGAN + Real-ESRGAN.

Pipeline:
  1. Real-ESRGAN — full-body AI super-resolution (2x on small input)
  2. GFPGAN — face detection & restoration (paste back onto enhanced image)

Both run on local hardware.  Images are resized down to ~512px before
Real-ESRGAN 2x processing, keeping output at ~1024px for fast execution
(5-15 seconds on Apple Silicon MPS, 10-30 seconds on CPU).
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

# Lazy-loaded singletons
_face_enhancer = None
_bg_upsampler = None

# Max dimension BEFORE Real-ESRGAN 2x (keeps output ~1024px)
MAX_INPUT_DIM = 512


def _get_device() -> torch.device:
    """Get the best available device (MPS for Apple Silicon, else CPU)."""
    if torch.backends.mps.is_available():
        return torch.device("mps")
    return torch.device("cpu")


def _ensure_weights_dir() -> None:
    """Create weights directory if it doesn't exist."""
    WEIGHTS_DIR.mkdir(parents=True, exist_ok=True)


def _get_bg_upsampler():
    """Lazy-load Real-ESRGAN 2x upsampler (singleton).

    Uses RealESRGAN_x2plus for 2x super-resolution.
    Input is pre-shrunk to ~512px so output is ~1024px.
    """
    global _bg_upsampler
    if _bg_upsampler is not None:
        return _bg_upsampler

    from basicsr.archs.rrdbnet_arch import RRDBNet
    from realesrgan import RealESRGANer

    _ensure_weights_dir()
    device = _get_device()

    model = RRDBNet(
        num_in_ch=3, num_out_ch=3, num_feat=64,
        num_block=23, num_grow_ch=32, scale=2,
    )

    model_path = str(WEIGHTS_DIR / "RealESRGAN_x2plus.pth")
    if not os.path.exists(model_path):
        model_path = (
            "https://github.com/xinntao/Real-ESRGAN/releases/"
            "download/v0.2.1/RealESRGAN_x2plus.pth"
        )

    # Use half precision on MPS/CUDA for speed, full on CPU
    use_half = device.type != "cpu"

    _bg_upsampler = RealESRGANer(
        scale=2,
        model_path=model_path,
        model=model,
        tile=0,        # No tiling needed for small images
        tile_pad=10,
        pre_pad=0,
        half=use_half,
        device=device,
    )
    logger.info(f"Real-ESRGAN x2 loaded on device: {device}")
    return _bg_upsampler


def _get_face_enhancer():
    """Lazy-load GFPGAN face enhancer (singleton).

    Uses the Real-ESRGAN bg_upsampler so both face and body
    are enhanced by AI models.
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

    bg_upsampler = _get_bg_upsampler()

    _face_enhancer = GFPGANer(
        model_path=model_path,
        upscale=2,              # 2x matches Real-ESRGAN scale
        arch="clean",
        channel_multiplier=2,
        bg_upsampler=bg_upsampler,
        device=device,
    )
    logger.info("GFPGAN + Real-ESRGAN loaded successfully")
    return _face_enhancer


def _enhance_body(image: Image.Image, alpha: Image.Image | None) -> Image.Image:
    """Enhance the full body using OpenCV (fast fallback).

    Used when Real-ESRGAN fails or is unavailable.
    """
    arr = np.array(image)

    if alpha is not None:
        mask = np.array(alpha) > 0
    else:
        mask = np.ones(arr.shape[:2], dtype=bool)

    # Denoise
    denoised = cv2.fastNlMeansDenoisingColored(arr, None, 6, 6, 7, 21)

    # CLAHE on L channel
    lab = cv2.cvtColor(denoised, cv2.COLOR_RGB2LAB)
    l_ch, a_ch, b_ch = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=1.5, tileGridSize=(8, 8))
    l_ch = clahe.apply(l_ch)
    enhanced = cv2.merge([l_ch, a_ch, b_ch])
    enhanced = cv2.cvtColor(enhanced, cv2.COLOR_LAB2RGB)

    # Unsharp mask
    blurred = cv2.GaussianBlur(enhanced, (0, 0), sigmaX=1.0)
    sharpened = cv2.addWeighted(enhanced, 1.4, blurred, -0.4, 0)
    sharpened = np.clip(sharpened, 0, 255).astype(np.uint8)

    result = arr.copy()
    result[mask] = sharpened[mask]
    return Image.fromarray(result, "RGB")


def ai_enhance(image: Image.Image) -> tuple[Image.Image, dict]:
    """Apply AI face + body enhancement to a segmented person image.

    Pipeline:
    1. Extract RGB and alpha channel
    2. Resize down to ~512px (so Real-ESRGAN 2x outputs ~1024px)
    3. Run GFPGAN with Real-ESRGAN bg_upsampler (face + body AI enhancement)
    4. Resize back to original dimensions
    5. Restore alpha channel

    Falls back to GFPGAN-only + OpenCV body enhancement if Real-ESRGAN fails.

    Args:
        image: RGBA PIL Image (segmented person)

    Returns:
        Tuple of (enhanced RGBA image, info dict with timing/details)
    """
    start = time.time()
    info = {"method": "gfpgan+realesrgan", "scale": 2}

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

    # Resize down to MAX_INPUT_DIM for Real-ESRGAN 2x processing
    max_side = max(orig_w, orig_h)
    if max_side > MAX_INPUT_DIM:
        scale_down = MAX_INPUT_DIM / max_side
        proc_w = int(orig_w * scale_down)
        proc_h = int(orig_h * scale_down)
        rgb_pil = Image.fromarray(rgb_arr, "RGB").resize(
            (proc_w, proc_h), Image.LANCZOS
        )
        rgb_bgr = cv2.cvtColor(np.array(rgb_pil), cv2.COLOR_RGB2BGR)
    else:
        rgb_bgr = cv2.cvtColor(rgb_arr, cv2.COLOR_RGB2BGR)

    # Run GFPGAN + Real-ESRGAN
    try:
        face_enhancer = _get_face_enhancer()
        _, _, output = face_enhancer.enhance(
            rgb_bgr,
            has_aligned=False,
            only_center_face=False,
            paste_back=True,
        )
    except RuntimeError as e:
        logger.warning(
            f"GFPGAN+Real-ESRGAN failed ({e}), falling back to OpenCV body enhancement"
        )
        # Fallback: resize to original and use OpenCV enhancement
        result = Image.fromarray(rgb_arr, "RGB")
        result = _enhance_body(result, alpha_pil)
        info["method"] = "opencv-fallback"
        info["scale"] = 1

        if has_alpha and alpha_pil is not None:
            result = result.convert("RGBA")
            result.putalpha(alpha_pil)

        elapsed = time.time() - start
        info["processing_time_ms"] = int(elapsed * 1000)
        info["output_size"] = {"width": result.width, "height": result.height}
        logger.info(
            f"AI enhancement (fallback): {image.size} → {result.size} "
            f"in {info['processing_time_ms']}ms ({info['method']})"
        )
        return result, info

    # Convert back to RGB
    output_rgb = cv2.cvtColor(output, cv2.COLOR_BGR2RGB)

    # Resize back to original dimensions
    result = Image.fromarray(output_rgb, "RGB").resize(
        (orig_w, orig_h), Image.LANCZOS
    )

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
