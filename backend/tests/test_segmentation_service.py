"""Tests for segmentation service."""

import io
from unittest.mock import patch, MagicMock

import numpy as np
import pytest
from PIL import Image

from app.services.segmentation import (
    is_rembg_loaded,
    preload_rembg,
    segment_image,
)
from app.services.cache import segmentation_cache


@pytest.fixture(autouse=True)
def _clear_cache():
    """Clear cache before/after each test."""
    segmentation_cache.clear()
    yield
    segmentation_cache.clear()


def _create_mock_remove():
    """Create a mock rembg.remove function that returns a person-shaped alpha."""
    def mock_remove(image, **kwargs):
        width, height = image.size
        result = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        pixels = np.array(result)
        cx, cy = width // 2, height // 2
        pw, ph = width // 3, int(height * 0.7)
        y_start = max(0, cy - ph // 2)
        y_end = min(height, cy + ph // 2)
        x_start = max(0, cx - pw // 2)
        x_end = min(width, cx + pw // 2)
        input_pixels = np.array(image.convert("RGBA"))
        pixels[y_start:y_end, x_start:x_end, :3] = input_pixels[
            y_start:y_end, x_start:x_end, :3
        ]
        pixels[y_start:y_end, x_start:x_end, 3] = 255
        return Image.fromarray(pixels, "RGBA")
    return mock_remove


class TestIsRembgLoaded:
    """Tests for is_rembg_loaded."""

    def test_returns_bool(self):
        """is_rembg_loaded returns a boolean."""
        with patch("app.services.segmentation._rembg_loaded", True):
            assert is_rembg_loaded() is True
        with patch("app.services.segmentation._rembg_loaded", False):
            assert is_rembg_loaded() is False


class TestSegmentImage:
    """Tests for segment_image."""

    def test_returns_id_and_output(self):
        """Returns a valid seg_id and SegmentedOutput."""
        image = Image.new("RGB", (300, 400), (100, 150, 200))
        mock_remove = _create_mock_remove()
        with patch("app.services.segmentation.remove", mock_remove):
            with patch("app.services.segmentation._rembg_loaded", True):
                with patch("app.services.segmentation._rembg_session", None):
                    seg_id, output = segment_image(image, (300, 400))
        assert seg_id.startswith("seg_")
        assert len(seg_id) == 12  # seg_ + 8 hex chars
        assert output.image.mode == "RGBA"
        assert output.original_size == (300, 400)

    def test_stores_in_cache(self):
        """Result is stored in cache."""
        image = Image.new("RGB", (300, 400), (100, 150, 200))
        mock_remove = _create_mock_remove()
        with patch("app.services.segmentation.remove", mock_remove):
            with patch("app.services.segmentation._rembg_loaded", True):
                with patch("app.services.segmentation._rembg_session", None):
                    seg_id, _ = segment_image(image, (300, 400))
        assert segmentation_cache.get(seg_id) is not None

    def test_bbox_valid(self):
        """BBox values are valid."""
        image = Image.new("RGB", (300, 400), (100, 150, 200))
        mock_remove = _create_mock_remove()
        with patch("app.services.segmentation.remove", mock_remove):
            with patch("app.services.segmentation._rembg_loaded", True):
                with patch("app.services.segmentation._rembg_session", None):
                    _, output = segment_image(image, (300, 400))
        x, y, w, h = output.bbox
        assert x >= 0
        assert y >= 0
        assert w > 0
        assert h > 0

    def test_foot_y_equals_bbox_y_plus_h(self):
        """foot_y equals bbox.y + bbox.height."""
        image = Image.new("RGB", (300, 400), (100, 150, 200))
        mock_remove = _create_mock_remove()
        with patch("app.services.segmentation.remove", mock_remove):
            with patch("app.services.segmentation._rembg_loaded", True):
                with patch("app.services.segmentation._rembg_session", None):
                    _, output = segment_image(image, (300, 400))
        assert output.foot_y == output.bbox[1] + output.bbox[3]

    def test_no_foreground_raises_value_error(self):
        """All-transparent result raises ValueError."""
        image = Image.new("RGB", (300, 400), (100, 150, 200))

        def mock_remove_transparent(image, **kwargs):
            return Image.new("RGBA", image.size, (0, 0, 0, 0))

        with patch("app.services.segmentation.remove", mock_remove_transparent):
            with patch("app.services.segmentation._rembg_loaded", True):
                with patch("app.services.segmentation._rembg_session", None):
                    with pytest.raises(ValueError, match="No foreground"):
                        segment_image(image, (300, 400))

    def test_unique_ids(self):
        """Each call generates a unique ID."""
        image = Image.new("RGB", (300, 400), (100, 150, 200))
        mock_remove = _create_mock_remove()
        ids = []
        with patch("app.services.segmentation.remove", mock_remove):
            with patch("app.services.segmentation._rembg_loaded", True):
                with patch("app.services.segmentation._rembg_session", None):
                    for _ in range(5):
                        seg_id, _ = segment_image(image, (300, 400))
                        ids.append(seg_id)
        assert len(set(ids)) == 5
