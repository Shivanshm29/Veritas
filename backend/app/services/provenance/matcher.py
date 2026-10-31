from typing import List, Optional

from backend.app.schemas.provenance import (
    HistoricalMatch,
    HistoricalMatchResponse,
    MatchGrade,
    MediaFingerprint,
)
from backend.app.services.provenance.hasher import hamming_distance
from backend.app.services.provenance.reference_store import (
    HistoricalReferenceStore,
    reference_store,
)


def match_against_historical_references(
    fingerprint: MediaFingerprint,
    query_sha256: str,
    store: Optional[HistoricalReferenceStore] = None,
    max_hamming_threshold: int = 12,
) -> HistoricalMatchResponse:
    """
    Searches the reference collection for historical matches using perceptual hashes.
    Enforces the core rule:
    - Distinguishes verified relationships (EXACT, NEAR_DUPLICATE) from tentative similarity matches (TENTATIVE_SIMILAR).
    - Avoids treating visual similarity alone as proof of common origin or context.
    """
    active_store = store or reference_store
    all_refs = active_store.get_all()

    matches: List[HistoricalMatch] = []

    for ref in all_refs:
        # Check both pHash and dHash
        dist_phash = hamming_distance(fingerprint.phash, ref.phash)
        dist_dhash = hamming_distance(fingerprint.dhash, ref.dhash)

        # Minimum distance represents best alignment
        best_dist = min(dist_phash, dist_dhash)

        if best_dist <= max_hamming_threshold:
            # Map distance to match grade
            if best_dist == 0:
                grade = MatchGrade.EXACT
                is_confirmed = True
                basis = (
                    f"Identical perceptual hash (Hamming distance 0/64) matches verified reference "
                    f"'{ref.id}'. Confirmed visual match with identical frequency distribution."
                )
            elif best_dist <= 5:
                grade = MatchGrade.NEAR_DUPLICATE
                is_confirmed = True
                basis = (
                    f"Near-duplicate match (Hamming distance {best_dist}/64). Asset exhibits minor "
                    f"compression artifacts, downsampling, or slight cropping of reference '{ref.id}'."
                )
            else:
                grade = MatchGrade.TENTATIVE_SIMILAR
                is_confirmed = False
                basis = (
                    f"Tentative visual similarity (Hamming distance {best_dist}/64). Shared broad composition "
                    f"with reference '{ref.id}', but not confirmed as derived from the same source."
                )

            similarity = round(1.0 - (best_dist / 64.0), 4)

            matches.append(
                HistoricalMatch(
                    reference_id=ref.id,
                    title=ref.title,
                    source_url=ref.source_url,
                    publisher=ref.publisher,
                    original_published_date=ref.original_published_date,
                    hamming_distance=best_dist,
                    similarity_score=similarity,
                    match_grade=grade,
                    basis=basis,
                    is_confirmed_origin=is_confirmed,
                )
            )

    # Sort matches by best similarity (lowest hamming distance)
    matches.sort(key=lambda m: m.hamming_distance)

    return HistoricalMatchResponse(
        query_sha256=query_sha256,
        fingerprint=fingerprint,
        total_references_searched=len(all_refs),
        matches_found=len(matches),
        matches=matches,
    )
