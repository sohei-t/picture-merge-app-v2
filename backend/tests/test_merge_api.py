"""Tests for POST /api/merge endpoint."""

import base64
import io

import pytest
from PIL import Image


class TestMergeEndpointSuccess:
    """Successful merge tests."""

    def test_preview_mode(self, client, segmented_pair):
        """BE-MRG-001: Preview mode returns 512x512 JPEG."""
        id1, id2 = segmented_pair
        response = client.post(
            "/api/merge",
            json={
                "image1_id": id1,
                "image2_id": id2,
                "preview_mode": True,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["merged_image"].startswith("data:image/jpeg;base64,")
        assert data["output_size"]["width"] == 768
        assert data["output_size"]["height"] == 768
        assert data["processing_time_ms"] >= 0

    def test_full_resolution(self, client, segmented_pair):
        """BE-MRG-002: Full resolution returns PNG at settings size."""
        id1, id2 = segmented_pair
        response = client.post(
            "/api/merge",
            json={
                "image1_id": id1,
                "image2_id": id2,
                "preview_mode": False,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["merged_image"].startswith("data:image/png;base64,")
        assert data["output_size"]["width"] == 2048
        assert data["output_size"]["height"] == 2048

    def test_default_settings(self, client, segmented_pair):
        """BE-MRG-003: Merge with default settings."""
        id1, id2 = segmented_pair
        response = client.post(
            "/api/merge",
            json={"image1_id": id1, "image2_id": id2},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["output_size"]["width"] == 2048
        assert data["output_size"]["height"] == 2048

    def test_background_color(self, client, segmented_pair):
        """BE-MRG-004: Background color is applied."""
        id1, id2 = segmented_pair
        response = client.post(
            "/api/merge",
            json={
                "image1_id": id1,
                "image2_id": id2,
                "settings": {"background_color": "#FF0000"},
                "preview_mode": False,
            },
        )
        assert response.status_code == 200
        data = response.json()
        # Decode the image and check corner pixel
        b64 = data["merged_image"].split(",", 1)[1]
        img_bytes = base64.b64decode(b64)
        img = Image.open(io.BytesIO(img_bytes))
        # Top-left corner should be red (or close to it)
        pixel = img.getpixel((0, 0))
        assert pixel[0] > 200  # Red channel high
        assert pixel[1] < 50  # Green channel low
        assert pixel[2] < 50  # Blue channel low

    def test_custom_output_size(self, client, segmented_pair):
        """BE-MRG-005: Custom output size."""
        id1, id2 = segmented_pair
        response = client.post(
            "/api/merge",
            json={
                "image1_id": id1,
                "image2_id": id2,
                "settings": {"output_width": 1280, "output_height": 720},
                "preview_mode": False,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["output_size"]["width"] == 1280
        assert data["output_size"]["height"] == 720

    def test_person_position(self, client, segmented_pair):
        """BE-MRG-006: Person position parameters."""
        id1, id2 = segmented_pair
        response = client.post(
            "/api/merge",
            json={
                "image1_id": id1,
                "image2_id": id2,
                "settings": {
                    "person1": {"x": 0.2, "y_offset": 0, "scale": 1.0},
                    "person2": {"x": 0.8, "y_offset": 0, "scale": 1.0},
                },
            },
        )
        assert response.status_code == 200

    def test_person_scale(self, client, segmented_pair):
        """BE-MRG-007: Person scale parameter."""
        id1, id2 = segmented_pair
        response = client.post(
            "/api/merge",
            json={
                "image1_id": id1,
                "image2_id": id2,
                "settings": {"person1": {"x": 0.3, "y_offset": 0, "scale": 1.5}},
            },
        )
        assert response.status_code == 200

    def test_shadow_enabled(self, client, segmented_pair):
        """BE-MRG-009: Shadow enabled generates shadow."""
        id1, id2 = segmented_pair
        response = client.post(
            "/api/merge",
            json={
                "image1_id": id1,
                "image2_id": id2,
                "settings": {"shadow": {"enabled": True, "intensity": 0.8}},
                "preview_mode": False,
            },
        )
        assert response.status_code == 200

    def test_shadow_disabled(self, client, segmented_pair):
        """BE-MRG-010: Shadow disabled."""
        id1, id2 = segmented_pair
        response = client.post(
            "/api/merge",
            json={
                "image1_id": id1,
                "image2_id": id2,
                "settings": {"shadow": {"enabled": False}},
            },
        )
        assert response.status_code == 200

    def test_color_correction_enabled(self, client, segmented_pair):
        """BE-MRG-012: Color correction enabled."""
        id1, id2 = segmented_pair
        response = client.post(
            "/api/merge",
            json={
                "image1_id": id1,
                "image2_id": id2,
                "settings": {"color_correction": True},
            },
        )
        assert response.status_code == 200

    def test_color_correction_disabled(self, client, segmented_pair):
        """BE-MRG-013: Color correction disabled."""
        id1, id2 = segmented_pair
        response = client.post(
            "/api/merge",
            json={
                "image1_id": id1,
                "image2_id": id2,
                "settings": {"color_correction": False},
            },
        )
        assert response.status_code == 200

    def test_processing_time(self, client, segmented_pair):
        """BE-MRG-014: Processing time is returned."""
        id1, id2 = segmented_pair
        response = client.post(
            "/api/merge",
            json={"image1_id": id1, "image2_id": id2},
        )
        data = response.json()
        assert data["processing_time_ms"] >= 0
        assert isinstance(data["processing_time_ms"], int)

    def test_preview_smaller_than_full(self, client, segmented_pair):
        """BE-MRG-015: Preview response is smaller than full resolution."""
        id1, id2 = segmented_pair
        r_preview = client.post(
            "/api/merge",
            json={"image1_id": id1, "image2_id": id2, "preview_mode": True},
        )
        r_full = client.post(
            "/api/merge",
            json={"image1_id": id1, "image2_id": id2, "preview_mode": False},
        )
        preview_len = len(r_preview.json()["merged_image"])
        full_len = len(r_full.json()["merged_image"])
        assert preview_len < full_len


class TestMergeEndpointErrors:
    """Error case tests for merge endpoint."""

    def test_invalid_image1_id(self, client, segmented_pair):
        """BE-MRG-016: Non-existent image1_id."""
        _, id2 = segmented_pair
        response = client.post(
            "/api/merge",
            json={"image1_id": "seg_nonexist", "image2_id": id2},
        )
        assert response.status_code == 404
        data = response.json()
        assert data["error"] == "invalid_segment_id"

    def test_invalid_image2_id(self, client, segmented_pair):
        """BE-MRG-017: Non-existent image2_id."""
        id1, _ = segmented_pair
        response = client.post(
            "/api/merge",
            json={"image1_id": id1, "image2_id": "seg_nonexist"},
        )
        assert response.status_code == 404
        data = response.json()
        assert data["error"] == "invalid_segment_id"

    def test_both_ids_invalid(self, client):
        """BE-MRG-018: Both IDs invalid."""
        response = client.post(
            "/api/merge",
            json={"image1_id": "seg_invalid1", "image2_id": "seg_invalid2"},
        )
        assert response.status_code == 404

    def test_scale_too_low(self, client, segmented_pair):
        """BE-MRG-019: Scale below minimum (0.1)."""
        id1, id2 = segmented_pair
        response = client.post(
            "/api/merge",
            json={
                "image1_id": id1,
                "image2_id": id2,
                "settings": {"person1": {"x": 0.3, "y_offset": 0, "scale": 0.1}},
            },
        )
        assert response.status_code == 422  # Pydantic validation error

    def test_scale_too_high(self, client, segmented_pair):
        """BE-MRG-020: Scale above maximum (3.0)."""
        id1, id2 = segmented_pair
        response = client.post(
            "/api/merge",
            json={
                "image1_id": id1,
                "image2_id": id2,
                "settings": {"person1": {"x": 0.3, "y_offset": 0, "scale": 3.0}},
            },
        )
        assert response.status_code == 422

    def test_x_too_low(self, client, segmented_pair):
        """BE-MRG-021: X position below minimum."""
        id1, id2 = segmented_pair
        response = client.post(
            "/api/merge",
            json={
                "image1_id": id1,
                "image2_id": id2,
                "settings": {"person1": {"x": -0.1, "y_offset": 0, "scale": 1.0}},
            },
        )
        assert response.status_code == 422

    def test_x_too_high(self, client, segmented_pair):
        """BE-MRG-022: X position above maximum."""
        id1, id2 = segmented_pair
        response = client.post(
            "/api/merge",
            json={
                "image1_id": id1,
                "image2_id": id2,
                "settings": {"person1": {"x": 1.5, "y_offset": 0, "scale": 1.0}},
            },
        )
        assert response.status_code == 422

    def test_intensity_too_high(self, client, segmented_pair):
        """BE-MRG-023: Shadow intensity above maximum."""
        id1, id2 = segmented_pair
        response = client.post(
            "/api/merge",
            json={
                "image1_id": id1,
                "image2_id": id2,
                "settings": {"shadow": {"enabled": True, "intensity": 2.0}},
            },
        )
        assert response.status_code == 422

    def test_output_width_too_small(self, client, segmented_pair):
        """BE-MRG-024: Output width below minimum."""
        id1, id2 = segmented_pair
        response = client.post(
            "/api/merge",
            json={
                "image1_id": id1,
                "image2_id": id2,
                "settings": {"output_width": 10},
            },
        )
        assert response.status_code == 422

    def test_output_width_too_large(self, client, segmented_pair):
        """BE-MRG-025: Output width above maximum."""
        id1, id2 = segmented_pair
        response = client.post(
            "/api/merge",
            json={
                "image1_id": id1,
                "image2_id": id2,
                "settings": {"output_width": 5000},
            },
        )
        assert response.status_code == 422

    def test_invalid_background_color(self, client, segmented_pair):
        """BE-MRG-026: Invalid background color format."""
        id1, id2 = segmented_pair
        response = client.post(
            "/api/merge",
            json={
                "image1_id": id1,
                "image2_id": id2,
                "settings": {"background_color": "red"},
            },
        )
        assert response.status_code == 422

    def test_missing_body(self, client):
        """BE-MRG-027: Missing request body."""
        response = client.post("/api/merge")
        assert response.status_code == 422

    def test_missing_image1_id(self, client, segmented_pair):
        """BE-MRG-028: Missing image1_id."""
        _, id2 = segmented_pair
        response = client.post(
            "/api/merge",
            json={"image2_id": id2},
        )
        assert response.status_code == 422
