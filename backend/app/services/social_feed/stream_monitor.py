"""
Live Social Feed Monitor and Early Warning Service for Mode B.

Continuously monitors public feeds and simulates high-velocity viral
misinformation spikes across X/Twitter, Telegram, Reddit, and YouTube.
"""

from datetime import datetime, timezone
import logging
from typing import List, Optional
import uuid

import httpx

from backend.app.schemas.feed import FeedItem

logger = logging.getLogger(__name__)

# Pre-seeded realistic viral claims spanning deepfakes and geopolitical assertions
INITIAL_LIVE_FEED_ITEMS = [
    {
        "id": "post_live_x_001",
        "platform": "X / Twitter",
        "author": "Geopolitics Wire",
        "author_handle": "@GeoWireGlobal",
        "title": "Breaking: Alleged leaked diplomatic audio reveals emergency defense alliance talks",
        "content": "A leaked high-level audio recording allegedly captures foreign ministry officials agreeing to secret bilateral defense terms ahead of the regional summit.",
        "media_url": "https://picsum.photos/seed/geopolitics_leak/800/450.jpg",
        "media_type": "audio",
        "virality_score": 0.94,
        "shares_per_minute": 4200,
        "total_impressions": 184000,
        "is_viral_spike": True,
        "posted_at": datetime.now(timezone.utc).isoformat(),
        "source_url": "https://twitter.com/GeoWireGlobal/status/1789012345678901234",
    },
    {
        "id": "post_live_tg_002",
        "platform": "Telegram",
        "author": "Global Citizen Intel",
        "author_handle": "@CitizenIntelLive",
        "title": "Viral image claiming flooded subway systems after unprecedented monsoon rainfall",
        "content": "Citizens circulate dramatic photos showing metro station platforms completely submerged under 6 feet of water, claiming city infrastructure failed.",
        "media_url": "https://picsum.photos/seed/flooded_subway/800/600.jpg",
        "media_type": "image",
        "virality_score": 0.81,
        "shares_per_minute": 2150,
        "total_impressions": 92000,
        "is_viral_spike": False,
        "posted_at": datetime.now(timezone.utc).isoformat(),
        "source_url": "https://t.me/CitizenIntelLive/4912",
    },
    {
        "id": "post_live_yt_003",
        "platform": "YouTube",
        "author": "Health Today Channel",
        "author_handle": "@HealthTodayGlobal",
        "title": "Deepfake video of WHO director recommending banned synthetic wellness supplements",
        "content": "Video circulating on video platforms depicts World Health Organization leadership endorsing untested chemical concoctions for immune enhancement.",
        "media_url": "https://picsum.photos/seed/who_director_speech/800/450.jpg",
        "media_type": "video",
        "virality_score": 0.89,
        "shares_per_minute": 3600,
        "total_impressions": 310000,
        "is_viral_spike": True,
        "posted_at": datetime.now(timezone.utc).isoformat(),
        "source_url": "https://youtube.com/watch?v=mock_who_deepfake_leak",
    },
    {
        "id": "post_live_rd_004",
        "platform": "Reddit",
        "author": "u/MarketDisruptor",
        "author_handle": "u/MarketDisruptor",
        "title": "Central Bank secretly planned unexpected emergency 150-basis-point interest rate drop",
        "content": "Reddit financial forums are circulating leaked meeting minutes stating the central banking committee secretly voted to slash benchmark rates tonight.",
        "media_url": None,
        "media_type": "text",
        "virality_score": 0.72,
        "shares_per_minute": 1420,
        "total_impressions": 48000,
        "is_viral_spike": False,
        "posted_at": datetime.now(timezone.utc).isoformat(),
        "source_url": "https://reddit.com/r/economics/comments/leak_central_bank_rates",
    },
]


class LiveFeedMonitorService:
    """Manages real-time social feed ingestion, virality tracking, and spike simulation."""

    def __init__(self):
        self._items: list[FeedItem] = [FeedItem(**item) for item in INITIAL_LIVE_FEED_ITEMS]

    async def fetch_live_reddit_public(self, subreddit: str = "worldnews", limit: int = 5) -> list[FeedItem]:
        """Polls public Reddit JSON feed (zero API keys required) for real breaking news items."""
        real_items: list[FeedItem] = []
        url = f"https://www.reddit.com/r/{subreddit}/new.json?limit={limit}"
        headers = {"User-Agent": "PramaanLiveMonitor/1.0"}

        try:
            async with httpx.AsyncClient(timeout=4.0) as client:
                resp = await client.get(url, headers=headers)
                if resp.status_code == 200:
                    data = resp.json()
                    children = data.get("data", {}).get("children", [])
                    for child in children:
                        post_data = child.get("data", {})
                        title = post_data.get("title", "")
                        if not title:
                            continue

                        # Check for thumbnail/image
                        thumb = post_data.get("thumbnail")
                        media_url = thumb if thumb and thumb.startswith("http") else None
                        score = post_data.get("score", 1)
                        num_comments = post_data.get("num_comments", 0)

                        velocity = min(5000, (score + num_comments) * 15)
                        virality_score = round(min(1.0, velocity / 4000.0), 2)

                        item = FeedItem(
                            id=f"red_{post_data.get('id', uuid.uuid4().hex[:6])}",
                            platform="Reddit",
                            author=post_data.get("author", "anonymous"),
                            author_handle=f"u/{post_data.get('author', 'user')}",
                            title=title,
                            content=post_data.get("selftext") or title,
                            media_url=media_url,
                            media_type="image" if media_url else "text",
                            virality_score=virality_score,
                            shares_per_minute=velocity,
                            total_impressions=(score + num_comments) * 250,
                            is_viral_spike=virality_score > 0.75,
                            posted_at=datetime.fromtimestamp(post_data.get("created_utc", 0), tz=timezone.utc).isoformat(),
                            source_url=f"https://reddit.com{post_data.get('permalink', '')}",
                        )
                        real_items.append(item)
        except Exception as exc:
            logger.debug(f"Public Reddit live poll bypassed: {exc}")

        return real_items

    async def get_live_stream(self, include_live_network: bool = True) -> list[FeedItem]:
        """Returns the aggregate live stream ordered by virality and recency."""
        current_list = list(self._items)

        if include_live_network:
            try:
                live_reddit = await self.fetch_live_reddit_public(limit=3)
                # Deduplicate by ID
                existing_ids = {i.id for i in current_list}
                for item in live_reddit:
                    if item.id not in existing_ids:
                        current_list.append(item)
            except Exception:
                pass

        # Sort with viral spikes at the top, then by virality_score
        current_list.sort(key=lambda x: (x.is_viral_spike, x.virality_score), reverse=True)
        return current_list

    def trigger_viral_spike(self, custom_claim: Optional[str] = None) -> FeedItem:
        """Injects a simulated high-velocity breaking deepfake claim (for live demos/evaluations)."""
        spike_id = f"spike_{uuid.uuid4().hex[:6]}"
        now = datetime.now(timezone.utc).isoformat()

        content = custom_claim or (
            "URGENT: High-fidelity deepfake broadcast depicting central election committee "
            "allegedly announcing emergency voting postponement due to cyber infrastructure breach."
        )

        spike_item = FeedItem(
            id=spike_id,
            platform="X / Twitter",
            author="Flash News Network",
            author_handle="@FlashNewsRadar",
            title="BREAKING: Election committee voting postponement broadcast circulating rapidly",
            content=content,
            media_url="https://picsum.photos/seed/election_deepfake_spike/800/450.jpg",
            media_type="video",
            virality_score=0.98,
            shares_per_minute=6800,
            total_impressions=420000,
            is_viral_spike=True,
            posted_at=now,
            source_url="https://twitter.com/FlashNewsRadar/status/viral_spike_election",
        )

        # Prepend to the active list
        self._items.insert(0, spike_item)
        return spike_item

    def get_item_by_id(self, item_id: str) -> Optional[FeedItem]:
        return next((i for i in self._items if i.id == item_id), None)


# Singleton monitor instance
live_feed_monitor = LiveFeedMonitorService()
