"""Image utility functions."""

import base64
import io
from typing import Optional

import numpy as np
from PIL import Image, ImageOps

# Maximum dimension for input images
MAX_DIMENSION = 4000

# Supported content types
SUPPORTED_CONTENT_TYPES = {
    "image/jpeg",
    "image/png",
    "image/webp",
    "image/heic",
    "image/heif",
}

# Magic bytes for image format verification
MAGIC_BYTES = {
    b"\xff\xd8": "image/jpeg",  # JPEG
    b"\x89PNG": "image/png",  # PNG (first 4 bytes: 89 50 4E 47)
    b"RIFF": "image/webp",  # WebP (starts with RIFF)
}

# Maximum file size in bytes (20MB)
MAX_FILE_SIZE = 20 * 1024 * 1024


def validate_magic_bytes(data: bytes) -> bool:
    """Validate image format using magic bytes."""
    if len(data) < 4:
        return False
    # JPEG
    if data[:2] == b"\xff\xd8":
        return True
    # PNG
    if data[:4] == b"\x89PNG":
        return True
    # WebP (RIFF....WEBP)
    if data[:4] == b"RIFF" and len(data) >= 12 and data[8:12] == b"WEBP":
        return True
    return False


def resize_if_needed(image: Image.Image) -> tuple[Image.Image, bool]:
    """Resize image if longest side exceeds MAX_DIMENSION. Returns (image, was_resized)."""
    width, height = image.size
    max_side = max(width, height)
    if max_side <= MAX_DIMENSION:
        return image, False
    ratio = MAX_DIMENSION / max_side
    new_width = int(width * ratio)
    new_height = int(height * ratio)
    resized = image.resize((new_width, new_height), Image.LANCZOS)
    return resized, True


def decode_image(data: bytes) -> Image.Image:
    """Decode image bytes to PIL Image with EXIF rotation correction."""
    image = Image.open(io.BytesIO(data))
    image = ImageOps.exif_transpose(image)
    if image.mode not in ("RGB", "RGBA"):
        image = image.convert("RGB")
    return image


def image_to_base64(image: Image.Image, fmt: str = "PNG", quality: int = 70) -> str:
    """Convert PIL Image to base64 data URI string."""
    buffer = io.BytesIO()
    if fmt.upper() == "JPEG":
        # JPEG doesn't support alpha
        if image.mode == "RGBA":
            image = image.convert("RGB")
        image.save(buffer, format="JPEG", quality=quality)
        mime = "image/jpeg"
    else:
        image.save(buffer, format="PNG")
        mime = "image/png"
    encoded = base64.b64encode(buffer.getvalue()).decode("utf-8")
    return f"data:{mime};base64,{encoded}"


def compute_bbox(alpha: np.ndarray) -> Optional[tuple[int, int, int, int]]:
    """Compute bounding box from alpha channel.
    Returns (x, y, width, height) or None if no foreground.
    """
    rows = np.any(alpha > 10, axis=1)
    cols = np.any(alpha > 10, axis=0)
    if not rows.any() or not cols.any():
        return None
    y_min, y_max = np.where(rows)[0][[0, -1]]
    x_min, x_max = np.where(cols)[0][[0, -1]]
    return (int(x_min), int(y_min), int(x_max - x_min + 1), int(y_max - y_min + 1))
