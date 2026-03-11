"""Tests for eraser API endpoints."""

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
    """Clear cache before each test."""
    segmentation_cache.clear()
    # Also clear detection cache
    from app.api.eraser import _detection_cache
    _detection_cache.clear()
    yield
    segmentation_cache.clear()
    _detection_cache.clear()


def _create_two_person_image():
    """Create a test image with two separated foreground regions."""
    rgba = np.zeros((300, 300, 4), dtype=np.uint8)
    # Person 1 (left, larger)
    rgba[30:200, 20:100, :3] = [255, 150, 150]
    rgba[30:200, 20:100, 3] = 255
    # Person 2 (right, smaller)
    rgba[50:180, 180:260, :3] = [150, 150, 255]
    rgba[50:180, 180:260, 3] = 255
    return Image.fromarray(rgba, "RGBA")


def _add_test_entry(seg_id="seg_test123"):
    """Add a test segmentation result to cache."""
    image = _create_two_person_image()
    entry = SegmentedOutput(
        image=image,
        bbox=(20, 30, 240, 170),
        foot_y=200,
        original_size=(300, 300),
    )
    segmentation_cache.put(seg_id, entry)
    return seg_id


class TestDetectRegionsEndpoint:
    """Tests for POST /api/detect-regions/{seg_id}."""

    def test_detect_regions_success(self, client):
        seg_id = _add_test_entry()
        response = client.post(f"/api/detect-regions/{seg_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["seg_id"] == seg_id
        assert data["region_count"] >= 2
        assert len(data["regions"]) >= 2

    def test_detect_regions_not_found(self, client):
        response = client.post("/api/detect-regions/seg_nonexistent")

        assert response.status_code == 404
        data = response.json()
        assert data["error"] == "invalid_segment_id"

    def test_detect_regions_returns_thumbnails(self, client):
        seg_id = _add_test_entry()
        response = client.post(f"/api/detect-regions/{seg_id}")

        data = response.json()
        for region in data["regions"]:
            assert region["thumbnail"].startswith("data:image/png;base64,")

    def test_detect_regions_marks_main(self, client):
        seg_id = _add_test_entry()
        response = client.post(f"/api/detect-regions/{seg_id}")

        data = response.json()
        main_count = sum(1 for r in data["regions"] if r["is_main"])
        assert main_count == 1


class TestEraseRegionsEndpoint:
    """Tests for POST /api/erase-regions."""

    def test_erase_region_success(self, client):
        seg_id = _add_test_entry()

        # First detect regions
        detect_resp = client.post(f"/api/detect-regions/{seg_id}")
        assert detect_resp.status_code == 200
        regions = detect_resp.json()["regions"]

        # Find non-main region
        non_main = [r for r in regions if not r["is_main"]]
        assert len(non_main) > 0

        # Erase it
        erase_resp = client.post("/api/erase-regions", json={
            "seg_id": seg_id,
            "region_ids": [non_main[0]["region_id"]],
        })

        assert erase_resp.status_code == 200
        data = erase_resp.json()
        assert data["seg_id"] == seg_id
        assert data["segmented_image"].startswith("data:image/png;base64,")

    def test_erase_without_detection_fails(self, client):
        seg_id = _add_test_entry()

        response = client.post("/api/erase-regions", json={
            "seg_id": seg_id,
            "region_ids": [1],
        })

        assert response.status_code == 400

    def test_erase_nonexistent_seg_id(self, client):
        response = client.post("/api/erase-regions", json={
            "seg_id": "seg_nonexistent",
            "region_ids": [0],
        })

        assert response.status_code == 404

    def test_erase_updates_cache(self, client):
        seg_id = _add_test_entry()

        # Get original image
        orig_entry = segmentation_cache.get(seg_id)
        orig_alpha_sum = np.sum(np.array(orig_entry.image)[:, :, 3] > 0)

        # Detect + erase
        detect_resp = client.post(f"/api/detect-regions/{seg_id}")
        regions = detect_resp.json()["regions"]
        non_main = [r for r in regions if not r["is_main"]]

        client.post("/api/erase-regions", json={
            "seg_id": seg_id,
            "region_ids": [non_main[0]["region_id"]],
        })

        # Check cache was updated
        updated_entry = segmentation_cache.get(seg_id)
        updated_alpha_sum = np.sum(np.array(updated_entry.image)[:, :, 3] > 0)
        assert updated_alpha_sum < orig_alpha_sum


class TestEraseManualEndpoint:
    """Tests for POST /api/erase-manual."""

    def test_erase_manual_success(self, client):
        seg_id = _add_test_entry()

        response = client.post("/api/erase-manual", json={
            "seg_id": seg_id,
            "strokes": [
                {"x": 50, "y": 50, "radius": 20},
                {"x": 60, "y": 60, "radius": 20},
            ],
            "display_width": 300,
            "display_height": 300,
        })

        assert response.status_code == 200
        data = response.json()
        assert data["seg_id"] == seg_id
        assert data["segmented_image"].startswith("data:image/png;base64,")

    def test_erase_manual_nonexistent_seg_id(self, client):
        response = client.post("/api/erase-manual", json={
            "seg_id": "seg_nonexistent",
            "strokes": [{"x": 50, "y": 50, "radius": 20}],
            "display_width": 300,
            "display_height": 300,
        })

        assert response.status_code == 404

    def test_erase_manual_updates_cache(self, client):
        seg_id = _add_test_entry()

        orig_entry = segmentation_cache.get(seg_id)
        orig_alpha_sum = np.sum(np.array(orig_entry.image)[:, :, 3] > 0)

        client.post("/api/erase-manual", json={
            "seg_id": seg_id,
            "strokes": [{"x": 50, "y": 100, "radius": 30}],
            "display_width": 300,
            "display_height": 300,
        })

        updated_entry = segmentation_cache.get(seg_id)
        updated_alpha_sum = np.sum(np.array(updated_entry.image)[:, :, 3] > 0)
        assert updated_alpha_sum < orig_alpha_sum
