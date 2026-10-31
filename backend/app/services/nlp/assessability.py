"""
Claim assessability classification, entity extraction, and categorization service for Veritas.

Differentiates factual assertions from opinions, questions, commands, and fragments.
Extracts named entities and assigns canonical ClaimCategory.
"""

from enum import Enum
from typing import List, Optional, Set, Tuple
import re

from contracts.schemas.models import ClaimCategory


class StatementType(str, Enum):
    FACTUAL_CLAIM = "FACTUAL_CLAIM"
    OPINION = "OPINION"
    QUESTION = "QUESTION"
    COMMAND_OR_REQUEST = "COMMAND_OR_REQUEST"
    INCOMPLETE_OR_FRAGMENT = "INCOMPLETE_OR_FRAGMENT"
    AMBIGUOUS = "AMBIGUOUS"


class AssessabilityClassifier:
    """
    Rule-based, multilingual assessability classifier and entity extractor.
    Enforces that questions, opinions, commands, and greetings are not forced into factual claims.
    """

    # Subjective/Opinion indicators
    OPINION_MARKERS = {
        # English
        "in my opinion", "i believe", "i think", "i feel", "i personally", "personally",
        "best", "worst", "greatest", "terrible", "awful", "beautiful", "ugly",
        "should", "ought to", "must be better", "arguably", "favorite",
        # Hindi / Hinglish
        "mujhe lagta hai", "mere khayal se", "meri raye", "behtareen", "achha hai",
        "bura hai", "sundar", "pasandida",
        # Spanish
        "en mi opinion", "yo creo", "yo pienso", "me parece", "el mejor", "el peor",
        # French
        "a mon avis", "je pense", "je crois", "selon moi", "le meilleur", "le pire",
    }

    # Interrogative markers
    QUESTION_STARTERS = {
        # English
        "what", "why", "how", "when", "where", "who", "whom", "which", "is", "are",
        "was", "were", "do", "does", "did", "can", "could", "will", "would", "has",
        "have", "had", "should",
        # Hindi / Hinglish
        "kya", "kyun", "kyu", "kaise", "kab", "kahan", "kaun", "kisko",
        # Spanish
        "que", "por que", "como", "cuando", "donde", "quien",
        # French
        "quoi", "pourquoi", "comment", "quand", "ou", "qui",
    }

    # Imperative / Command markers
    COMMAND_MARKERS = {
        # English
        "please share", "share this", "retweet", "click here", "subscribe",
        "follow me", "check this out", "watch this", "forward this", "don't forget to",
        # Hindi
        "share karein", "forward karein", "dekho", "dekhiye", "kripya",
        # Spanish
        "comparte", "por favor comparte", "haz clic", "suscribete",
        # French
        "partagez", "veuillez partager", "cliquez", "abonnez-vous",
    }

    # Greeting / Fragment markers
    GREETINGS_AND_FRAGMENTS = {
        "hello", "hi", "hey", "good morning", "good evening", "good night",
        "namaste", "namaskar", "salam", "hola", "bonjour", "salut",
        "thanks", "thank you", "dhanyawad", "shukriya", "gracias", "merci",
        "breaking news", "update", "alert", "urgent", "attention", "wow", "omg",
    }

    # Categorization keywords
    CATEGORY_KEYWORDS = {
        ClaimCategory.POLITICAL: {
            "minister", "president", "government", "election", "parliament", "congress",
            "bjp", "senate", "governor", "policy", "vote", "voters", "candidate", "party",
            "sarkar", "chunav", "neta", "pradhanmantri", "pm", "modi", "biden", "trump",
            "gobierno", "elecciones", "presidente", "politique", "president",
        },
        ClaimCategory.FINANCIAL: {
            "bank", "inflation", "tax", "rbi", "fed", "interest rate", "gdp", "stock",
            "currency", "rupee", "dollar", "market", "economy", "recession", "subsidies",
            "budget", "paisa", "crore", "lakh", "banco", "dolar", "impuesto", "banque",
        },
        ClaimCategory.PUBLIC_HEALTH: {
            "vaccine", "virus", "who", "health", "hospital", "covid", "disease",
            "cancer", "outbreak", "infection", "deaths", "doctors", "medicine",
            "swasthya", "bimari", "dawa", "salud", "vacuna", "sante", "vaccin",
        },
        ClaimCategory.DISASTER: {
            "earthquake", "flood", "tsunami", "cyclone", "fire", "explosion",
            "storm", "casualty", "casualties", "collapse", "destroyed", "landslide",
            "bhukamp", "baadh", "terremoto", "inundacion", "seisme", "inondation",
        },
        ClaimCategory.CELEBRITY_IDENTITY: {
            "actor", "actress", "celebrity", "singer", "player", "cricketer", "star",
            "married", "arrested", "dead", "passed away", "affair", "scandal",
            "film", "movie", "hollywood", "bollywood", "actriz", "chanteur",
        },
    }

    @classmethod
    def classify_statement(cls, text: str) -> Tuple[StatementType, float, Optional[str]]:
        """
        Classifies a candidate statement into StatementType.
        Returns (StatementType, confidence, reason).
        """
        stripped = text.strip()
        if not stripped:
            return (StatementType.INCOMPLETE_OR_FRAGMENT, 0.95, "Empty statement")

        lower = stripped.lower()
        words = [re.sub(r"[^\w]", "", w) for w in lower.split()]
        words = [w for w in words if w]

        # 1. Greeting & conversational pleasantry check (e.g. "Good morning everyone!", "Hello folks", "Namaste")
        for grt in cls.GREETINGS_AND_FRAGMENTS:
            if grt in lower:
                grt_words = set(grt.split())
                non_greeting_words = [
                    w for w in words
                    if w not in grt_words and w not in {"everyone", "all", "folks", "friends", "there", "to", "day", "today"}
                ]
                if len(non_greeting_words) <= 1 and not any(ch.isdigit() for ch in stripped):
                    return (StatementType.INCOMPLETE_OR_FRAGMENT, 0.90, f"Greeting or conversational pleasantry: '{grt}'")

        # 2. Fragment / length checks
        if len(words) < 3:
            return (StatementType.INCOMPLETE_OR_FRAGMENT, 0.85, "Phrase fragment with insufficient sentential structure")

        # 3. Interrogative / Question check
        if stripped.endswith("?") or stripped.endswith("؟"):
            return (StatementType.QUESTION, 0.98, "Interrogative sentence ending with question mark")

        first_word = words[0] if words else ""
        first_two_words = " ".join(words[:2]) if len(words) >= 2 else ""
        if first_word in cls.QUESTION_STARTERS or first_two_words in cls.QUESTION_STARTERS:
            # If it starts with question words and lacks strong declarative indicator
            if not any(marker in lower for marker in ["announced that", "stated that", "proved that", "confirmed that"]):
                return (StatementType.QUESTION, 0.85, "Interrogative structure starting with question word")

        # 4. Imperative / Command check
        for cmd in cls.COMMAND_MARKERS:
            if cmd in lower:
                return (StatementType.COMMAND_OR_REQUEST, 0.90, f"Imperative command marker detected: '{cmd}'")

        # 5. Pure Opinion / Subjective assertion check
        opinion_matches = [op for op in cls.OPINION_MARKERS if op in lower]
        if opinion_matches:
            # Check if opinion is qualified with specific factual data
            has_numbers = bool(re.search(r"\b\d+(?:[\.,]\d+)?\b", stripped))
            if not has_numbers and len(opinion_matches) >= 1:
                return (StatementType.OPINION, 0.85, f"Subjective opinion marker detected: '{opinion_matches[0]}'")

        # 6. Check for factual assertion cues
        has_entities_or_dates = bool(re.search(r"\b(19\d\d|20\d\d|january|february|march|april|may|june|july|august|september|october|november|december|yesterday|today|tomorrow)\b", lower))
        has_numbers_or_stats = bool(re.search(r"\b\d+(?:[\.,]\d+)?%?\b", stripped))
        has_proper_nouns = bool(re.search(r"\b[A-Z][a-z]+\b", stripped[1:]))  # Capitalized words not at start

        # Check verb presence (heuristic)
        verb_cues = {"is", "are", "was", "were", "has", "have", "had", "will", "announced", "reported",
                     "declared", "killed", "passed", "increased", "decreased", "signed", "banned",
                     "hai", "tha", "huye", "kiya", "diya", "gaya", "es", "fue", "ha", "est", "a"}
        has_verb_cue = any(v in words for v in verb_cues) or bool(re.search(r"\w+(?:ed|ing|s)\b", lower))

        if not has_verb_cue and not has_numbers_or_stats:
            return (StatementType.AMBIGUOUS, 0.65, "Lacks recognizable predicate or quantitative assertion")

        # Statement exhibits factual assertion characteristics
        confidence = 0.70
        if has_numbers_or_stats:
            confidence += 0.10
        if has_entities_or_dates:
            confidence += 0.08
        if has_proper_nouns:
            confidence += 0.07

        confidence = min(0.95, round(confidence, 2))
        return (StatementType.FACTUAL_CLAIM, confidence, "Contains assertive factual proposition")

    @classmethod
    def categorize_claim(cls, text: str) -> ClaimCategory:
        """Assigns the most relevant ClaimCategory based on keyword and context cues."""
        lower = text.lower()
        scores = {}
        for cat, keywords in cls.CATEGORY_KEYWORDS.items():
            matches = sum(1 for kw in keywords if re.search(r"\b" + re.escape(kw) + r"\b", lower))
            scores[cat] = matches

        best_cat, best_score = max(scores.items(), key=lambda x: x[1])
        if best_score > 0:
            return best_cat
        return ClaimCategory.GENERAL

    @classmethod
    def extract_entities(cls, text: str) -> List[str]:
        """
        Extracts salient named entities, numerical anchors, dates, and organizations.
        Deterministic regex and pattern based.
        """
        entities: Set[str] = set()

        # 1. Capitalized multi-word sequences (e.g. "Ministry of Health", "World Health Organization")
        cap_sequences = re.findall(r"\b[A-Z][a-z]+(?:\s+(?:of|and|the|for|in|de|del|la|du)\s+[A-Z][a-z]+|\s+[A-Z][a-z]+)+\b", text)
        for seq in cap_sequences:
            if len(seq) > 3:
                entities.add(seq.strip())

        # 2. Standalone capitalized proper nouns not at sentence start
        # Split into sentences to avoid capturing first word
        sentences = re.split(r"[\.!?।]\s*", text)
        for s in sentences:
            words = s.split()
            for w in words[1:]:
                clean_w = re.sub(r"[^\w]", "", w)
                if clean_w and clean_w[0].isupper() and clean_w.isalpha() and len(clean_w) > 2:
                    # Ignore common day names or ordinary words
                    if clean_w.lower() not in {"yesterday", "tomorrow", "today", "monday", "sunday", "the", "and"}:
                        entities.add(clean_w)

        # 3. Currency and numerical statistics (e.g. "$50 billion", "5% increase", "10,000 cases")
        stats = re.findall(r"(?:[\$€£₹]\s*\d+(?:[\.,]\d+)?(?:\s*(?:billion|million|crore|lakh|thousand))?|\b\d+(?:[\.,]\d+)?\s*%\s*(?:increase|decrease|drop|growth)?|\b\d{1,3}(?:,\d{3})+\b)", text, re.IGNORECASE)
        for st in stats:
            entities.add(st.strip())

        # 4. Dates and Years (e.g. "2024", "October 31", "15 August 1947")
        dates = re.findall(r"\b(?:\d{1,2}\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}|\b(?:19|20)\d{2}\b)", text, re.IGNORECASE)
        for dt in dates:
            entities.add(dt.strip())

        # Return sorted list for determinism
        return sorted(list(entities))
