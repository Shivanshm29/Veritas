"""
Evidence Retrieval & Source Intelligence orchestration service for Veritas.

Coordinates query generation, provider retrieval, source credibility scoring,
evidence deduplication, and passage extraction into canonical SourceDocument
and EvidenceItem contracts.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
import time
from typing import List, Optional
import uuid

from backend.app.core.errors import EmptyTextError, PayloadTooLargeError, ResourceNotFoundError
from backend.app.core.logging import logger
from backend.app.services.retrieval.credibility import SourceCredibilityEvaluator
from backend.app.services.retrieval.deduplication import EvidenceDeduplicator
from backend.app.services.retrieval.passage_extractor import PassageExtractor
from backend.app.services.retrieval.provider import (
    EvidenceRetrievalProvider,
    HybridRetrievalProvider,
    RawDocumentProposal,
    SimulatedRetrievalProvider,
)
from backend.app.services.retrieval.query import EvidenceQuery, QueryGenerator
from contracts.schemas.models import (
    Claim,
    EvidenceItem,
    EvidenceStance,
    RetrievalMethod,
    SourceDocument,
)


MAX_QUERY_CHARS = 5000
MAX_RESULTS_LIMIT = 50


@dataclass
class EvidenceRetrievalBatch:
    """Structured response from the evidence retrieval pipeline."""
    query: EvidenceQuery
    source_documents: List[SourceDocument]
    evidence_items: List[EvidenceItem]
    total_sources: int
    total_evidence_items: int
    duplicates_detected: int
    execution_time_ms: int
    provider_status: str
    warnings: List[str] = field(default_factory=list)


class EvidenceRetrievalService:
    """
    Main orchestration service for Phase 3 Source Intelligence & Evidence Retrieval.
    Guarantees strict separation between retrieval relevance and claim truth.
    """

    def __init__(
        self,
        provider: Optional[EvidenceRetrievalProvider] = None,
        method_version: str = "veritas-retrieval-v1",
    ):
        self.provider = provider or HybridRetrievalProvider()
        self.method_version = method_version

    def retrieve_for_claim(
        self,
        claim: Claim,
        max_results: int = 10,
        domain_filters: Optional[List[str]] = None,
    ) -> EvidenceRetrievalBatch:
        """Generates a query from a Claim and retrieves relevant evidence items."""
        query = QueryGenerator.from_claim(claim)
        if domain_filters:
            query.domain_filter = domain_filters
        return self._execute_retrieval(query, max_results=max_results, claim_id=claim.id)

    def retrieve_for_text(
        self,
        query_text: str,
        claim_id: Optional[str] = None,
        entities: Optional[List[str]] = None,
        language: Optional[str] = None,
        max_results: int = 10,
        domain_filters: Optional[List[str]] = None,
    ) -> EvidenceRetrievalBatch:
        """Executes retrieval directly from free-form text or propositions."""
        if not query_text or not query_text.strip():
            raise EmptyTextError("Retrieval query text cannot be empty or whitespace.")

        if len(query_text) > MAX_QUERY_CHARS:
            raise PayloadTooLargeError(
                max_size_bytes=MAX_QUERY_CHARS,
                actual_size_bytes=len(query_text),
            )

        query = QueryGenerator.generate(
            text=query_text,
            claim_id=claim_id,
            entities=entities,
            language=language,
            domain_filter=domain_filters,
        )
        return self._execute_retrieval(query, max_results=max_results, claim_id=claim_id)

    def _execute_retrieval(
        self,
        query: EvidenceQuery,
        max_results: int = 10,
        claim_id: Optional[str] = None,
    ) -> EvidenceRetrievalBatch:
        start_time = time.perf_counter()
        warnings: List[str] = []
        bounded_max = max(1, min(max_results, MAX_RESULTS_LIMIT))

        # 1. Execute search provider query
        try:
            raw_proposals = self.provider.retrieve(query, max_results=bounded_max)
            provider_status = "SUCCESS"
        except Exception as e:
            logger.error(f"Retrieval provider error: {e}")
            raise

        if not raw_proposals:
            warnings.append("No source documents matched the specified query terms.")
            elapsed_ms = int((time.perf_counter() - start_time) * 1000)
            return EvidenceRetrievalBatch(
                query=query,
                source_documents=[],
                evidence_items=[],
                total_sources=0,
                total_evidence_items=0,
                duplicates_detected=0,
                execution_time_ms=elapsed_ms,
                provider_status="EMPTY_RESULTS",
                warnings=warnings,
            )

        # 2. Convert proposals to dict format for deduplication
        doc_dicts = [
            {
                "id": f"doc_{uuid.uuid4()}",
                "title": p.title,
                "url": p.url,
                "domain": p.domain,
                "content": p.content,
                "author": p.author,
                "publisher": p.publisher,
                "published_date": p.published_date,
                "retrieval_method": p.retrieval_method,
                "is_simulated": p.is_simulated,
            }
            for p in raw_proposals
        ]

        # 3. Deduplication (exact hash + syndicated wire duplicate detection)
        unique_docs, duplicate_docs, dup_count = EvidenceDeduplicator.deduplicate_documents(doc_dicts)
        if dup_count > 0:
            warnings.append(
                f"Identified {dup_count} duplicate or syndicated source report(s); filtered from independent citation weight."
            )

        now = datetime.now(timezone.utc)
        target_claim_id = claim_id or query.claim_id or f"clm_{uuid.uuid4()}"

        source_documents: List[SourceDocument] = []
        evidence_items: List[EvidenceItem] = []

        # 4. Construct canonical SourceDocument and EvidenceItem models
        for doc_item in unique_docs:
            content_text = doc_item["content"]
            content_hash = doc_item["content_sha256"]

            # Evaluate domain credibility
            cred_res = SourceCredibilityEvaluator.evaluate(doc_item["domain"])

            # Create snippet (bounded length)
            snippet = content_text.strip()
            if len(snippet) < 10:
                snippet = snippet + " [content snippet]"
            if len(snippet) > 500:
                snippet = snippet[:497] + "..."

            source_doc = SourceDocument(
                id=doc_item["id"],
                title=doc_item["title"],
                url=doc_item["url"],
                domain=doc_item["domain"],
                author=doc_item.get("author"),
                publisher=doc_item.get("publisher"),
                published_date=doc_item.get("published_date"),
                retrieval_timestamp=now,
                content_snippet=snippet,
                content_sha256=content_hash,
                source_reliability_score=cred_res.reliability_score,
                full_text_storage_uri=None,
                is_simulated=doc_item.get("is_simulated", False),
            )
            source_documents.append(source_doc)

            # 5. Extract relevant evidence passages from the document
            passages = PassageExtractor.extract_passages(
                document_text=content_text,
                query_terms=query.search_terms,
                claim_text=query.raw_query,
                max_passages=2,
            )

            for p in passages:
                evi_item = EvidenceItem(
                    id=f"evi_{uuid.uuid4()}",
                    claim_id=target_claim_id,
                    source_document_id=source_doc.id,
                    evidence_text=p.text,
                    stance=p.stance_hint,
                    relevance_score=p.relevance_score,
                    page_number=p.page_number,
                    paragraph_index=p.paragraph_index,
                    retrieval_method=doc_item.get("retrieval_method", RetrievalMethod.HYBRID_RRF),
                    created_at=now,
                )
                evidence_items.append(evi_item)

        elapsed_ms = int((time.perf_counter() - start_time) * 1000)

        logger.info(
            f"Retrieved {len(evidence_items)} evidence items across {len(source_documents)} source documents "
            f"in {elapsed_ms}ms ({dup_count} duplicates suppressed) [Query: {ascii(query.raw_query[:30])}...]"
        )

        return EvidenceRetrievalBatch(
            query=query,
            source_documents=source_documents,
            evidence_items=evidence_items,
            total_sources=len(source_documents),
            total_evidence_items=len(evidence_items),
            duplicates_detected=dup_count,
            execution_time_ms=elapsed_ms,
            provider_status=provider_status,
            warnings=warnings,
        )


# Default singleton instance
_default_retrieval_service: Optional[EvidenceRetrievalService] = None


def get_retrieval_service() -> EvidenceRetrievalService:
    global _default_retrieval_service
    if _default_retrieval_service is None:
        _default_retrieval_service = EvidenceRetrievalService()
    return _default_retrieval_service
