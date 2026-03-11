"""Tests for region detection service."""

import numpy as np
import pytest
from PIL import Image

from app.services.region_detector import detect_regions, erase_regions, erase_manual


def _make_two_blobs_image(width=200, height=200, gap=40):
    """Create an RGBA image with two separated foreground blobs."""
    rgba = np.zeros((height, width, 4), dtype=np.uint8)

    # Blob 1: left side (larger)
    rgba[30:150, 10:70, :3] = [255, 100, 100]
    rgba[30:150, 10:70, 3] = 255

    # Blob 2: right side (smaller)
    rgba[50:130, 70 + gap : 70 + gap + 40, :3] = [100, 100, 255]
    rgba[50:130, 70 + gap : 70 + gap + 40, 3] = 255

    return Image.fromarray(rgba, "RGBA")


def _make_single_blob_image(width=200, height=200):
    """Create an RGBA image with a single foreground blob."""
    rgba = np.zeros((height, width, 4), dtype=np.uint8)
    rgba[30:170, 30:170, :3] = [200, 200, 200]
    rgba[30:170, 30:170, 3] = 255
    return Image.fromarray(rgba, "RGBA")


def _make_empty_image(width=200, height=200):
    """Create an RGBA image with no foreground."""
    rgba = np.zeros((height, width, 4), dtype=np.uint8)
    return Image.fromarray(rgba, "RGBA")


class TestDetectRegions:
    """Tests for detect_regions()."""

    def test_detects_two_blobs(self):
        image = _make_two_blobs_image()
        regions, labels, label_map = detect_regions(image)

        assert len(regions) == 2
        assert regions[0]["is_main"] is True
        assert regions[1]["is_main"] is False

    def test_detects_single_blob(self):
        image = _make_single_blob_image()
        regions, labels, label_map = detect_regions(image)

        assert len(regions) == 1
        assert regions[0]["is_main"] is True

    def test_empty_image_returns_no_regions(self):
        image = _make_empty_image()
        regions, labels, label_map = detect_regions(image)

        assert len(regions) == 0

    def test_regions_sorted_by_area_descending(self):
        image = _make_two_blobs_image()
        regions, labels, label_map = detect_regions(image)

        assert len(regions) >= 2
        assert regions[0]["area"] >= regions[1]["area"]

    def test_region_has_required_fields(self):
        image = _make_two_blobs_image()
        regions, labels, label_map = detect_regions(image)

        for r in regions:
            assert "region_id" in r
            assert "bbox" in r
            assert "area" in r
            assert "center" in r
            assert "thumbnail" in r
            assert "is_main" in r
            assert "x" in r["bbox"]
            assert "y" in r["bbox"]
            assert "width" in r["bbox"]
            assert "height" in r["bbox"]

    def test_thumbnails_are_base64(self):
        image = _make_two_blobs_image()
        regions, labels, label_map = detect_regions(image)

        for r in regions:
            assert r["thumbnail"].startswith("data:image/png;base64,")

    def test_label_map_has_entries(self):
        image = _make_two_blobs_image()
        regions, labels, label_map = detect_regions(image)

        assert len(label_map) == len(regions)
        for r in regions:
            assert r["region_id"] in label_map


class TestEraseRegions:
    """Tests for erase_regions()."""

    def test_erase_removes_region(self):
        image = _make_two_blobs_image()
        regions, labels, label_map = detect_regions(image)

        # Erase the smaller region (region_id=1)
        erased = erase_regions(image, labels, label_map, [1])
        erased_alpha = np.array(erased)[:, :, 3]

        # Original has two blobs
        orig_alpha = np.array(image)[:, :, 3]
        assert np.sum(orig_alpha > 0) > np.sum(erased_alpha > 0)

    def test_erase_preserves_main_region(self):
        image = _make_two_blobs_image()
        regions, labels, label_map = detect_regions(image)

        # Erase region 1, keep region 0 (main)
        erased = erase_regions(image, labels, label_map, [1])
        erased_alpha = np.array(erased)[:, :, 3]

        # Main region should still have pixels
        assert np.sum(erased_alpha > 0) > 0

    def test_erase_all_regions(self):
        image = _make_two_blobs_image()
        regions, labels, label_map = detect_regions(image)

        all_ids = [r["region_id"] for r in regions]
        erased = erase_regions(image, labels, label_map, all_ids)
        erased_alpha = np.array(erased)[:, :, 3]

        # All should be transparent
        assert np.sum(erased_alpha > 0) == 0

    def test_erase_nonexistent_region_is_noop(self):
        image = _make_two_blobs_image()
        regions, labels, label_map = detect_regions(image)

        erased = erase_regions(image, labels, label_map, [999])
        orig_alpha = np.array(image)[:, :, 3]
        erased_alpha = np.array(erased)[:, :, 3]

        np.testing.assert_array_equal(orig_alpha, erased_alpha)


class TestEraseManual:
    """Tests for erase_manual()."""

    def test_erase_with_brush_strokes(self):
        image = _make_single_blob_image()
        strokes = [
            {"x": 50, "y": 50, "radius": 20},
            {"x": 60, "y": 60, "radius": 20},
        ]

        erased = erase_manual(image, strokes, 200, 200)
        erased_alpha = np.array(erased)[:, :, 3]
        orig_alpha = np.array(image)[:, :, 3]

        # Some pixels should have been erased
        assert np.sum(erased_alpha > 0) < np.sum(orig_alpha > 0)

    def test_erase_with_no_strokes_is_noop(self):
        image = _make_single_blob_image()
        erased = erase_manual(image, [], 200, 200)

        orig_alpha = np.array(image)[:, :, 3]
        erased_alpha = np.array(erased)[:, :, 3]

        np.testing.assert_array_equal(orig_alpha, erased_alpha)

    def test_erase_scales_to_image_coordinates(self):
        image = _make_single_blob_image(width=400, height=400)
        # Display is half size (200x200), stroke at center
        strokes = [{"x": 100, "y": 100, "radius": 10}]

        erased = erase_manual(image, strokes, 200, 200)
        erased_array = np.array(erased)

        # The erased area should be around the center of the 400x400 image
        center_alpha = erased_array[190:210, 190:210, 3]
        assert np.mean(center_alpha) < 200  # Should be partially or fully erased
