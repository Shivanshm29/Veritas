"""
Pydantic schemas for Mode A (URL-Based Ingestion via oEmbed) and
Mode B (Real-Time Live Social Feed Monitoring & Early Warning).
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class UrlAuditRequest(BaseModel):
    """Request to audit a specific social media or web URL (Mode A)."""
    url: str = Field(..., min_length=5, description="Social media or web URL to audit")
    investigation_id: Optional[str] = Field(None, description="Optional custom investigation ID (inv_<uuid4>)")


class FeedItem(BaseModel):
    """A post ingested from live social streams (Mode B)."""
    id: str = Field(..., description="Unique post ID (e.g. post_xyz or red_xyz)")
    platform: str = Field(..., description="Platform name: X / Twitter, Reddit, Telegram, YouTube, TikTok, Bluesky")
    author: str = Field(..., description="Author display name")
    author_handle: Optional[str] = Field(None, description="Author username or channel handle")
    title: str = Field(..., description="Headline or post title")
    content: str = Field(..., description="Full post text / claim content")
    media_url: Optional[str] = Field(None, description="Direct URL to associated image or video thumbnail")
    media_type: str = Field("text", description="image, video, audio, or text")
    virality_score: float = Field(0.0, ge=0.0, le=1.0, description="Normalized virality velocity (0.0 to 1.0)")
    shares_per_minute: int = Field(0, description="Estimated share or repost acceleration per minute")
    total_impressions: int = Field(0, description="Total views or estimated audience reach")
    is_viral_spike: bool = Field(False, description="True if post exceeds velocity threshold for urgent alert")
    posted_at: str = Field(..., description="ISO 8601 timestamp of post")
    source_url: str = Field(..., description="Canonical source permalink")
    html_embed: Optional[str] = Field(None, description="oEmbed rich HTML embed if available")


class AuditFeedItemRequest(BaseModel):
    """Request to trigger full forensic & fact audit on an item from the live feed."""
    item_id: str
    feed_item: Optional[FeedItem] = None


class ResolvedUrlMetadata(BaseModel):
    """Parsed metadata from oEmbed and OpenGraph URL extraction."""
    url: str
    platform: str
    title: Optional[str] = None
    author_name: Optional[str] = None
    author_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    html_embed: Optional[str] = None
    description: Optional[str] = None
    media_type: str = "text"


class UnifiedPipelineResponse(BaseModel):
    """Consolidated investigation output unifying forensics, claims, and provenance."""
    investigation_id: str
    status: str
    mode: str = Field("URL_AUDIT", description="URL_AUDIT (Mode A) or LIVE_FEED_RADAR (Mode B)")
    source_url: Optional[str] = None
    source_platform: Optional[str] = None
    post_metadata: Optional[Dict[str, Any]] = None
    claims: List[Dict[str, Any]] = Field(default_factory=list)
    claim_assessments: List[Dict[str, Any]] = Field(default_factory=list)
    forensic_findings: Optional[Dict[str, Any]] = None
    provenance: Optional[Dict[str, Any]] = None
    verdict_summary: str = Field(..., description="Overall human-readable investigation conclusion")
    execution_time_ms: int = Field(0)
