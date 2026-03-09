"""Tests for color correction service."""

import numpy as np
import pytest
from PIL import Image

from app.services.color_correction import match_color


class TestMatchColor:
    """Tests for match_color function."""

    def test_same_image_no_change(self):
        """Matching an image to itself produces similar result."""
        img = Image.new("RGBA", (50, 50), (100, 150, 200, 255))
        result = match_color(img, img)
        assert result.size == img.size
        assert result.mode == "RGBA"

    def test_preserves_alpha_channel(self):
        """Alpha channel is preserved after color correction."""
        src = Image.new("RGBA", (50, 50), (100, 100, 100, 128))
        ref = Image.new("RGBA", (50, 50), (200, 200, 200, 255))
        result = match_color(src, ref)
        result_arr = np.array(result)
        np.testing.assert_array_equal(result_arr[:, :, 3], 128)

    def test_output_is_rgba(self):
        """Output mode is RGBA."""
        src = Image.new("RGBA", (50, 50), (100, 100, 100, 255))
        ref = Image.new("RGBA", (50, 50), (200, 100, 100, 255))
        result = match_color(src, ref)
        assert result.mode == "RGBA"

    def test_output_size_matches_source(self):
        """Output size matches source size."""
        src = Image.new("RGBA", (60, 40), (100, 100, 100, 255))
        ref = Image.new("RGBA", (80, 80), (200, 100, 100, 255))
        result = match_color(src, ref)
        assert result.size == (60, 40)

    def test_different_sized_images(self):
        """Works with different sized source and reference."""
        src = Image.new("RGBA", (30, 30), (100, 100, 100, 255))
        ref = Image.new("RGBA", (100, 100), (200, 50, 50, 255))
        result = match_color(src, ref)
        assert result.size == (30, 30)

    def test_transparent_source_handled(self):
        """Fully transparent source is handled gracefully."""
        src = Image.new("RGBA", (50, 50), (100, 100, 100, 0))
        ref = Image.new("RGBA", (50, 50), (200, 200, 200, 255))
        result = match_color(src, ref)
        assert result.mode == "RGBA"
        assert result.size == (50, 50)

    def test_pixel_values_in_valid_range(self):
        """Output pixel values are in 0-255 range."""
        # Create images with extreme color differences
        src = Image.new("RGBA", (50, 50), (10, 10, 10, 255))
        ref = Image.new("RGBA", (50, 50), (245, 245, 245, 255))
        result = match_color(src, ref)
        result_arr = np.array(result)
        assert result_arr.min() >= 0
        assert result_arr.max() <= 255
