"""Pytest fixtures for backend tests."""

import io
from unittest.mock import MagicMock, patch

import numpy as np
import pytest
from httpx import ASGITransport, AsyncClient
from PIL import Image

from app.main import app
from app.services.cache import SegmentedOutput, segmentation_cache


@pytest.fixture(autouse=True)
def clear_cache():
    """Clear the segmentation cache before each test."""
    segmentation_cache.clear()
    yield
    segmentation_cache.clear()


@pytest.fixture
def client():
    """Synchronous test client."""
    from starlette.testclient import TestClient
    return TestClient(app)


@pytest.fixture
async def async_client():
    """Async test client using httpx."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


def _create_test_image(
    width: int = 300,
    height: int = 400,
    color: tuple = (100, 150, 200),
    fmt: str = "JPEG",
    with_person: bool = True,
) -> bytes:
    """Create a test image as bytes."""
    img = Image.new("RGB", (width, height), color)
    if with_person:
        # Draw a simple "person" shape (white rectangle in center)
        pixels = np.array(img)
        cx, cy = width // 2, height // 2
        pw, ph = width // 4, height // 2
        pixels[cy - ph // 2 : cy + ph // 2, cx - pw // 2 : cx + pw // 2] = [255, 255, 255]
        img = Image.fromarray(pixels)
    buf = io.BytesIO()
    img.save(buf, format=fmt)
    buf.seek(0)
    return buf.getvalue()


@pytest.fixture
def sample_jpeg_image() -> bytes:
    """300x400 test JPEG image."""
    return _create_test_image(300, 400, fmt="JPEG")


@pytest.fixture
def sample_png_image() -> bytes:
    """300x400 test PNG image."""
    return _create_test_image(300, 400, fmt="PNG")


@pytest.fixture
def sample_webp_image() -> bytes:
    """300x400 test WebP image."""
    return _create_test_image(300, 400, fmt="WEBP")


@pytest.fixture
def large_image() -> bytes:
    """5000x3000 test image for resize validation."""
    return _create_test_image(5000, 3000, fmt="JPEG")


@pytest.fixture
def oversized_file() -> bytes:
    """21MB dummy file for size validation."""
    return b"\xff\xd8" + b"\x00" * (21 * 1024 * 1024)


@pytest.fixture
def non_image_file() -> bytes:
    """Text file for format validation."""
    return b"This is not an image file."


@pytest.fixture
def pdf_file() -> bytes:
    """PDF-like file."""
    return b"%PDF-1.4 fake pdf content" + b"\x00" * 100


def create_mock_segmented_output(
    width: int = 300,
    height: int = 400,
    color: tuple = (100, 150, 200),
    bbox: tuple = (50, 20, 200, 360),
) -> SegmentedOutput:
    """Create a mock SegmentedOutput for testing."""
    img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    pixels = np.array(img)
    x, y, w, h = bbox
    pixels[y : y + h, x : x + w, :3] = color
    pixels[y : y + h, x : x + w, 3] = 255
    img = Image.fromarray(pixels, "RGBA")

    return SegmentedOutput(
        image=img,
        bbox=bbox,
        foot_y=y + h,
        original_size=(width, height),
    )


@pytest.fixture
def segmented_pair() -> tuple[str, str]:
    """Create two segmented images in the cache and return their IDs."""
    seg1 = create_mock_segmented_output(
        width=300, height=400, color=(100, 150, 200), bbox=(50, 20, 200, 360)
    )
    seg2 = create_mock_segmented_output(
        width=300, height=400, color=(200, 100, 150), bbox=(60, 30, 180, 340)
    )
    id1 = "seg_test0001"
    id2 = "seg_test0002"
    segmentation_cache.put(id1, seg1)
    segmentation_cache.put(id2, seg2)
    return id1, id2


# Mock rembg for tests
@pytest.fixture(autouse=True)
def mock_rembg():
    """Mock rembg to avoid downloading the model in tests."""
    def mock_remove(image, **kwargs):
        """Return a mock segmented image with alpha channel."""
        width, height = image.size
        result = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        pixels = np.array(result)
        # Create a "person" area in center
        cx, cy = width // 2, height // 2
        pw, ph = width // 3, int(height * 0.7)
        y_start = max(0, cy - ph // 2)
        y_end = min(height, cy + ph // 2)
        x_start = max(0, cx - pw // 2)
        x_end = min(width, cx + pw // 2)
        # Copy RGB from input
        input_pixels = np.array(image.convert("RGBA"))
        pixels[y_start:y_end, x_start:x_end, :3] = input_pixels[y_start:y_end, x_start:x_end, :3]
        pixels[y_start:y_end, x_start:x_end, 3] = 255
        return Image.fromarray(pixels, "RGBA")

    with patch("app.services.segmentation.remove", mock_remove):
        with patch("app.services.segmentation._rembg_loaded", True):
            with patch("app.services.segmentation._rembg_session", None):
                yield
