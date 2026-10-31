"""
Unified Investigation Pipeline Orchestrator.

Integrates Ingestion (Module 1), Media Forensics (Modules 5-7),
Claim Intelligence (Module 3), Fact Verification (Module 4),
and Provenance Graph Lineage (Module 8) into a single cohesive investigation.
"""

from datetime import datetime, timezone
import logging
from pathlib import Path
import time
from typing import Any, Dict, List, Optional
import uuid
import numpy as np

from backend.app.schemas.feed import UnifiedPipelineResponse
from backend.app.services.image_forensics.analysis import analyze_image
from backend.app.services.nlp.extractor import ClaimExtractionService
from backend.app.services.provenance.hasher import compute_image_fingerprint
from backend.app.services.provenance.matcher import match_against_historical_references
from backend.app.services.verification.service import VerificationService

logger = logging.getLogger(__name__)

ARTIFACTS_DIR = Path("artifacts")


def _sanitize_for_json(val: Any) -> Any:
    """Recursively converts numpy primitives and arbitrary types to pure Python JSON-safe types."""
    if isinstance(val, (np.floating, float)):
        return float(val)
    elif isinstance(val, (np.integer, int)):
        return int(val)
    elif isinstance(val, np.ndarray):
        return val.tolist()
    elif isinstance(val, dict):
        return {str(k): _sanitize_for_json(v) for k, v in val.items()}
    elif isinstance(val, (list, tuple, set)):
        return [_sanitize_for_json(v) for v in val]
    return val


class InvestigationPipeline:
    """Unified pipeline chaining multimodal forensics, claims NLP, and provenance matching."""

    def __init__(self):
        self.claim_service = ClaimExtractionService()
        self.verification_service = VerificationService()

    async def execute_investigation(
        self,
        claim_text: str,
        media_path: Optional[Path] = None,
        source_url: Optional[str] = None,
        source_platform: Optional[str] = None,
        post_metadata: Optional[Dict[str, Any]] = None,
        investigation_id: Optional[str] = None,
        mode: str = "URL_AUDIT",
    ) -> UnifiedPipelineResponse:
        """Runs the complete end-to-end investigation workflow."""
        start_time = time.perf_counter()
        inv_id = investigation_id or f"inv_{uuid.uuid4()}"

        extracted_claims_list: List[Dict[str, Any]] = []
        claim_assessments_list: List[Dict[str, Any]] = []
        forensic_findings: Optional[Dict[str, Any]] = None
        provenance_data: Optional[Dict[str, Any]] = None

        # ── 1. Multimodal Forensics & Perceptual Provenance ────────────────────
        if media_path and media_path.is_file():
            try:
                # Run image forensic analysis
                forensics_raw = analyze_image(media_path, ARTIFACTS_DIR)
                forensic_findings = forensics_raw

                # Run perceptual fingerprinting & historical provenance matching
                fingerprint = compute_image_fingerprint(media_path)
                phash_val = (
                    fingerprint.get("phash", "")
                    if isinstance(fingerprint, dict)
                    else getattr(fingerprint, "phash", "")
                )
                match_results = match_against_historical_references(
                    phash=phash_val,
                    hamming_threshold=14,
                )

                # Construct provenance DAG representation
                nodes = [
                    {"id": f"src_{inv_id[:8]}", "label": f"{source_platform or 'Source'} Post", "type": "SOURCE_POST"},
                    {"id": f"ast_{inv_id[:8]}", "label": "Ingested Media Asset", "type": "ASSET"},
                ]
                edges = [
                    {"id": "e_src_ast", "source": f"src_{inv_id[:8]}", "target": f"ast_{inv_id[:8]}", "relationship": "EMBEDS_MEDIA"}
                ]

                historical_matches_serialized = []
                for match in match_results.matches:
                    match_dict = match.model_dump() if hasattr(match, "model_dump") else match.__dict__
                    historical_matches_serialized.append(match_dict)
                    ref_node_id = f"ref_{match.reference_id}"
                    nodes.append({"id": ref_node_id, "label": match.title[:30], "type": "HISTORICAL_REFERENCE"})
                    edges.append({
                        "id": f"e_ast_{match.reference_id}",
                        "source": f"ast_{inv_id[:8]}",
                        "target": ref_node_id,
                        "relationship": match.match_grade,
                    })

                provenance_data = {
                    "fingerprint": (
                        fingerprint
                        if isinstance(fingerprint, dict)
                        else (fingerprint.model_dump() if hasattr(fingerprint, "model_dump") else fingerprint.__dict__)
                    ),
                    "matches_found": match_results.matches_found,
                    "matches": historical_matches_serialized,
                    "dag": {
                        "nodes": nodes,
                        "edges": edges,
                        "is_valid_dag": True,
                    },
                }
            except Exception as exc:
                logger.warning(f"Forensic / Provenance analysis skipped due to error: {exc}")

        # ── 2. Claim Extraction (Module 3) ───────────────────────────────────
        if claim_text and claim_text.strip():
            try:
                extraction_batch = self.claim_service.extract_claims(
                    text=claim_text,
                    investigation_id=inv_id,
                )
                for clm in extraction_batch.claims:
                    extracted_claims_list.append(clm.model_dump() if hasattr(clm, "model_dump") else clm.__dict__)
            except Exception as exc:
                logger.warning(f"Claim extraction error: {exc}")

        # If rule-based extractor abstained (e.g. short headline), treat raw text as 1 candidate claim
        if not extracted_claims_list and claim_text and len(claim_text.strip()) > 10:
            extracted_claims_list.append({
                "id": f"clm_{uuid.uuid4()}",
                "investigation_id": inv_id,
                "claim_text": claim_text.strip(),
                "category": "GENERAL_FACTUAL",
                "extracted_at": datetime.now(timezone.utc).isoformat(),
            })

        # ── 3. Evidence Retrieval & Fact Verification (Module 4) ─────────────
        for clm_dict in extracted_claims_list:
            text_to_verify = clm_dict.get("claim_text", "")
            if not text_to_verify:
                continue
            try:
                assessment_res = self.verification_service.verify_claim_text(
                    claim_text=text_to_verify,
                    investigation_id=inv_id,
                    persist=False,
                )
                assessment_dict = (
                    assessment_res.model_dump()
                    if hasattr(assessment_res, "model_dump")
                    else assessment_res.__dict__
                )
                claim_assessments_list.append(assessment_dict)
            except Exception as exc:
                logger.warning(f"Verification failed for claim '{text_to_verify}': {exc}")
                claim_assessments_list.append({
                    "id": f"asm_{uuid.uuid4()}",
                    "claim_id": clm_dict.get("id", ""),
                    "verdict": "INSUFFICIENT_EVIDENCE",
                    "confidence_score": 0.5,
                    "explanation": f"Automated retrieval inconclusive: {exc}",
                    "assessed_at": datetime.now(timezone.utc).isoformat(),
                })

        # ── 4. Verdict Synthesis ─────────────────────────────────────────────
        verdict_summary = self._synthesize_overall_verdict(
            claims=claim_assessments_list,
            forensics=forensic_findings,
            provenance=provenance_data,
        )

        duration_ms = int((time.perf_counter() - start_time) * 1000)

        return UnifiedPipelineResponse(
            investigation_id=inv_id,
            status="COMPLETED",
            mode=mode,
            source_url=source_url,
            source_platform=source_platform,
            post_metadata=post_metadata,
            claims=_sanitize_for_json(extracted_claims_list),
            claim_assessments=_sanitize_for_json(claim_assessments_list),
            forensic_findings=_sanitize_for_json(forensic_findings),
            provenance=_sanitize_for_json(provenance_data),
            verdict_summary=verdict_summary,
            execution_time_ms=duration_ms,
        )

    @staticmethod
    def _synthesize_overall_verdict(
        claims: List[Dict[str, Any]],
        forensics: Optional[Dict[str, Any]],
        provenance: Optional[Dict[str, Any]],
    ) -> str:
        parts: List[str] = []

        # Check media forensics anomalies
        has_media_anomaly = False
        if forensics:
            for finding in forensics.get("findings", []):
                details = finding.get("result_details", {})
                if details.get("candidate_detected") or (details.get("mean_absolute_difference", 0) > 6.0):
                    has_media_anomaly = True
                    break

        if has_media_anomaly:
            parts.append("Visual forensics detected geometric copy-move or compression anomalies.")
        elif forensics:
            parts.append("No definitive visual tampering artifacts detected in media header/spectral analysis.")

        # Check provenance
        if provenance and provenance.get("matches_found", 0) > 0:
            top_match = provenance["matches"][0]
            parts.append(
                f"Historical matching identified visual predecessor in reference archives: "
                f"'{top_match.get('title')}' ({top_match.get('match_grade')})."
            )

        # Check claim verifications
        verdicts = [c.get("verdict") for c in claims]
        if "REFUTED" in verdicts:
            parts.append("Primary factual assertions contradict verified public records (Verdict: REFUTED).")
        elif "SUPPORTED" in verdicts:
            parts.append("Core factual assertions corroborated by official source archives (Verdict: SUPPORTED).")
        elif "INSUFFICIENT_EVIDENCE" in verdicts:
            parts.append("Available public reporting is insufficient to substantiate or refute the claim.")
        else:
            parts.append("Investigation completed across multimodal indicators.")

        return " ".join(parts)


unified_pipeline = InvestigationPipeline()
