"""LRU cache for segmentation results."""

from __future__ import annotations

from collections import OrderedDict
from dataclasses import dataclass, field
from typing import Optional

import numpy as np
from PIL import Image


@dataclass
class SegmentedOutput:
    """Segmentation output data."""

    image: Image.Image  # RGBA PIL Image
    bbox: tuple[int, int, int, int]  # (x, y, width, height)
    foot_y: int  # Foot Y coordinate
    original_size: tuple[int, int]  # (width, height)


class SegmentationCache:
    """In-memory LRU cache for segmentation results."""

    MAX_ENTRIES = 10

    def __init__(self) -> None:
        self._store: OrderedDict[str, SegmentedOutput] = OrderedDict()

    def put(self, seg_id: str, entry: SegmentedOutput) -> None:
        """Store a segmentation result. Evicts oldest if over capacity."""
        if seg_id in self._store:
            self._store.move_to_end(seg_id)
        self._store[seg_id] = entry
        while len(self._store) > self.MAX_ENTRIES:
            self._store.popitem(last=False)

    def get(self, seg_id: str) -> Optional[SegmentedOutput]:
        """Retrieve a segmentation result by ID. Updates LRU order."""
        if seg_id in self._store:
            self._store.move_to_end(seg_id)
            return self._store[seg_id]
        return None

    def clear(self) -> None:
        """Clear all entries."""
        self._store.clear()

    def __len__(self) -> int:
        return len(self._store)


# Global singleton instance
segmentation_cache = SegmentationCache()
