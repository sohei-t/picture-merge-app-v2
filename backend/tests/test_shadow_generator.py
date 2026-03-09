"""Tests for shadow generator service."""

import numpy as np
import pytest

from app.services.shadow_generator import generate_shadow


class TestGenerateShadow:
    """Tests for generate_shadow function."""

    def test_output_shape(self):
        """Output is RGBA array with correct dimensions."""
        result = generate_shadow(200, 200, 100, 160, 80, 0.5)
        assert result.shape == (200, 200, 4)
        assert result.dtype == np.uint8

    def test_zero_intensity_returns_empty(self):
        """Zero intensity produces an empty shadow layer."""
        result = generate_shadow(100, 100, 50, 80, 40, 0.0)
        assert np.all(result == 0)

    def test_negative_intensity_returns_empty(self):
        """Negative intensity produces an empty shadow layer."""
        result = generate_shadow(100, 100, 50, 80, 40, -0.5)
        assert np.all(result == 0)

    def test_zero_person_width_returns_empty(self):
        """Zero person width produces an empty shadow layer."""
        result = generate_shadow(100, 100, 50, 80, 0, 0.5)
        assert np.all(result == 0)

    def test_shadow_has_alpha(self):
        """Shadow with positive intensity has non-zero alpha values."""
        result = generate_shadow(200, 200, 100, 160, 80, 0.8)
        assert np.max(result[:, :, 3]) > 0

    def test_shadow_rgb_is_dark(self):
        """Shadow RGB channels are dark (near zero) where alpha is present."""
        result = generate_shadow(200, 200, 100, 160, 80, 0.8)
        alpha_mask = result[:, :, 3] > 10
        if np.any(alpha_mask):
            # RGB values where shadow exists should be low
            for ch in range(3):
                max_val = result[:, :, ch][alpha_mask].max()
                assert max_val < 50  # shadow color is black (0,0,0)

    def test_high_intensity_stronger_shadow(self):
        """Higher intensity produces stronger (higher alpha) shadow."""
        low = generate_shadow(200, 200, 100, 160, 80, 0.3)
        high = generate_shadow(200, 200, 100, 160, 80, 0.9)
        assert np.max(high[:, :, 3]) >= np.max(low[:, :, 3])

    def test_shadow_near_foot_position(self):
        """Shadow alpha is concentrated near foot position."""
        result = generate_shadow(200, 200, 100, 160, 80, 0.8)
        # The shadow should be near y=160
        top_half_alpha = np.max(result[:80, :, 3])
        bottom_region_alpha = np.max(result[140:180, :, 3])
        assert bottom_region_alpha > top_half_alpha

    def test_foot_position_clamped_to_canvas(self):
        """Foot position outside canvas is clamped."""
        # Should not raise an error
        result = generate_shadow(100, 100, -10, 150, 40, 0.5)
        assert result.shape == (100, 100, 4)
        result2 = generate_shadow(100, 100, 200, 50, 40, 0.5)
        assert result2.shape == (100, 100, 4)
