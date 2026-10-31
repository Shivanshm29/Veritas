"""
Evidence and source document deduplication service for Veritas.

Detects exact hash collisions and near-duplicate syndicated reports to prevent
duplicate coverage from falsely magnifying independent evidentiary corroboration.
"""

from dataclasses import dataclass, field
import hashlib
import re
from typing import Dict, List, Optional, Set, Tuple


@dataclass
class DeduplicatedItem:
    item_id: str
    is_duplicate: bool
    duplicate_of_id: Optional[str] = None
    similarity_score: float = 0.0
    reason: str = "Unique"




class EvidenceDeduplicator:
    """
    Identifies exact hash duplicates and near-duplicate syndicated wire stories.
    """

    @staticmethod
    def compute_sha256(text: str) -> str:
        """Computes deterministic lowercase 64-char hex SHA-256 of text."""
        return hashlib.sha256(text.encode("utf-8")).hexdigest()

    @staticmethod
    def _tokenize(text: str) -> Set[str]:
        """Extracts lowercase alpha tokens for Jaccard similarity."""
        return set(re.findall(r"\b[a-zA-Z0-9_\u0900-\u097F]{3,}\b", text.lower()))

    @classmethod
    def compute_jaccard_similarity(cls, text_a: str, text_b: str) -> float:
        """Computes token Jaccard similarity between two texts."""
        set_a = cls._tokenize(text_a)
        set_b = cls._tokenize(text_b)
        if not set_a or not set_b:
            return 0.0
        intersection = len(set_a & set_b)
        union = len(set_a | set_b)
        return round(intersection / union, 4)

    @classmethod
    def deduplicate_documents(
        cls,
        documents: List[dict],
        jaccard_threshold: float = 0.80,
    ) -> Tuple[List[dict], List[dict], int]:
        """
        Deduplicates a list of document dicts (each having 'id', 'content' or 'content_snippet').
        Returns (unique_documents, duplicate_documents, duplicate_count).
        """
        unique_docs: List[dict] = []
        duplicate_docs: List[dict] = []
        seen_hashes: Dict[str, str] = {}  # sha256 -> doc_id
        seen_texts: List[Tuple[str, str, Set[str]]] = []  # (doc_id, text, token_set)

        for doc in documents:
            doc_id = doc.get("id", "")
            content = doc.get("content") or doc.get("content_snippet", "")
            content_hash = doc.get("content_sha256") or cls.compute_sha256(content)
            doc["content_sha256"] = content_hash

            # 1. Exact SHA-256 match
            if content_hash in seen_hashes:
                doc["is_duplicate"] = True
                doc["duplicate_of_id"] = seen_hashes[content_hash]
                doc["duplicate_type"] = "EXACT_HASH_MATCH"
                duplicate_docs.append(doc)
                continue

            # 2. Near-duplicate syndicated story match
            doc_tokens = cls._tokenize(content)
            is_near_dup = False
            for seen_id, _, seen_toks in seen_texts:
                if not doc_tokens or not seen_toks:
                    continue
                jaccard = len(doc_tokens & seen_toks) / len(doc_tokens | seen_toks)
                if jaccard >= jaccard_threshold:
                    doc["is_duplicate"] = True
                    doc["duplicate_of_id"] = seen_id
                    doc["duplicate_type"] = "SYNDICATED_WIRE_RECOPY"
                    doc["similarity_score"] = round(jaccard, 4)
                    duplicate_docs.append(doc)
                    is_near_dup = True
                    break

            if not is_near_dup:
                doc["is_duplicate"] = False
                doc["duplicate_of_id"] = None
                doc["duplicate_type"] = None
                unique_docs.append(doc)
                seen_hashes[content_hash] = doc_id
                seen_texts.append((doc_id, content, doc_tokens))

        return unique_docs, duplicate_docs, len(duplicate_docs)

