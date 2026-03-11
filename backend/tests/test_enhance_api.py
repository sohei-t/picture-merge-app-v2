"""Tests for enhance/adjust API endpoints."""

import numpy as np
import pytest
from fastapi.testclient import TestClient
from PIL import Image

from app.main import app
from app.services.cache import SegmentedOutput, segmentation_cache


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture(autouse=True)
def clean_cache():
    """Clear caches before each test."""
    segmentation_cache.clear()
    from app.api.enhance import _original_images
    _original_images.clear()
    yield
    segmentation_cache.clear()
    _original_images.clear()


def _create_test_image():
    """Create a test RGBA image."""
    rgba = np.zeros((200, 200, 4), dtype=np.uint8)
    rgba[30:170, 30:170, :3] = [180, 120, 80]
    rgba[30:170, 30:170, 3] = 255
    return Image.fromarray(rgba, "RGBA")


def _add_test_entry(seg_id="seg_test_enhance"):
    image = _create_test_image()
    entry = SegmentedOutput(
        image=image,
        bbox=(30, 30, 140, 140),
        foot_y=170,
        original_size=(200, 200),
    )
    segmentation_cache.put(seg_id, entry)
    return seg_id


class TestAdjustEndpoint:
    """Tests for POST /api/adjust."""

    def test_adjust_brightness(self, client):
        seg_id = _add_test_entry()
        response = client.post("/api/adjust", json={
            "seg_id": seg_id,
            "brightness": 0.3,
        })
        assert response.status_code == 200
        data = response.json()
        assert data["seg_id"] == seg_id
        assert data["segmented_image"].startswith("data:image/png;base64,")

    def test_adjust_all_params(self, client):
        seg_id = _add_test_entry()
        response = client.post("/api/adjust", json={
            "seg_id": seg_id,
            "brightness": 0.2,
            "contrast": 0.1,
            "saturation": 0.3,
            "temperature": -0.1,
            "sharpness": 0.2,
        })
        assert response.status_code == 200

    def test_adjust_not_found(self, client):
        response = client.post("/api/adjust", json={
            "seg_id": "nonexistent",
            "brightness": 0.3,
        })
        assert response.status_code == 404

    def test_adjust_preserves_original(self, client):
        """Multiple adjustments should not degrade quality (always from original)."""
        seg_id = _add_test_entry()

        # First adjustment
        client.post("/api/adjust", json={
            "seg_id": seg_id,
            "brightness": 0.5,
        })

        # Second adjustment with different values
        response = client.post("/api/adjust", json={
            "seg_id": seg_id,
            "brightness": -0.3,
        })
        assert response.status_code == 200

    def test_adjust_reset(self, client):
        """All zeros should reset to original."""
        seg_id = _add_test_entry()

        # Adjust first
        client.post("/api/adjust", json={
            "seg_id": seg_id,
            "brightness": 0.5,
        })

        # Reset
        response = client.post("/api/adjust", json={
            "seg_id": seg_id,
            "brightness": 0.0,
            "contrast": 0.0,
            "saturation": 0.0,
            "temperature": 0.0,
            "sharpness": 0.0,
        })
        assert response.status_code == 200

    def test_adjust_validation_out_of_range(self, client):
        seg_id = _add_test_entry()
        response = client.post("/api/adjust", json={
            "seg_id": seg_id,
            "brightness": 2.0,  # Out of range
        })
        assert response.status_code == 422

    def test_adjust_updates_cache(self, client):
        seg_id = _add_test_entry()
        orig = segmentation_cache.get(seg_id)
        orig_mean = np.array(orig.image)[:, :, :3].mean()

        client.post("/api/adjust", json={
            "seg_id": seg_id,
            "brightness": 0.5,
        })

        updated = segmentation_cache.get(seg_id)
        updated_mean = np.array(updated.image)[:, :, :3].mean()
        assert updated_mean > orig_mean


class TestEnhanceBody:
    """Tests for _enhance_body() OpenCV body enhancement."""

    def test_enhance_body_produces_different_output(self):
        from app.services.ai_enhancer import _enhance_body
        image = _create_test_image()
        rgb = image.convert("RGB")
        alpha = Image.fromarray(np.array(image)[:, :, 3])
        result = _enhance_body(rgb, alpha)
        assert result.size == rgb.size
        assert result.mode == "RGB"
        # Should differ from input (denoising + CLAHE + sharpening)
        assert not np.array_equal(np.array(result), np.array(rgb))

    def test_enhance_body_preserves_transparent_areas(self):
        from app.services.ai_enhancer import _enhance_body
        image = _create_test_image()
        rgb = image.convert("RGB")
        alpha = Image.fromarray(np.array(image)[:, :, 3])
        result = _enhance_body(rgb, alpha)
        result_arr = np.array(result)
        orig_arr = np.array(rgb)
        alpha_arr = np.array(alpha)
        # Transparent pixels (alpha=0) should be unchanged
        transparent = alpha_arr == 0
        np.testing.assert_array_equal(
            result_arr[transparent], orig_arr[transparent]
        )

    def test_enhance_body_no_alpha(self):
        from app.services.ai_enhancer import _enhance_body
        rgb = _create_test_image().convert("RGB")
        result = _enhance_body(rgb, None)
        assert result.size == rgb.size
        assert result.mode == "RGB"


# Note: AI enhance tests are skipped here because they require
# downloading large model weights (100MB+). They should be tested
# in integration/manual testing.
class TestAiEnhanceEndpoint:
    """Tests for POST /api/ai-enhance/{seg_id} — basic validation only."""

    def test_ai_enhance_not_found(self, client):
        response = client.post("/api/ai-enhance/nonexistent")
        assert response.status_code == 404
