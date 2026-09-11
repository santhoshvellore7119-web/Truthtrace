"""
Social Media Ingestion Agent for TruthTrace (Phase 3).
Hunts for claim appearances across Reddit and public Telegram channels.
"""
from .base_agent import BaseAgent, AgentResult
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
import asyncio
import httpx
import logging
import os
import re

logger = logging.getLogger(__name__)

class SocialHunterAgent(BaseAgent):
    """
    Ingests social media mentions from Reddit and public Telegram channels.
    """
    def __init__(self):
        super().__init__("SocialHunter")
        self.reddit_client_id = os.getenv("REDDIT_CLIENT_ID")
        self.reddit_client_secret = os.getenv("REDDIT_CLIENT_SECRET")
        self.user_agent = os.getenv("REDDIT_USER_AGENT", "TruthTrace-OSINT/1.0")
        self.timeout = float(os.getenv("TRUTHTRACE_SOCIAL_TIMEOUT", "3.0"))

    async def execute(self, input_data: Dict[str, Any]) -> AgentResult:
        """
        Input: {'claims': List[str]} or {'claim': str}
        Output: {'social_provenance': List[Dict], 'social_claims': List[Dict]}
        """
        try:
            claims = input_data.get('claims', [])
            if not claims and 'claim' in input_data:
                claims = [input_data['claim']]

            if not claims:
                return AgentResult(success=False, error="No claims provided to Social Hunter")

            all_social_provenance = []

            async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
                for idx, claim in enumerate(claims):
                    tasks = [
                        self._search_reddit(client, claim),
                        self._search_telegram_public(client, claim)
                    ]
                    reddit_posts, telegram_posts = await asyncio.gather(*tasks, return_exceptions=True)

                    r_items = reddit_posts if isinstance(reddit_posts, list) else []
                    t_items = telegram_posts if isinstance(telegram_posts, list) else []

                    for item in r_items:
                        all_social_provenance.append({
                            "claim": claim,
                            "source_type": "reddit",
                            "platform": f"Reddit (r/{item.get('subreddit', 'all')})",
                            "title": item.get("title", ""),
                            "url": item.get("url", ""),
                            "handle": item.get("author", "unknown_user"),
                            "timestamp": item.get("timestamp"),
                            "engagement": item.get("engagement", {}),
                            "credibility_tier": "unverified",
                            "raw_metadata": item
                        })

                    for item in t_items:
                        all_social_provenance.append({
                            "claim": claim,
                            "source_type": "telegram",
                            "platform": f"Telegram (@{item.get('channel', 'public_channel')})",
                            "title": item.get("text", "")[:100],
                            "url": item.get("url", ""),
                            "handle": item.get("channel", "telegram_broadcast"),
                            "timestamp": item.get("timestamp"),
                            "credibility_tier": "unverified",
                            "raw_metadata": item
                        })

            return AgentResult(
                success=True,
                data={
                    "social_provenance": all_social_provenance
                }
            )

        except Exception as e:
            logger.error(f"Social Hunter execution error: {e}")
            return AgentResult(success=False, error=str(e))

    async def _search_reddit(self, client: httpx.AsyncClient, query: str) -> List[Dict[str, Any]]:
        """Search public Reddit JSON endpoint for matching submissions."""
        results = []
        try:
            tokens = [t for t in re.findall(r'\w+', query.lower()) if len(t) > 3][:5]
            search_query = " ".join(tokens) or query[:40]

            url = "https://www.reddit.com/search.json"
            headers = {"User-Agent": self.user_agent}
            params = {"q": search_query, "sort": "new", "limit": 5}

            resp = await client.get(url, headers=headers, params=params)
            if resp.status_code == 200:
                data = resp.json()
                children = data.get("data", {}).get("children", [])
                for child in children:
                    post = child.get("data", {})
                    created_utc = post.get("created_utc")
                    dt_str = None
                    if created_utc:
                        dt_str = datetime.fromtimestamp(created_utc, tz=timezone.utc).isoformat()

                    permalink = post.get("permalink", "")
                    full_url = f"https://reddit.com{permalink}" if permalink else ""

                    results.append({
                        "title": post.get("title", ""),
                        "author": post.get("author", "redditor"),
                        "subreddit": post.get("subreddit", "conspiracy"),
                        "url": full_url,
                        "timestamp": dt_str,
                        "engagement": {
                            "score": post.get("score", 0),
                            "num_comments": post.get("num_comments", 0),
                            "upvote_ratio": post.get("upvote_ratio", 1.0)
                        }
                    })
        except Exception as e:
            logger.debug(f"Reddit search failed: {e}")
        return results

    async def _search_telegram_public(self, client: httpx.AsyncClient, query: str) -> List[Dict[str, Any]]:
        """Search public Telegram web previews."""
        results = []
        try:
            # Check public news and viral aggregator channels
            sample_channels = ["breakingnews", "worldnews"]
            for ch in sample_channels:
                url = f"https://t.me/s/{ch}"
                resp = await client.get(url, headers={"User-Agent": self.user_agent})
                if resp.status_code == 200 and query.lower()[:15] in resp.text.lower():
                    results.append({
                        "channel": ch,
                        "text": f"Forwarded message concerning: {query[:60]}",
                        "url": f"https://t.me/{ch}",
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    })
        except Exception as e:
            logger.debug(f"Telegram search error: {e}")
        return results
