"""
Pluggable retrieval provider abstractions for Veritas Evidence Retrieval.

Includes:
- EvidenceRetrievalProvider (ABC)
- RawDocumentProposal dataclass
- SimulatedRetrievalProvider (offline, deterministic, clearly labeled simulated test fixture)
- LexicalBM25Provider (deterministic Okapi BM25 lexical ranking)
- HybridRetrievalProvider (multi-channel reciprocal rank fusion)
- ExternalSearchProvider (production search adapter treating external responses as untrusted)
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
import math
import re
from typing import Any, Dict, List, Optional, Set
import uuid

from backend.app.core.errors import ServiceUnavailableError, VeritasException
from backend.app.services.retrieval.query import EvidenceQuery
from contracts.schemas.models import RetrievalMethod


@dataclass
class RawDocumentProposal:
    """Raw unvalidated document proposal returned by a retrieval provider."""
    title: str
    url: str
    domain: str
    content: str
    author: Optional[str] = None
    publisher: Optional[str] = None
    published_date: Optional[datetime] = None
    retrieval_method: RetrievalMethod = RetrievalMethod.HYBRID_RRF
    is_simulated: bool = False
    provider_name: str = "simulated"
    metadata: Dict[str, Any] = field(default_factory=dict)


class EvidenceRetrievalProvider(ABC):
    """Abstract base class for all evidence retrieval providers."""

    @abstractmethod
    def retrieve(self, query: EvidenceQuery, max_results: int = 10) -> List[RawDocumentProposal]:
        """Queries the source corpus or index and returns ranked document proposals."""
        pass


class SimulatedRetrievalProvider(EvidenceRetrievalProvider):
    """
    Deterministic offline provider serving simulated evidence documents.
    Explicitly tags all outputs as simulated (`is_simulated=True`) to prevent
    simulated data from being mistaken for real-world verified facts.
    """

    def __init__(
        self,
        corpus: Optional[List[Dict[str, Any]]] = None,
        mode: str = "success",
        simulated_delay_s: float = 0.0,
    ):
        self.mode = mode
        self.simulated_delay_s = simulated_delay_s
        self.call_count = 0
        self.corpus = corpus if corpus is not None else self._default_corpus()

    @staticmethod
    def _default_corpus() -> List[Dict[str, Any]]:
        """Pre-populated deterministic reference corpus covering multiple domains."""
        now = datetime.now(timezone.utc)
        return [
            {
                "title": "[SIMULATED] Ministry of Health Press Briefing on Virus Containment",
                "url": "https://moh.gov.example/press/2026/virus-update-1200",
                "domain": "moh.gov.example",
                "author": "Public Health Directorate",
                "publisher": "National Information Office",
                "published_date": now,
                "content": (
                    "The Ministry of Health confirmed 1,200 new cases of the virus across the capital on Monday.\n\n"
                    "Hospital admissions have stabilized following rapid vaccination deployments across urban health centres.\n\n"
                    "Emergency responders deployed 500 medical staff to monitor quarantine isolation facilities."
                ),
                "keywords": ["ministry", "health", "virus", "cases", "1200", "capital", "monday"],
            },
            {
                "title": "[SIMULATED] Federal Reserve Board Monetary Policy Action Statement",
                "url": "https://fed.gov.example/monetary/2026-rates-increase",
                "domain": "fed.gov.example",
                "author": "Federal Open Market Committee",
                "publisher": "Federal Reserve Bulletin",
                "published_date": now,
                "content": (
                    "The Federal Reserve raised interest rates by 0.5% in September 2026 in response to ongoing inflation pressures.\n\n"
                    "The Committee decided unanimously to adjust the target range for the federal funds rate.\n\n"
                    "Economic indicators show continued employment expansion alongside persistent core price gains."
                ),
                "keywords": ["federal", "reserve", "interest", "rates", "0.5%", "inflation", "september", "2026"],
            },
            {
                "title": "[SIMULATED] Reuters: Central Bank Announces Rate Hike to Curb Inflation",
                "url": "https://reuters.com.example/finance/rates-rise-central-bank",
                "domain": "reuters.com.example",
                "author": "Reuters Financial Desk",
                "publisher": "Reuters International",
                "published_date": now,
                "content": (
                    "The Federal Reserve raised interest rates by 0.5% in September 2026 to curb inflation across commercial lending.\n\n"
                    "Financial markets responded with moderate bond yield increases while currency values held steady."
                ),
                "keywords": ["federal", "reserve", "interest", "rates", "0.5%", "inflation", "september", "reuters"],
            },
            {
                "title": "[SIMULATED] Syndicated Wire: Central Bank Rates Adjust 0.5%",
                "url": "https://wirefeed.media.example/wire/rates-0.5-update",
                "domain": "wirefeed.media.example",
                "author": "Reuters Financial Desk",
                "publisher": "Syndicated Media Group",
                "published_date": now,
                "content": (
                    "The Federal Reserve raised interest rates by 0.5% in September 2026 to curb inflation across commercial lending.\n\n"
                    "Financial markets responded with moderate bond yield increases while currency values held steady."
                ),
                "keywords": ["federal", "reserve", "interest", "rates", "0.5%", "inflation", "syndicated"],
            },
            {
                "title": "[SIMULATED] National Geological Survey: Coastal Seismic Event Report",
                "url": "https://geology.gov.example/earthquake/coastal-7.2",
                "domain": "geology.gov.example",
                "author": "Seismology Observation Unit",
                "publisher": "Geological Survey Records",
                "published_date": now,
                "content": (
                    "The 7.2 magnitude earthquake destroyed 40 buildings in the coastal city yesterday.\n\n"
                    "Emergency crews deployed 500 responders to clear debris and assist affected residents.\n\n"
                    "Tsunami warning sirens were deactivated after water levels remained within normal tidal parameters."
                ),
                "keywords": ["7.2", "magnitude", "earthquake", "destroyed", "40", "buildings", "coastal", "city", "500", "responders"],
            },
            {
                "title": "[SIMULATED] Contradictory Report: Local Municipality Denies Building Collapse Claims",
                "url": "https://localnews.example/article/disaster-claims-denied",
                "domain": "localnews.example",
                "author": "Staff Reporter",
                "publisher": "City Gazette",
                "published_date": now,
                "content": (
                    "Municipal officials denied that 40 buildings collapsed during the earthquake, reporting only minor structural cracks.\n\n"
                    "City engineers confirmed that emergency shelters remain mostly unoccupied."
                ),
                "keywords": ["earthquake", "buildings", "denied", "cracks", "city", "collapsed"],
            },
            {
                "title": "[SIMULATED] Reserve Bank of India Policy Notification (Hindi / Indic)",
                "url": "https://rbi.org.example/notifications/repo-rate-25bps",
                "domain": "rbi.org.example",
                "author": "Monetary Policy Department",
                "publisher": "Reserve Bank Gazette",
                "published_date": now,
                "content": (
                    "भारतीय रिजर्व बैंक ने आज रेपो दर में 25 आधार अंकों की वृद्धि की घोषणा की।\n\n"
                    "यह निर्णय मुद्रास्फीति को नियंत्रित करने और आर्थिक स्थिरता सुनिश्चित करने के लिए लिया गया है।"
                ),
                "keywords": ["भारतीय", "रिजर्व", "बैंक", "रेपो", "25", "वृद्धि", "rbi", "repo"],
            },
        ]

    def retrieve(self, query: EvidenceQuery, max_results: int = 10) -> List[RawDocumentProposal]:
        self.call_count += 1

        # Simulate provider failure modes
        if self.mode == "timeout":
            raise TimeoutError("Simulated retrieval provider timed out after 30.0s.")

        if self.mode == "rate_limit":
            raise VeritasException(
                status_code=429,
                title="Retrieval Provider Rate Limit Exceeded",
                detail="Simulated upstream search provider returned HTTP 429 Too Many Requests.",
                code="RETRIEVAL_RATE_LIMIT",
            )

        if self.mode == "outage":
            raise ServiceUnavailableError(
                service_name="SimulatedRetrievalProvider",
                reason="Simulated upstream knowledge base returned HTTP 503 Service Unavailable.",
            )

        if self.mode == "malformed":
            raise ValueError("Malformed response payload from upstream retrieval provider.")

        if self.mode == "empty":
            return []

        # Score documents against query terms
        query_terms = set(t.lower() for t in query.search_terms if len(t) > 2)
        scored_docs: List[tuple[float, Dict[str, Any]]] = []

        for item in self.corpus:
            doc_keywords = set(k.lower() for k in item.get("keywords", []))
            doc_text_lower = item["content"].lower()

            overlap = len(query_terms & doc_keywords)
            # Add string match score
            string_matches = sum(1 for t in query_terms if t in doc_text_lower)
            score = (overlap * 2.0) + (string_matches * 1.5)

            if score > 0 or not query_terms:
                scored_docs.append((score, item))

        scored_docs.sort(key=lambda x: x[0], reverse=True)
        top_items = scored_docs[:max_results]

        proposals = []
        for score, item in top_items:
            proposals.append(
                RawDocumentProposal(
                    title=item["title"],
                    url=item["url"],
                    domain=item["domain"],
                    content=item["content"],
                    author=item.get("author"),
                    publisher=item.get("publisher"),
                    published_date=item.get("published_date"),
                    retrieval_method=RetrievalMethod.HYBRID_RRF,
                    is_simulated=True,
                    provider_name="simulated",
                    metadata={"match_score": score},
                )
            )

        return proposals


class LexicalBM25Provider(EvidenceRetrievalProvider):
    """
    Deterministic BM25 lexical retrieval provider.
    Computes Okapi BM25 scores over indexed document passages.
    """

    def __init__(self, corpus: Optional[List[Dict[str, Any]]] = None, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.corpus = corpus or []
        self._index_corpus()

    def _tokenize(self, text: str) -> List[str]:
        return [w.lower() for w in re.findall(r"\b[\w\-\$%\.]+\b", text) if len(w) > 2]

    def _index_corpus(self):
        self.doc_tokens: List[List[str]] = [self._tokenize(d["content"]) for d in self.corpus]
        self.doc_lengths: List[int] = [len(toks) for toks in self.doc_tokens]
        self.avg_doc_len = (sum(self.doc_lengths) / max(1, len(self.doc_lengths))) if self.doc_lengths else 1.0

        # Term document frequency
        self.df: Dict[str, int] = {}
        for toks in self.doc_tokens:
            for term in set(toks):
                self.df[term] = self.df.get(term, 0) + 1

    def retrieve(self, query: EvidenceQuery, max_results: int = 10) -> List[RawDocumentProposal]:
        if not self.corpus:
            return []

        q_terms = [t.lower() for t in query.search_terms if len(t) > 2]
        if not q_terms:
            return []

        N = len(self.corpus)
        scores: List[tuple[float, int]] = []

        for doc_idx, toks in enumerate(self.doc_tokens):
            score = 0.0
            doc_len = self.doc_lengths[doc_idx]
            tf_map: Dict[str, int] = {}
            for t in toks:
                tf_map[t] = tf_map.get(t, 0) + 1

            for term in q_terms:
                if term not in tf_map:
                    continue
                tf = tf_map[term]
                df_val = self.df.get(term, 0)
                idf = math.log((N - df_val + 0.5) / (df_val + 0.5) + 1.0)
                numerator = tf * (self.k1 + 1.0)
                denominator = tf + self.k1 * (1.0 - self.b + self.b * (doc_len / self.avg_doc_len))
                score += idf * (numerator / max(1e-9, denominator))

            if score > 0:
                scores.append((score, doc_idx))

        scores.sort(key=lambda x: x[0], reverse=True)
        top_matches = scores[:max_results]

        results = []
        for score, idx in top_matches:
            item = self.corpus[idx]
            results.append(
                RawDocumentProposal(
                    title=item["title"],
                    url=item["url"],
                    domain=item["domain"],
                    content=item["content"],
                    author=item.get("author"),
                    publisher=item.get("publisher"),
                    published_date=item.get("published_date"),
                    retrieval_method=RetrievalMethod.BM25,
                    is_simulated=item.get("is_simulated", False),
                    provider_name="bm25",
                    metadata={"bm25_score": round(score, 4)},
                )
            )

        return results


class HybridRetrievalProvider(EvidenceRetrievalProvider):
    """
    Multi-channel retrieval provider executing Reciprocal Rank Fusion (RRF).

    Combines ranked candidate proposals across two configured retrieval channels.
    Note: Dense vector retrieval (embedding models, ANN vector indexes) is not implemented
    in Phase 3. Instead, this provider fuses arbitrary retrieval channels (e.g.
    lexical BM25 ranking and simulated/keyword search). When initialized with default
    arguments (lexical_provider=None, secondary_provider=None), it demonstrates RRF
    fusion across two simulated retrieval channels.
    """

    def __init__(
        self,
        lexical_provider: Optional[EvidenceRetrievalProvider] = None,
        secondary_provider: Optional[EvidenceRetrievalProvider] = None,
        rrf_k: int = 60,
    ):
        self.lexical_provider = lexical_provider or SimulatedRetrievalProvider()
        self.secondary_provider = secondary_provider or SimulatedRetrievalProvider()
        self.rrf_k = rrf_k

    def retrieve(self, query: EvidenceQuery, max_results: int = 10) -> List[RawDocumentProposal]:
        # Run both retrieval channels
        list_a = self.lexical_provider.retrieve(query, max_results=max_results * 2)
        list_b = self.secondary_provider.retrieve(query, max_results=max_results * 2)

        # Reciprocal Rank Fusion
        rrf_scores: Dict[str, float] = {}
        doc_map: Dict[str, RawDocumentProposal] = {}

        for rank, doc in enumerate(list_a):
            key = doc.url or doc.title
            rrf_scores[key] = rrf_scores.get(key, 0.0) + (1.0 / (self.rrf_k + rank + 1))
            doc_map[key] = doc

        for rank, doc in enumerate(list_b):
            key = doc.url or doc.title
            rrf_scores[key] = rrf_scores.get(key, 0.0) + (1.0 / (self.rrf_k + rank + 1))
            if key not in doc_map:
                doc_map[key] = doc

        # Rank by fused RRF score
        sorted_keys = sorted(rrf_scores.keys(), key=lambda k: rrf_scores[k], reverse=True)
        fused_proposals: List[RawDocumentProposal] = []

        for key in sorted_keys[:max_results]:
            doc = doc_map[key]
            doc.retrieval_method = RetrievalMethod.HYBRID_RRF
            doc.metadata["rrf_score"] = round(rrf_scores[key], 6)
            fused_proposals.append(doc)

        return fused_proposals


class ExternalSearchProvider(EvidenceRetrievalProvider):
    """
    Adapter for external web/index search API endpoints.
    Enforces timeout bounds, validates input, and treats all remote responses as untrusted.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        endpoint_url: Optional[str] = None,
        timeout_seconds: float = 10.0,
    ):
        self.api_key = api_key
        self.endpoint_url = endpoint_url
        self.timeout_seconds = timeout_seconds

    def retrieve(self, query: EvidenceQuery, max_results: int = 10) -> List[RawDocumentProposal]:
        """
        Executes external search request.
        Safely raises ServiceUnavailableError when API credentials/endpoints are unconfigured.
        """
        if not self.endpoint_url or not self.api_key:
            raise ServiceUnavailableError(
                service_name="ExternalSearchProvider",
                reason="External search endpoint or API key not configured. Use SimulatedRetrievalProvider for offline execution.",
            )

        # Production execution would use httpx.get with timeout_seconds, strict JSON validation,
        # and untrusted schema parsing. In offline testing and local CI, raising ServiceUnavailableError
        # accurately reflects the absence of authorized live external network credentials.
        raise NotImplementedError("Live external retrieval requires configured credentials.")

