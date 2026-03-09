"""Tests for POST /api/segment endpoint."""

import io
import re

import pytest
from PIL import Image


class TestSegmentEndpointSuccess:
    """Successful segmentation tests."""

    def test_jpeg_segmentation(self, client, sample_jpeg_image):
        """BE-SEG-001: JPEG image segmentation."""
        response = client.post(
            "/api/segment",
            files={"image": ("test.jpg", sample_jpeg_image, "image/jpeg")},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"].startswith("seg_")
        assert data["segmented_image"].startswith("data:image/png;base64,")
        assert data["bbox"]["x"] >= 0
        assert data["bbox"]["y"] >= 0
        assert data["bbox"]["width"] > 0
        assert data["bbox"]["height"] > 0
        assert data["foot_y"] > 0
        assert data["original_size"]["width"] == 300
        assert data["original_size"]["height"] == 400
        assert data["processing_time_ms"] >= 0

    def test_png_segmentation(self, client, sample_png_image):
        """BE-SEG-002: PNG image segmentation."""
        response = client.post(
            "/api/segment",
            files={"image": ("test.png", sample_png_image, "image/png")},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"].startswith("seg_")
        assert data["segmented_image"].startswith("data:image/png;base64,")

    def test_webp_segmentation(self, client, sample_webp_image):
        """BE-SEG-003: WebP image segmentation."""
        response = client.post(
            "/api/segment",
            files={"image": ("test.webp", sample_webp_image, "image/webp")},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"].startswith("seg_")

    def test_unique_ids(self, client, sample_jpeg_image):
        """BE-SEG-004: Segmentation IDs are unique."""
        r1 = client.post(
            "/api/segment",
            files={"image": ("test.jpg", sample_jpeg_image, "image/jpeg")},
        )
        r2 = client.post(
            "/api/segment",
            files={"image": ("test.jpg", sample_jpeg_image, "image/jpeg")},
        )
        assert r1.status_code == 200
        assert r2.status_code == 200
        id1 = r1.json()["id"]
        id2 = r2.json()["id"]
        assert id1 != id2
        assert re.match(r"^seg_[a-f0-9]{8}$", id1)
        assert re.match(r"^seg_[a-f0-9]{8}$", id2)

    def test_bbox_validity(self, client, sample_jpeg_image):
        """BE-SEG-005: BBox values are valid."""
        response = client.post(
            "/api/segment",
            files={"image": ("test.jpg", sample_jpeg_image, "image/jpeg")},
        )
        data = response.json()
        bbox = data["bbox"]
        orig = data["original_size"]
        assert bbox["x"] >= 0
        assert bbox["y"] >= 0
        assert bbox["width"] > 0
        assert bbox["height"] > 0
        # BBox should fit within processed image
        # (may be larger than original if enhancement was applied)
        enhanced = data.get("enhanced", False)
        scale = data.get("enhancement_scale", 1)
        effective_w = orig["width"] * scale if enhanced else orig["width"]
        effective_h = orig["height"] * scale if enhanced else orig["height"]
        assert bbox["x"] + bbox["width"] <= effective_w
        assert bbox["y"] + bbox["height"] <= effective_h

    def test_foot_y_validity(self, client, sample_jpeg_image):
        """BE-SEG-006: foot_y equals bbox.y + bbox.height."""
        response = client.post(
            "/api/segment",
            files={"image": ("test.jpg", sample_jpeg_image, "image/jpeg")},
        )
        data = response.json()
        assert data["foot_y"] == data["bbox"]["y"] + data["bbox"]["height"]

    def test_processing_time(self, client, sample_jpeg_image):
        """BE-SEG-007: processing_time_ms is returned."""
        response = client.post(
            "/api/segment",
            files={"image": ("test.jpg", sample_jpeg_image, "image/jpeg")},
        )
        data = response.json()
        assert data["processing_time_ms"] >= 0
        assert isinstance(data["processing_time_ms"], int)

    def test_cache_storage(self, client, sample_jpeg_image):
        """BE-SEG-010: Result is stored in cache."""
        response = client.post(
            "/api/segment",
            files={"image": ("test.jpg", sample_jpeg_image, "image/jpeg")},
        )
        seg_id = response.json()["id"]

        from app.services.cache import segmentation_cache
        assert segmentation_cache.get(seg_id) is not None


class TestSegmentEndpointErrors:
    """Error case tests for segmentation endpoint."""

    def test_pdf_file(self, client, pdf_file):
        """BE-SEG-011: PDF file is rejected."""
        response = client.post(
            "/api/segment",
            files={"image": ("test.pdf", pdf_file, "application/pdf")},
        )
        assert response.status_code == 400
        data = response.json()
        assert data["error"] == "invalid_image"

    def test_text_file(self, client, non_image_file):
        """BE-SEG-012: Text file is rejected."""
        response = client.post(
            "/api/segment",
            files={"image": ("test.txt", non_image_file, "text/plain")},
        )
        assert response.status_code == 400
        data = response.json()
        assert data["error"] == "invalid_image"

    def test_content_type_spoofing(self, client, pdf_file):
        """BE-SEG-013: Content-Type spoofing is detected via magic bytes."""
        response = client.post(
            "/api/segment",
            files={"image": ("test.jpg", pdf_file, "image/jpeg")},
        )
        assert response.status_code == 400
        data = response.json()
        assert data["error"] == "invalid_image"

    def test_oversized_file(self, client, oversized_file):
        """BE-SEG-014: Files over 20MB are rejected."""
        response = client.post(
            "/api/segment",
            files={"image": ("big.jpg", oversized_file, "image/jpeg")},
        )
        assert response.status_code == 413
        data = response.json()
        assert data["error"] == "file_too_large"

    def test_empty_file(self, client):
        """BE-SEG-015: Empty file is rejected."""
        response = client.post(
            "/api/segment",
            files={"image": ("empty.jpg", b"", "image/jpeg")},
        )
        assert response.status_code == 400

    def test_landscape_image(self, client):
        """BE-SEG-016: Image with no person detected (mocked as all-transparent)."""
        from unittest.mock import patch
        from PIL import Image as PILImage
        import numpy as np

        def mock_remove_no_person(image, **kwargs):
            width, height = image.size
            return PILImage.new("RGBA", (width, height), (0, 0, 0, 0))

        # Create a valid JPEG image
        img = PILImage.new("RGB", (300, 200), (50, 100, 50))
        buf = io.BytesIO()
        img.save(buf, format="JPEG")
        data = buf.getvalue()

        with patch("app.services.segmentation.remove", mock_remove_no_person):
            response = client.post(
                "/api/segment",
                files={"image": ("landscape.jpg", data, "image/jpeg")},
            )
        assert response.status_code == 422
        resp_data = response.json()
        assert resp_data["error"] == "segmentation_failed"
