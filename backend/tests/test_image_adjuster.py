"""Tests for manual image adjustment service."""

import numpy as np
import pytest
from PIL import Image

from app.services.image_adjuster import adjust_image


def _make_test_image(width=200, height=200):
    """Create a test RGBA image with colored foreground."""
    rgba = np.zeros((height, width, 4), dtype=np.uint8)
    # Foreground with some color
    rgba[30:170, 30:170, 0] = 180  # R
    rgba[30:170, 30:170, 1] = 120  # G
    rgba[30:170, 30:170, 2] = 80   # B
    rgba[30:170, 30:170, 3] = 255  # A
    return Image.fromarray(rgba, "RGBA")


class TestAdjustImage:
    """Tests for adjust_image()."""

    def test_no_change_returns_similar(self):
        image = _make_test_image()
        result = adjust_image(image)
        assert result.size == image.size
        assert result.mode == "RGBA"
        # Should be identical when no adjustments
        np.testing.assert_array_equal(np.array(result), np.array(image))

    def test_brightness_increase(self):
        image = _make_test_image()
        result = adjust_image(image, brightness=0.5)
        orig_rgb = np.array(image)[:, :, :3].mean()
        result_rgb = np.array(result)[:, :, :3].mean()
        assert result_rgb > orig_rgb

    def test_brightness_decrease(self):
        image = _make_test_image()
        result = adjust_image(image, brightness=-0.5)
        orig_rgb = np.array(image)[:, :, :3].mean()
        result_rgb = np.array(result)[:, :, :3].mean()
        assert result_rgb < orig_rgb

    def test_contrast_change(self):
        image = _make_test_image()
        result = adjust_image(image, contrast=0.5)
        assert result.size == image.size
        assert result.mode == "RGBA"
        # Should be different from original
        assert not np.array_equal(np.array(result)[:, :, :3], np.array(image)[:, :, :3])

    def test_saturation_increase(self):
        image = _make_test_image()
        result = adjust_image(image, saturation=0.5)
        assert result.size == image.size
        assert not np.array_equal(np.array(result)[:, :, :3], np.array(image)[:, :, :3])

    def test_temperature_warm(self):
        image = _make_test_image()
        result = adjust_image(image, temperature=0.5)
        assert result.size == image.size
        assert not np.array_equal(np.array(result)[:, :, :3], np.array(image)[:, :, :3])

    def test_temperature_cool(self):
        image = _make_test_image()
        result = adjust_image(image, temperature=-0.5)
        assert result.size == image.size

    def test_sharpness_change(self):
        image = _make_test_image()
        result = adjust_image(image, sharpness=0.5)
        assert result.size == image.size

    def test_preserves_alpha_channel(self):
        image = _make_test_image()
        result = adjust_image(image, brightness=0.5, contrast=0.3, saturation=0.2)
        orig_alpha = np.array(image)[:, :, 3]
        result_alpha = np.array(result)[:, :, 3]
        np.testing.assert_array_equal(orig_alpha, result_alpha)

    def test_combined_adjustments(self):
        image = _make_test_image()
        result = adjust_image(
            image,
            brightness=0.2,
            contrast=0.3,
            saturation=-0.1,
            temperature=0.2,
            sharpness=0.4,
        )
        assert result.size == image.size
        assert result.mode == "RGBA"

    def test_extreme_values(self):
        image = _make_test_image()
        result = adjust_image(
            image,
            brightness=1.0,
            contrast=1.0,
            saturation=1.0,
            temperature=1.0,
            sharpness=1.0,
        )
        assert result.size == image.size
        # Should not crash even with extreme values

    def test_rgb_input(self):
        rgba = _make_test_image()
        rgb = rgba.convert("RGB")
        result = adjust_image(rgb, brightness=0.3)
        assert result.mode == "RGB"
        assert result.size == rgb.size
