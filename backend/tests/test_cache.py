"""Tests for SegmentationCache service."""

import pytest
import numpy as np
from PIL import Image

from app.services.cache import SegmentationCache, SegmentedOutput


def _make_output(color=(100, 150, 200)) -> SegmentedOutput:
    """Helper to create a minimal SegmentedOutput."""
    img = Image.new("RGBA", (100, 100), (*color, 255))
    return SegmentedOutput(
        image=img,
        bbox=(10, 10, 80, 80),
        foot_y=90,
        original_size=(100, 100),
    )


class TestSegmentationCache:
    """Unit tests for SegmentationCache."""

    def test_put_and_get(self):
        """Cache stores and retrieves entries."""
        cache = SegmentationCache()
        entry = _make_output()
        cache.put("seg_001", entry)
        assert cache.get("seg_001") is entry

    def test_get_missing_returns_none(self):
        """Cache returns None for missing key."""
        cache = SegmentationCache()
        assert cache.get("nonexistent") is None

    def test_lru_eviction(self):
        """Oldest entry is evicted when cache exceeds MAX_ENTRIES."""
        cache = SegmentationCache()
        for i in range(cache.MAX_ENTRIES + 1):
            cache.put(f"seg_{i:03d}", _make_output())
        # First entry should be evicted
        assert cache.get("seg_000") is None
        # Last entry should still be present
        assert cache.get(f"seg_{cache.MAX_ENTRIES:03d}") is not None

    def test_lru_access_refreshes_order(self):
        """Accessing an entry moves it to the end, preventing eviction."""
        cache = SegmentationCache()
        for i in range(cache.MAX_ENTRIES):
            cache.put(f"seg_{i:03d}", _make_output())
        # Access the first entry to refresh it
        cache.get("seg_000")
        # Add one more to trigger eviction
        cache.put("seg_new", _make_output())
        # seg_000 was refreshed, so seg_001 should be evicted
        assert cache.get("seg_000") is not None
        assert cache.get("seg_001") is None

    def test_put_existing_key_updates(self):
        """Putting an existing key updates the value."""
        cache = SegmentationCache()
        entry1 = _make_output((100, 100, 100))
        entry2 = _make_output((200, 200, 200))
        cache.put("seg_001", entry1)
        cache.put("seg_001", entry2)
        assert cache.get("seg_001") is entry2
        assert len(cache) == 1

    def test_clear(self):
        """Clear removes all entries."""
        cache = SegmentationCache()
        for i in range(5):
            cache.put(f"seg_{i}", _make_output())
        assert len(cache) == 5
        cache.clear()
        assert len(cache) == 0

    def test_len(self):
        """__len__ returns correct count."""
        cache = SegmentationCache()
        assert len(cache) == 0
        cache.put("seg_1", _make_output())
        assert len(cache) == 1
        cache.put("seg_2", _make_output())
        assert len(cache) == 2

    def test_max_entries_is_10(self):
        """MAX_ENTRIES is 10."""
        assert SegmentationCache.MAX_ENTRIES == 10
