"""
Source credibility and domain reliability evaluation service for Veritas.

Provides transparent, heuristic reliability signals for external sources.
Guarantees separation between source credibility and claim truth.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional
from urllib.parse import urlparse


class DomainCategory(str, Enum):
    GOVERNMENT_OFFICIAL = "GOVERNMENT_OFFICIAL"
    ACADEMIC_RESEARCH = "ACADEMIC_RESEARCH"
    FACT_CHECKING_ORGANIZATION = "FACT_CHECKING_ORGANIZATION"
    ESTABLISHED_NEWS = "ESTABLISHED_NEWS"
    COMMERCIAL_MEDIA = "COMMERCIAL_MEDIA"
    USER_GENERATED_CONTENT = "USER_GENERATED_CONTENT"
    UNKNOWN_OR_UNCLASSIFIED = "UNKNOWN_OR_UNCLASSIFIED"


@dataclass
class SourceCredibilityResult:
    """
    Transparent evaluation of a source's institutional credibility.
    Explicitly labeled as an uncalibrated heuristic indicator, not a truth measure.
    """
    domain: str
    reliability_score: Optional[float]  # 0.0 to 1.0, or None if uncertain/insufficient info
    category: DomainCategory
    is_calibrated_probability: bool     # Always False for heuristic scores
    rationale: str
    limitations_disclaimer: str = (
        "Heuristic domain credibility score. High credibility does not establish that a specific claim "
        "is true, nor does low or unclassified credibility prove that a claim is false."
    )


class SourceCredibilityEvaluator:
    """
    Rule-based source reliability evaluator.
    Preserves epistemic uncertainty for unindexed or novel domains.
    """

    # Domain classifications
    GOV_TLDS = {".gov", ".mil", ".gov.in", ".gov.uk", ".gov.au", ".nic.in"}
    EDU_TLDS = {".edu", ".ac.uk", ".edu.in", ".ac.in"}
    INT_DOMAINS = {"who.int", "un.org", "unesco.org", "imf.org", "worldbank.org", "wmo.int"}

    FACT_CHECK_DOMAINS = {
        "factcheck.org", "politifact.com", "snopes.com", "fullfact.org",
        "altnews.in", "boomlive.in", "vishvasnews.com", "leadstories.com",
    }

    ESTABLISHED_NEWS_DOMAINS = {
        "reuters.com", "apnews.com", "bbc.com", "bbc.co.uk", "afp.com",
        "aljazeera.com", "thehindu.com", "indianexpress.com", "nytimes.com",
        "washingtonpost.com", "theguardian.com", "lemonde.fr", "dw.com",
    }

    UGC_PLATFORMS = {
        "twitter.com", "x.com", "facebook.com", "instagram.com", "tiktok.com",
        "reddit.com", "youtube.com", "telegram.org", "threads.net", "whatsapp.com",
    }

    @classmethod
    def evaluate(cls, url_or_domain: str) -> SourceCredibilityResult:
        """
        Evaluates source reliability from URL or domain.
        Returns SourceCredibilityResult with explicit heuristic disclosure.
        """
        if not url_or_domain or not url_or_domain.strip():
            return SourceCredibilityResult(
                domain="",
                reliability_score=None,
                category=DomainCategory.UNKNOWN_OR_UNCLASSIFIED,
                is_calibrated_probability=False,
                rationale="Empty or invalid source domain provided.",
            )

        # Extract normalized hostname
        parsed = urlparse(url_or_domain if "://" in url_or_domain else f"https://{url_or_domain}")
        domain = (parsed.hostname or url_or_domain).lower()
        if domain.startswith("www."):
            domain = domain[4:]

        # 1. International organizations
        if domain in cls.INT_DOMAINS:
            return SourceCredibilityResult(
                domain=domain,
                reliability_score=0.95,
                category=DomainCategory.GOVERNMENT_OFFICIAL,
                is_calibrated_probability=False,
                rationale="Intergovernmental treaty organization or multilateral standard-setting institution.",
            )

        # 2. Government / Military official TLDs
        if any(domain == tld.lstrip(".") or domain.endswith(tld) for tld in cls.GOV_TLDS):
            return SourceCredibilityResult(
                domain=domain,
                reliability_score=0.90,
                category=DomainCategory.GOVERNMENT_OFFICIAL,
                is_calibrated_probability=False,
                rationale="Official government or public administrative entity domain.",
            )

        # 3. Academic / Research institutions
        if any(domain == tld.lstrip(".") or domain.endswith(tld) for tld in cls.EDU_TLDS):
            return SourceCredibilityResult(
                domain=domain,
                reliability_score=0.88,
                category=DomainCategory.ACADEMIC_RESEARCH,
                is_calibrated_probability=False,
                rationale="Accredited higher-education or academic research institution domain.",
            )

        # 4. Verified fact-checking organizations (IFCN / certified)
        if domain in cls.FACT_CHECK_DOMAINS:
            return SourceCredibilityResult(
                domain=domain,
                reliability_score=0.92,
                category=DomainCategory.FACT_CHECKING_ORGANIZATION,
                is_calibrated_probability=False,
                rationale="Recognized professional fact-checking and forensic debriefing organization.",
            )

        # 5. Established global and national wire/news agencies
        if domain in cls.ESTABLISHED_NEWS_DOMAINS:
            return SourceCredibilityResult(
                domain=domain,
                reliability_score=0.85,
                category=DomainCategory.ESTABLISHED_NEWS,
                is_calibrated_probability=False,
                rationale="Established national or international journalistic news publisher.",
            )

        # 6. User-generated content / Social media platforms
        if domain in cls.UGC_PLATFORMS:
            return SourceCredibilityResult(
                domain=domain,
                reliability_score=0.40,
                category=DomainCategory.USER_GENERATED_CONTENT,
                is_calibrated_probability=False,
                rationale="Social network or user-generated publishing platform; content reflects unvetted user assertions.",
            )

        # 7. Unclassified or novel domain
        return SourceCredibilityResult(
            domain=domain,
            reliability_score=0.60,
            category=DomainCategory.UNKNOWN_OR_UNCLASSIFIED,
            is_calibrated_probability=False,
            rationale="Unclassified open-web domain; neutral baseline credibility applied with high uncertainty.",
        )
