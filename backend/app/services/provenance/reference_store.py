from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional


@dataclass
class ReferenceMediaItem:
    id: str
    title: str
    source_url: str
    publisher: str
    original_published_date: str
    sha256_hash: str
    phash: str
    dhash: str
    ahash: str
    description: str
    is_verified_original: bool = True
    metadata: Dict[str, str] = field(default_factory=dict)


class HistoricalReferenceStore:
    """
    In-memory and searchable reference database for historical media matching.
    Pre-populated with verified original reference records.
    """

    def __init__(self):
        self._store: Dict[str, ReferenceMediaItem] = {}
        self._seed_default_references()

    def _seed_default_references(self):
        """Seed baseline known historical media assets for testing and demonstration."""
        seed_items = [
            ReferenceMediaItem(
                id="ref_hist_2020_001",
                title="Official Press Briefing Photograph — G20 Summit Press Pool",
                source_url="https://apnews.com/article/press-pool-g20-summit-official",
                publisher="Associated Press",
                original_published_date="2020-11-21T14:30:00Z",
                sha256_hash="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
                phash="9c3a6e8f1b2d4c7a",
                dhash="a4b2c1d3e5f60718",
                ahash="ffff0000ffff0000",
                description="Verified uncropped official press pool photo from the summit plenary session.",
                is_verified_original=True,
            ),
            ReferenceMediaItem(
                id="ref_hist_2022_042",
                title="Satellite Imagery of Flooded Agricultural District",
                source_url="https://earthobservatory.nasa.gov/images/flooding-event-2022",
                publisher="NASA Earth Observatory",
                original_published_date="2022-08-14T08:15:00Z",
                sha256_hash="4a5b6c7d8e9f0123456789abcdef0123456789abcdef0123456789abcdef0123",
                phash="8f4e2a1b9c7d3e5f",
                dhash="1234567890abcdef",
                ahash="0000ffff0000ffff",
                description="Unprocessed calibrated Landsat-8 multispectral satellite capture.",
                is_verified_original=True,
            ),
            ReferenceMediaItem(
                id="ref_hist_2023_109",
                title="Stock City Skyline Sunset Video B-Roll",
                source_url="https://reuters.com/pictures/city-skyline-archive",
                publisher="Reuters Archive",
                original_published_date="2023-04-10T19:45:00Z",
                sha256_hash="789abcdef0123456789abcdef0123456789abcdef0123456789abcdef0123456",
                phash="bf1a2b3c4d5e6f70",
                dhash="fedcba9876543210",
                ahash="ffffffff00000000",
                description="Original 4K camera raw footage of metropolis downtown sunset.",
                is_verified_original=True,
            ),
        ]
        for item in seed_items:
            self._store[item.id] = item

    def get_all(self) -> List[ReferenceMediaItem]:
        return list(self._store.values())

    def get_by_id(self, ref_id: str) -> Optional[ReferenceMediaItem]:
        return self._store.get(ref_id)

    def add_reference(self, item: ReferenceMediaItem) -> None:
        self._store[item.id] = item

    def count(self) -> int:
        return len(self._store)


# Global singleton instance
reference_store = HistoricalReferenceStore()
