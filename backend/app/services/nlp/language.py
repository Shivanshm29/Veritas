"""
Multilingual language identification and script detection service for Veritas.

Supports Latin (en, es, fr, de), Devanagari (hi), Arabic (ar), Cyrillic (ru),
and CJK (zh), with explicit uncertainty handling, code-switching detection,
and confidence calibration.
"""

from dataclasses import dataclass
from typing import Optional, Set
import re
import unicodedata


@dataclass
class LanguageResult:
    language: str              # ISO 639-1 code (e.g. 'en', 'hi', 'es') or 'und'
    confidence: float          # 0.0 to 1.0 (extraction confidence, not truth)
    script: str                # e.g. 'Latin', 'Devanagari', 'Arabic', 'Mixed', 'Unknown'
    is_reliable: bool          # True if text length and signal exceed reliability threshold
    is_code_switched: bool     # True if significant mixed script/vocabulary detected
    details: Optional[str] = None


class LanguageDetector:
    """
    Deterministic multilingual language and script detector.
    Does not require external network requests or heavyweight model downloads.
    """

    # Common function words / stopwords for Latin-script languages
    STOPWORDS = {
        "en": {
            "the", "be", "to", "of", "and", "a", "in", "that", "have", "i",
            "it", "for", "not", "on", "with", "he", "as", "you", "do", "at",
            "this", "but", "his", "by", "from", "they", "we", "say", "her",
            "she", "or", "an", "will", "my", "one", "all", "would", "there",
            "their", "what", "so", "up", "out", "if", "about", "who", "get",
            "which", "go", "me", "when", "make", "can", "like", "time", "no",
            "just", "him", "know", "take", "people", "into", "year", "your",
            "good", "some", "could", "them", "see", "other", "than", "then",
            "now", "look", "only", "come", "its", "over", "think", "also",
            "back", "after", "use", "two", "how", "our", "work", "first",
            "well", "way", "even", "new", "want", "because", "any", "these",
            "give", "day", "most", "us", "is", "was", "are", "were", "has", "across",
        },
        "es": {
            "el", "la", "de", "que", "y", "a", "en", "un", "ser", "se", "no",
            "haber", "por", "con", "su", "para", "como", "estar", "tener", "le",
            "lo", "lo", "todo", "pero", "mas", "hacer", "o", "poder", "decir",
            "este", "ir", "otro", "ese", "la", "si", "me", "ya", "ver", "porque",
            "dar", "cuando", "el", "muy", "sin", "vez", "mucho", "saber", "que",
            "sobre", "mi", "alguno", "mismo", "yo", "hasta", "ano", "dos",
            "querer", "entre", "asi", "primero", "desde", "grande", "eso", "ni",
            "nos", "llegar", "pasar", "tiempo", "ella", "si", "dia", "uno",
            "bien", "poco", "deber", "entonces", "poner", "cosa", "tanto", "hombre",
            "es", "son", "fue", "ha", "han", "los", "las", "del", "una", "unos",
        },
        "fr": {
            "le", "de", "un", "etre", "et", "a", "il", "avoir", "ne", "je",
            "son", "que", "se", "qui", "ce", "dans", "en", "du", "elle", "au",
            "de", "ce", "le", "pour", "pas", "que", "vous", "par", "sur", "faire",
            "plus", "dire", "me", "on", "mon", "lui", "nous", "comme", "mais",
            "pouvoir", "avec", "tout", "y", "aller", "voir", "en", "bien", "ou",
            "sans", "tu", "ou", "leur", "si", "deux", "meme", "prendre", "meme",
            "votre", "tout", "un", "croire", "falloir", "venir", "grand", "si",
            "est", "sont", "ete", "ont", "les", "des", "une", "dans", "cette",
        },
        "de": {
            "der", "die", "und", "in", "den", "von", "zu", "das", "mit", "sich",
            "des", "auf", "fur", "ist", "im", "dem", "nicht", "ein", "eine",
            "als", "auch", "es", "an", "werden", "aus", "er", "hat", "dass",
            "sie", "nach", "wird", "bei", "einer", "um", "am", "sind", "noch",
            "wie", "einem", "uber", "einen", "so", "zum", "war", "haben", "nur",
            "oder", "aber", "vor", "zur", "bis", "mehr", "durch", "man", "sein",
            "wurde", "sei", "prozent", "hatte", "kann", "gegen", "vom", "können",
        },
        "hi_latin": {  # Hinglish romanized markers
            "hai", "hain", "ki", "ka", "ke", "ko", "se", "aur", "ne", "par",
            "bhi", "yeh", "woh", "kya", "nahi", "kaha", "liya", "diya", "hoga",
            "sarkar", "desh", "karna", "raha", "rahe", "gaya", "gaye", "wale",
        }
    }

    def detect(self, text: str) -> LanguageResult:
        """
        Identifies the primary language and script of the input text.
        Returns LanguageResult with language code, confidence, and reliability.
        """
        if not text or not text.strip():
            return LanguageResult(
                language="und",
                confidence=0.0,
                script="Unknown",
                is_reliable=False,
                is_code_switched=False,
                details="Empty or whitespace-only input",
            )

        stripped = text.strip()
        non_space_chars = [c for c in stripped if not c.isspace() and not c in ".,!?;:-\"'()[]{}"]
        total_chars = len(non_space_chars)

        if total_chars == 0:
            return LanguageResult(
                language="und",
                confidence=0.0,
                script="Unknown",
                is_reliable=False,
                is_code_switched=False,
                details="No alphanumeric characters present",
            )

        # Count character scripts
        devanagari_count = 0
        arabic_count = 0
        cyrillic_count = 0
        cjk_count = 0
        latin_count = 0

        for char in non_space_chars:
            cp = ord(char)
            if 0x0900 <= cp <= 0x097F or 0xA8E0 <= cp <= 0xA8FF:
                devanagari_count += 1
            elif 0x0600 <= cp <= 0x06FF or 0x0750 <= cp <= 0x077F:
                arabic_count += 1
            elif 0x0400 <= cp <= 0x04FF:
                cyrillic_count += 1
            elif (0x4E00 <= cp <= 0x9FFF or 0x3400 <= cp <= 0x4DBF or
                  0x20000 <= cp <= 0x2A6DF or 0x3040 <= cp <= 0x30FF):
                cjk_count += 1
            elif ('A' <= char <= 'Z') or ('a' <= char <= 'z') or (0x00C0 <= cp <= 0x024F):
                latin_count += 1

        # Check script dominance
        script_counts = {
            "Devanagari": devanagari_count,
            "Arabic": arabic_count,
            "Cyrillic": cyrillic_count,
            "CJK": cjk_count,
            "Latin": latin_count,
        }
        dominant_script, max_chars = max(script_counts.items(), key=lambda x: x[1])

        # Short input penalty
        is_short = total_chars < 15

        # Code-switching check (e.g. Devanagari + Latin)
        non_zero_scripts = [s for s, count in script_counts.items() if count > 5]
        is_code_switched = len(non_zero_scripts) > 1

        # Script-to-language mappings for unambiguous scripts
        if dominant_script == "Devanagari" and devanagari_count / total_chars > 0.4:
            conf = min(1.0, (devanagari_count / total_chars) * (0.6 if is_short else 0.95))
            return LanguageResult(
                language="hi",
                confidence=round(conf, 2),
                script="Devanagari",
                is_reliable=not is_short,
                is_code_switched=is_code_switched,
                details="Devanagari script detected (Hindi / Indic)",
            )

        if dominant_script == "Arabic" and arabic_count / total_chars > 0.4:
            conf = min(1.0, (arabic_count / total_chars) * (0.6 if is_short else 0.95))
            return LanguageResult(
                language="ar",
                confidence=round(conf, 2),
                script="Arabic",
                is_reliable=not is_short,
                is_code_switched=is_code_switched,
                details="Arabic script detected",
            )

        if dominant_script == "Cyrillic" and cyrillic_count / total_chars > 0.4:
            conf = min(1.0, (cyrillic_count / total_chars) * (0.6 if is_short else 0.95))
            return LanguageResult(
                language="ru",
                confidence=round(conf, 2),
                script="Cyrillic",
                is_reliable=not is_short,
                is_code_switched=is_code_switched,
                details="Cyrillic script detected (Russian)",
            )

        if dominant_script == "CJK" and cjk_count / total_chars > 0.4:
            conf = min(1.0, (cjk_count / total_chars) * (0.6 if is_short else 0.95))
            return LanguageResult(
                language="zh",
                confidence=round(conf, 2),
                script="CJK",
                is_reliable=not is_short,
                is_code_switched=is_code_switched,
                details="CJK Ideographs detected (Chinese)",
            )

        # Latin script disambiguation
        if dominant_script == "Latin" and latin_count > 0:
            words = [re.sub(r"[^\w]", "", w.lower()) for w in stripped.split()]
            words = [w for w in words if w]
            word_set = set(words)

            scores = {}
            for lang, stops in self.STOPWORDS.items():
                match_count = len(word_set & stops)
                scores[lang] = match_count

            best_lang, best_score = max(scores.items(), key=lambda x: x[1])

            # Check for Hinglish (Latin script Hindi markers)
            if best_lang == "hi_latin" and best_score >= 2:
                conf = 0.70 if is_short else 0.85
                return LanguageResult(
                    language="hi",
                    confidence=conf,
                    script="Latin",
                    is_reliable=True,
                    is_code_switched=True,
                    details="Romanized Hindi / Hinglish detected",
                )

            if best_score > 0:
                sorted_scores = sorted(scores.values(), reverse=True)
                second_score = sorted_scores[1] if len(sorted_scores) > 1 else 0
                margin = best_score - second_score
                conf = min(0.98, 0.65 + (min(best_score, 8) / 8.0) * 0.25 + (0.05 if margin >= 2 else 0.0))
                if is_short:
                    conf = min(conf, 0.75)
                return LanguageResult(
                    language=best_lang,
                    confidence=round(conf, 2),
                    script="Latin",
                    is_reliable=not is_short and best_score >= 2,
                    is_code_switched=is_code_switched,
                    details=f"Latin script identified via vocabulary frequency ({best_lang})",
                )

            # Default for Latin without distinctive stopwords
            return LanguageResult(
                language="en",  # English is standard default for Latin in absence of distinctive stops
                confidence=0.45 if is_short else 0.60,
                script="Latin",
                is_reliable=False,
                is_code_switched=is_code_switched,
                details="Latin script with ambiguous or sparse vocabulary; default en",
            )

        # Ambiguous / Mixed / Undetermined
        return LanguageResult(
            language="und",
            confidence=0.10,
            script="Mixed" if is_code_switched else "Unknown",
            is_reliable=False,
            is_code_switched=is_code_switched,
            details="Unable to determine language with sufficient confidence",
        )
