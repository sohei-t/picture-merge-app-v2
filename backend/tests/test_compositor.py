"""Tests for compositor (merge pipeline) service."""

import numpy as np
import pytest
from PIL import Image

from app.models.schemas import MergeSettingsModel
from app.services.cache import SegmentedOutput
from app.services.compositor import (
    _compute_auto_scale,
    _crop_to_bbox,
    _hex_to_rgb,
    _paste_with_alpha,
    merge_images,
)


def _make_seg_output(
    width=300, height=400, color=(100, 150, 200), bbox=(50, 20, 200, 360)
) -> SegmentedOutput:
    """Create a SegmentedOutput for testing."""
    img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    pixels = np.array(img)
    x, y, w, h = bbox
    pixels[y : y + h, x : x + w, :3] = color
    pixels[y : y + h, x : x + w, 3] = 255
    img = Image.fromarray(pixels, "RGBA")
    return SegmentedOutput(
        image=img, bbox=bbox, foot_y=y + h, original_size=(width, height)
    )


class TestCropToBbox:
    """Tests for _crop_to_bbox."""

    def test_crop_size(self):
        """Crop matches bbox dimensions."""
        seg = _make_seg_output(bbox=(10, 20, 50, 60))
        cropped, foot_rel = _crop_to_bbox(seg)
        assert cropped.size == (50, 60)

    def test_foot_y_relative(self):
        """foot_y_relative = foot_y - bbox_y."""
        seg = _make_seg_output(bbox=(10, 20, 50, 60))
        _, foot_rel = _crop_to_bbox(seg)
        assert foot_rel == seg.foot_y - 20


class TestComputeAutoScale:
    """Tests for _compute_auto_scale."""

    def test_equal_heights(self):
        """Equal heights return 1.0."""
        assert _compute_auto_scale(200, 200) == 1.0

    def test_clamp_low(self):
        """Ratio below 0.8 is clamped to 0.8."""
        # person1=100, person2=200 → ratio=0.5 → clamped to 0.8
        assert _compute_auto_scale(100, 200) == 0.8

    def test_clamp_high(self):
        """Ratio above 1.2 is clamped to 1.2."""
        # person1=300, person2=100 → ratio=3.0 → clamped to 1.2
        assert _compute_auto_scale(300, 100) == 1.2

    def test_within_range(self):
        """Ratio in valid range is returned as-is."""
        result = _compute_auto_scale(200, 200)
        assert 0.8 <= result <= 1.2

    def test_zero_person2(self):
        """Zero person2 height returns 1.0."""
        assert _compute_auto_scale(200, 0) == 1.0


class TestHexToRgb:
    """Tests for _hex_to_rgb."""

    def test_white(self):
        assert _hex_to_rgb("#FFFFFF") == (255, 255, 255)

    def test_black(self):
        assert _hex_to_rgb("#000000") == (0, 0, 0)

    def test_red(self):
        assert _hex_to_rgb("#FF0000") == (255, 0, 0)

    def test_without_hash(self):
        assert _hex_to_rgb("00FF00") == (0, 255, 0)

    def test_lowercase(self):
        assert _hex_to_rgb("#ff8800") == (255, 136, 0)


class TestPasteWithAlpha:
    """Tests for _paste_with_alpha."""

    def test_basic_paste(self):
        """Paste within bounds."""
        canvas = Image.new("RGBA", (100, 100), (255, 255, 255, 255))
        overlay = Image.new("RGBA", (20, 20), (255, 0, 0, 255))
        result = _paste_with_alpha(canvas, overlay, 10, 10)
        pixel = result.getpixel((15, 15))
        assert pixel[0] == 255  # red from overlay
        assert pixel[3] == 255

    def test_negative_position(self):
        """Overlay partially off-screen (negative x/y) is handled."""
        canvas = Image.new("RGBA", (100, 100), (255, 255, 255, 255))
        overlay = Image.new("RGBA", (50, 50), (255, 0, 0, 128))
        result = _paste_with_alpha(canvas, overlay, -25, -25)
        assert result.size == (100, 100)

    def test_fully_offscreen(self):
        """Overlay fully off-screen returns canvas unchanged."""
        canvas = Image.new("RGBA", (100, 100), (255, 255, 255, 255))
        overlay = Image.new("RGBA", (20, 20), (255, 0, 0, 255))
        result = _paste_with_alpha(canvas, overlay, -100, -100)
        # Canvas should be unchanged
        assert np.array_equal(np.array(result), np.array(canvas))


class TestMergeImages:
    """Tests for merge_images."""

    def test_default_settings(self):
        """Merge with default settings returns valid output."""
        seg1 = _make_seg_output()
        seg2 = _make_seg_output(color=(200, 100, 150))
        settings = MergeSettingsModel()
        base64_img, time_ms, (w, h) = merge_images(seg1, seg2, settings)
        assert base64_img.startswith("data:image/png;base64,")
        assert time_ms >= 0
        assert w == 2048
        assert h == 2048

    def test_preview_mode(self):
        """Preview mode returns 512x512 JPEG."""
        seg1 = _make_seg_output()
        seg2 = _make_seg_output(color=(200, 100, 150))
        settings = MergeSettingsModel()
        base64_img, time_ms, (w, h) = merge_images(
            seg1, seg2, settings, preview_mode=True
        )
        assert base64_img.startswith("data:image/jpeg;base64,")
        assert w == 768
        assert h == 768

    def test_custom_size(self):
        """Custom output size is respected."""
        seg1 = _make_seg_output()
        seg2 = _make_seg_output(color=(200, 100, 150))
        settings = MergeSettingsModel(output_width=800, output_height=600)
        _, _, (w, h) = merge_images(seg1, seg2, settings)
        assert w == 800
        assert h == 600

    def test_shadow_enabled(self):
        """Merge with shadow enabled produces valid output."""
        seg1 = _make_seg_output()
        seg2 = _make_seg_output(color=(200, 100, 150))
        settings = MergeSettingsModel(
            shadow={"enabled": True, "intensity": 0.8}
        )
        base64_img, _, _ = merge_images(seg1, seg2, settings)
        assert base64_img.startswith("data:image/png;base64,")

    def test_color_correction_enabled(self):
        """Merge with color correction enabled produces valid output."""
        seg1 = _make_seg_output()
        seg2 = _make_seg_output(color=(200, 100, 150))
        settings = MergeSettingsModel(color_correction=True)
        base64_img, _, _ = merge_images(seg1, seg2, settings)
        assert base64_img.startswith("data:image/png;base64,")

    def test_background_color(self):
        """Background color is applied."""
        seg1 = _make_seg_output()
        seg2 = _make_seg_output(color=(200, 100, 150))
        settings = MergeSettingsModel(background_color="#FF0000")
        base64_img, _, _ = merge_images(seg1, seg2, settings)
        # Decode and check corner pixel
        import base64
        import io

        b64 = base64_img.split(",", 1)[1]
        img_bytes = base64.b64decode(b64)
        img = Image.open(io.BytesIO(img_bytes))
        pixel = img.getpixel((0, 0))
        assert pixel[0] > 200  # Red channel high
