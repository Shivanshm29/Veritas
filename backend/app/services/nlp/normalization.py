"""
Deterministic text normalization and span alignment service for Veritas.

Provides Unicode NFC normalization, whitespace normalization, control character
sanitization, and exact character-span mapping into original source text.
"""

from dataclasses import dataclass
from typing import Optional, Tuple
import unicodedata
import re


@dataclass
class NormalizationResult:
    original_text: str
    normalized_text: str
    char_count_original: int
    char_count_normalized: int
    was_modified: bool


class TextNormalizer:
    """
    Deterministic text normalizer preserving semantic integrity, non-Latin scripts,
    numbers, negation, entities, and emoji.
    """

    @staticmethod
    def normalize(text: str) -> NormalizationResult:
        """
        Applies Unicode NFC normalization, control character removal,
        and whitespace regularization while preserving original text.
        """
        if not text:
            return NormalizationResult(
                original_text="",
                normalized_text="",
                char_count_original=0,
                char_count_normalized=0,
                was_modified=False,
            )

        # 1. Unicode NFC Normalization (canonical decomposition followed by canonical composition)
        nfc_text = unicodedata.normalize("NFC", text)

        # 2. Filter dangerous / unprintable control characters (retain \t, \n, \r)
        sanitized_chars = []
        for ch in nfc_text:
            cp = ord(ch)
            if cp < 32 and ch not in ("\t", "\n", "\r"):
                continue  # strip non-printable ASCII control chars
            if cp == 127:
                continue  # strip DEL
            sanitized_chars.append(ch)
        sanitized = "".join(sanitized_chars)

        # 3. Regularize whitespace: collapse multiple horizontal spaces/tabs, keep single space
        # Preserve newlines for paragraph/sentence boundary segmentation
        lines = sanitized.splitlines()
        normalized_lines = []
        for line in lines:
            collapsed = re.sub(r"[ \t]+", " ", line).strip()
            if collapsed:
                normalized_lines.append(collapsed)

        normalized = "\n".join(normalized_lines)

        return NormalizationResult(
            original_text=text,
            normalized_text=normalized,
            char_count_original=len(text),
            char_count_normalized=len(normalized),
            was_modified=(normalized != text),
        )

    @staticmethod
    def find_span_in_original(original_text: str, target_phrase: str) -> Optional[Tuple[int, int]]:
        """
        Locates the exact (start_char, end_char) byte/character offsets of target_phrase
        within original_text.

        Returns (start, end) where original_text[start:end] contains the phrase,
        or None if alignment cannot be reliably determined.
        """
        if not original_text or not target_phrase:
            return None

        # 1. Direct exact match
        idx = original_text.find(target_phrase)
        if idx != -1:
            return (idx, idx + len(target_phrase))

        # 2. Case-insensitive exact match
        lower_orig = original_text.lower()
        lower_target = target_phrase.lower()
        idx = lower_orig.find(lower_target)
        if idx != -1:
            return (idx, idx + len(target_phrase))

        # 3. Whitespace-flexible fuzzy regex match
        # Escape special regex chars in target words and match across any whitespace
        words = target_phrase.split()
        if len(words) >= 2:
            pattern_parts = [re.escape(w) for w in words]
            flexible_pattern = r"\s+".join(pattern_parts)
            match = re.search(flexible_pattern, original_text, re.IGNORECASE)
            if match:
                return (match.start(), match.end())

        # Exact alignment unavailable; do NOT fabricate offsets
        return None
