"""
Feed & Social Monitoring API Endpoints.

Supports:
- Mode A: URL-Based Investigation via oEmbed and OpenGraph (POST /api/v1/feed/audit-url)
- Mode B: Live Social Feed Monitoring, Virality Tracking & Early Warning (GET /api/v1/feed/live)
- Automated pipeline execution linking Forensics, Claim Verification, and Provenance.
"""

import logging
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query, status

from backend.app.schemas.feed import (
    AuditFeedItemRequest,
    FeedItem,
    ResolvedUrlMetadata,
    UnifiedPipelineResponse,
    UrlAuditRequest,
)
from backend.app.services.pipeline import unified_pipeline
from backend.app.services.social_feed.oembed import OEmbedResolver
from backend.app.services.social_feed.stream_monitor import live_feed_monitor

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/feed", tags=["Social Feeds & Early Warning"])
oembed_resolver = OEmbedResolver()
TEMP_UPLOADS = Path("artifacts/.uploads")


# ── Mode A: URL-Based Investigation (oEmbed) ─────────────────────────────────

@router.post(
    "/resolve-url",
    response_model=ResolvedUrlMetadata,
    summary="Mode A: Resolve social media URL via oEmbed",
    description="Extracts rich post claims, author information, and thumbnails from Twitter/X, YouTube, Reddit, TikTok.",
)
async def resolve_social_url(request: UrlAuditRequest) -> ResolvedUrlMetadata:
    if not request.url or not request.url.startswith("http"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A valid HTTP/HTTPS URL is required.",
        )
    return await oembed_resolver.resolve_url(request.url)


@router.post(
    "/audit-url",
    response_model=UnifiedPipelineResponse,
    summary="Mode A: Full automated verification of a social media or web URL",
    description=(
        "Pastes any social media URL (Twitter/X, YouTube, Reddit, TikTok, News). "
        "The engine resolves post claims via oEmbed, downloads or synthesizes the media asset, "
        "runs image forensics (ELA, CopyMove, Sensor noise), extracts and verifies claims against ground-truth evidence, "
        "and checks historical provenance."
    ),
)
async def audit_url_endpoint(request: UrlAuditRequest) -> UnifiedPipelineResponse:
    if not request.url or not request.url.startswith("http"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A valid HTTP/HTTPS URL is required.",
        )

    # 1. Resolve oEmbed & metadata
    metadata = await oembed_resolver.resolve_url(request.url)
    text_content = metadata.description or metadata.title or f"Assertion from {metadata.platform} under audit."

    # 2. Download thumbnail or synthesize evidence capture canvas
    media_path = await oembed_resolver.fetch_media_to_local_file(
        media_url=metadata.thumbnail_url,
        output_dir=TEMP_UPLOADS,
        fallback_text=text_content,
        platform_name=metadata.platform,
    )

    # 3. Execute unified investigation pipeline
    try:
        response = await unified_pipeline.execute_investigation(
            claim_text=text_content,
            media_path=media_path,
            source_url=request.url,
            source_platform=metadata.platform,
            post_metadata=metadata.model_dump(),
            investigation_id=request.investigation_id,
            mode="URL_AUDIT",
        )
        return response
    finally:
        # Clean up temporary staging file
        if media_path and media_path.exists():
            media_path.unlink(missing_ok=True)


# ── Mode B: Live Feed Monitoring & Early Warning Radar ────────────────────────

@router.get(
    "/live",
    response_model=List[FeedItem],
    summary="Mode B: Stream live social posts with virality tracking",
    description="Returns real-time feed items across Twitter/X, Reddit, Telegram with viral velocity and spike indicators.",
)
async def get_live_social_feed(
    include_live_network: bool = Query(True, description="Fetch real public Reddit posts without API keys")
) -> List[FeedItem]:
    return await live_feed_monitor.get_live_stream(include_live_network=include_live_network)


@router.post(
    "/audit-post",
    response_model=UnifiedPipelineResponse,
    summary="Mode B: One-click audit of an emerging post from the live stream",
    description="Takes an item from the live stream and immediately runs full forensics and fact-verification.",
)
async def audit_live_feed_post(request: AuditFeedItemRequest) -> UnifiedPipelineResponse:
    post = request.feed_item or live_feed_monitor.get_item_by_id(request.item_id)
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Feed item '{request.item_id}' not found.",
        )

    text_content = post.content or post.title

    media_path = await oembed_resolver.fetch_media_to_local_file(
        media_url=post.media_url,
        output_dir=TEMP_UPLOADS,
        fallback_text=text_content,
        platform_name=post.platform,
    )

    try:
        response = await unified_pipeline.execute_investigation(
            claim_text=text_content,
            media_path=media_path,
            source_url=post.source_url,
            source_platform=post.platform,
            post_metadata=post.model_dump(),
            mode="LIVE_FEED_RADAR",
        )
        return response
    finally:
        if media_path and media_path.exists():
            media_path.unlink(missing_ok=True)


@router.post(
    "/trigger-spike",
    response_model=FeedItem,
    summary="Mode B: Trigger simulated breaking viral spike (Demo / Judging)",
    description="Injects a high-velocity breaking deepfake claim at the top of the live radar stream.",
)
async def trigger_viral_spike_endpoint(
    custom_claim: Optional[str] = Query(None, description="Optional custom breaking claim text")
) -> FeedItem:
    return live_feed_monitor.trigger_viral_spike(custom_claim=custom_claim)
