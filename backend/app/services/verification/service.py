"""
Evidence-Based Claim Verification Service Orchestrator for Veritas (Phase 4).

Coordinates Claim extraction context, external/archival Evidence Retrieval (Phase 3),
Stance Classification, and Multi-Source Aggregation to yield canonical ClaimAssessment records.
"""

from datetime import datetime, timezone
import time
from typing import Dict, List, Optional, Tuple
from uuid import uuid4
from sqlalchemy.orm import Session

from contracts.schemas.models import (
    Claim,
    ClaimAssessment,
    ClaimModalityOrigin,
    ClaimStatus,
    ClaimVerdict,
    EntityPrefix,
    EvidenceItem,
    SourceDocument,
    validate_prefixed_id,
)
from backend.app.core.errors import (
    EmptyTextError,
    InvalidIdentifierError,
    ResourceNotFoundError,
)
from backend.app.core.logging import logger
from backend.app.db.models.claim import ClaimRecord
from backend.app.db.models.claim_assessment import ClaimAssessmentRecord
from backend.app.db.models.evidence_item import EvidenceItemRecord
from backend.app.db.models.source_document import SourceDocumentRecord
from backend.app.db.repositories.claim import ClaimRepository
from backend.app.db.repositories.claim_assessment import ClaimAssessmentRepository
from backend.app.db.repositories.evidence_item import EvidenceItemRepository
from backend.app.db.repositories.source_document import SourceDocumentRepository
from backend.app.services.retrieval.service import (
    EvidenceRetrievalBatch,
    get_retrieval_service,
)
from backend.app.services.verification.aggregation import EvidenceAggregator
from backend.app.services.verification.stance_classifier import (
    StanceClassificationResult,
    get_stance_classifier,
)


class VerificationService:
    """
    High-level verification engine for assessing claims against evidentiary sources.
    """

    def __init__(self):
        self.retrieval_service = get_retrieval_service()
        self.stance_classifier = get_stance_classifier()
        self.aggregator = EvidenceAggregator()

    def verify_claim(
        self,
        claim: Claim,
        evidence_items: Optional[List[EvidenceItem]] = None,
        source_documents: Optional[List[SourceDocument]] = None,
        investigation_id: Optional[str] = None,
        db: Optional[Session] = None,
        persist: bool = True,
    ) -> ClaimAssessment:
        """
        Assesses a Claim object against provided or freshly retrieved evidence.
        """
        inv_id = investigation_id or claim.investigation_id

        # 1. If evidence items not provided, retrieve them using Phase 3 service
        items = evidence_items
        sources = source_documents or []

        if items is None:
            retrieval_batch: EvidenceRetrievalBatch = self.retrieval_service.retrieve_for_text(
                query_text=claim.claim_text,
                claim_id=claim.id,
                entities=claim.claim_entities,
                language=claim.language,
                max_results=5,
            )
            items = retrieval_batch.evidence_items
            sources = retrieval_batch.source_documents

            # Persist newly retrieved sources and items if DB is active and persist=True
            if db and persist and items:
                doc_repo = SourceDocumentRepository(db)
                evi_repo = EvidenceItemRepository(db)
                for s in sources:
                    if not doc_repo.get_by_id(s.id):
                        doc_repo.create(
                            SourceDocumentRecord(
                                id=s.id,
                                title=s.title,
                                url=s.url,
                                domain=s.domain,
                                author=s.author,
                                publisher=s.publisher,
                                published_date=s.published_date,
                                retrieval_timestamp=s.retrieval_timestamp,
                                content_snippet=s.content_snippet,
                                content_sha256=s.content_sha256,
                                source_reliability_score=s.source_reliability_score,
                                full_text_storage_uri=s.full_text_storage_uri,
                                is_simulated=s.is_simulated,
                            )
                        )
                evi_records = []
                for it in items:
                    rm_val = None
                    if it.retrieval_method:
                        rm_val = it.retrieval_method.value if hasattr(it.retrieval_method, "value") else str(it.retrieval_method)
                    evi_records.append(
                        EvidenceItemRecord(
                            id=it.id,
                            claim_id=it.claim_id,
                            source_document_id=it.source_document_id,
                            evidence_text=it.evidence_text,
                            stance=it.stance.value if hasattr(it.stance, "value") else str(it.stance),
                            relevance_score=it.relevance_score,
                            page_number=it.page_number,
                            paragraph_index=it.paragraph_index,
                            retrieval_method=rm_val,
                            created_at=it.created_at,
                        )
                    )
                evi_repo.create_batch(evi_records)

        # 2. Run multi-source stance aggregation
        assessment = self.aggregator.aggregate(
            claim=claim,
            evidence_items=items or [],
            sources=sources,
            investigation_id=inv_id,
        )

        # 3. Persist assessment and update claim status if DB is provided
        if db and persist:
            asm_repo = ClaimAssessmentRepository(db)
            asm_record = ClaimAssessmentRecord(
                id=assessment.id,
                investigation_id=assessment.investigation_id,
                claim_id=assessment.claim_id,
                verdict=assessment.verdict.value if hasattr(assessment.verdict, "value") else str(assessment.verdict),
                confidence_score=assessment.confidence_score,
                explanation=assessment.explanation,
                cited_evidence_ids=assessment.cited_evidence_ids,
                conflicting_points=assessment.conflicting_points,
                limitations=assessment.limitations,
                model_identifier=assessment.model_identifier,
                assessed_at=assessment.assessed_at,
            )
            asm_repo.create(asm_record)

            # Update Claim status in DB
            claim_repo = ClaimRepository(db)
            existing_claim = claim_repo.get_by_id(claim.id)
            if existing_claim:
                if assessment.verdict in (ClaimVerdict.SUPPORTED, ClaimVerdict.REFUTED, ClaimVerdict.CONTRADICTORY_EVIDENCE):
                    existing_claim.status = ClaimStatus.VERIFIED.value
                else:
                    existing_claim.status = ClaimStatus.UNVERIFIABLE.value
                db.commit()

        return assessment

    def verify_claim_by_id(
        self,
        claim_id: str,
        db: Session,
        persist: bool = True,
    ) -> ClaimAssessment:
        """
        Loads a claim from DB, checks for stored evidence, and conducts verification.
        """
        validate_prefixed_id(claim_id, EntityPrefix.CLAIM)
        claim_repo = ClaimRepository(db)
        record = claim_repo.get_by_id(claim_id)
        if not record:
            raise ResourceNotFoundError("Claim", claim_id)

        claim_schema = record.to_schema()

        # Check for existing persisted evidence items for this claim
        evi_repo = EvidenceItemRepository(db)
        existing_items = evi_repo.list_by_claim(claim_id)
        evidence_schemas: Optional[List[EvidenceItem]] = None
        source_schemas: Optional[List[SourceDocument]] = None

        if existing_items:
            evidence_schemas = [it.to_schema() for it in existing_items]
            doc_repo = SourceDocumentRepository(db)
            doc_ids = {it.source_document_id for it in existing_items}
            source_schemas = []
            for doc_id in doc_ids:
                d = doc_repo.get_by_id(doc_id)
                if d:
                    source_schemas.append(d.to_schema())

        return self.verify_claim(
            claim=claim_schema,
            evidence_items=evidence_schemas,
            source_documents=source_schemas,
            db=db,
            persist=persist,
        )

    def verify_claim_text(
        self,
        claim_text: str,
        investigation_id: Optional[str] = None,
        db: Optional[Session] = None,
        persist: bool = False,
    ) -> ClaimAssessment:
        """
        Ad-hoc verification of a claim text string.
        """
        if not claim_text or not claim_text.strip():
            raise EmptyTextError("Claim text cannot be empty for verification.")

        inv_id = investigation_id or f"inv_{uuid4()}"
        claim_id = f"clm_{uuid4()}"

        claim = Claim(
            id=claim_id,
            investigation_id=inv_id,
            claim_text=claim_text.strip(),
            modality_origin=ClaimModalityOrigin.USER_PROMPT,
            extraction_confidence=1.0,
            status=ClaimStatus.EXTRACTED,
            created_at=datetime.now(timezone.utc),
        )

        return self.verify_claim(
            claim=claim,
            investigation_id=inv_id,
            db=db,
            persist=persist,
        )


_DEFAULT_VERIFICATION_SERVICE: Optional[VerificationService] = None


def get_verification_service() -> VerificationService:
    """Returns the singleton VerificationService instance."""
    global _DEFAULT_VERIFICATION_SERVICE
    if _DEFAULT_VERIFICATION_SERVICE is None:
        _DEFAULT_VERIFICATION_SERVICE = VerificationService()
    return _DEFAULT_VERIFICATION_SERVICE
