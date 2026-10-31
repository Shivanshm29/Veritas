"""
Provenance & Historical Media Matching Service.
Module 8 of PRAMAAN / Veritas.
"""

from backend.app.services.provenance.graph_builder import (
    build_provenance_graph,
    detect_cycles_in_graph,
)
from backend.app.services.provenance.hasher import (
    compute_ahash,
    compute_color_fingerprint,
    compute_dhash,
    compute_image_fingerprint,
    compute_phash,
    compute_video_fingerprints,
    hamming_distance,
)
from backend.app.services.provenance.matcher import match_against_historical_references
from backend.app.services.provenance.reference_store import (
    HistoricalReferenceStore,
    ReferenceMediaItem,
    reference_store,
)

__all__ = [
    "compute_ahash",
    "compute_dhash",
    "compute_phash",
    "compute_color_fingerprint",
    "compute_image_fingerprint",
    "compute_video_fingerprints",
    "hamming_distance",
    "match_against_historical_references",
    "HistoricalReferenceStore",
    "ReferenceMediaItem",
    "reference_store",
    "build_provenance_graph",
    "detect_cycles_in_graph",
]
