"""Community sources - Reddit, HN, etc. Extract URLs from discussions."""

import asyncio
import re
import httpx
from typing import AsyncIterator

# URL pattern
URL_PATTERN = re.compile(
    r"https?://(?:(?:[a-zA-Z0-9][-a-zA-Z0-9.]*[a-zA-Z0-9])|(?:\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}))(?::\d+)?(?:/[^\s\)\]\"'<>]*)?",
    re.IGNORECASE,
)

SKIP_DOMAINS = [
    "github.com", "npmjs.com", "reddit.com", "youtube.com", "twitter.com",
    "img.shields", "badge", "example.com", "localhost", "discord.gg",
]


def _extract_urls(text: str) -> list[str]:
    return [m.group(0).rstrip(".,;:)") for m in URL_PATTERN.finditer(text)]


def _is_plausible(url: str) -> bool:
    lower = url.lower()
    return not any(s in lower for s in SKIP_DOMAINS) and "http" in lower


class CommunityCrawler:
    """Extracts URLs from Reddit, Hacker News, etc."""

    def __init__(self, timeout: int = 30):
        self.timeout = timeout

    async def discover(self) -> AsyncIterator[str]:
        """Fetch community posts and extract URLs."""
        seen: set[str] = set()
        async with httpx.AsyncClient(
            timeout=self.timeout,
            headers={"User-Agent": "OpenClaw-SecurityScanner/1.0"},
        ) as client:
            # Reddit - r/openclaw, r/clawbot (if exists)
            for sub in ["openclaw", "OpenClaw", "clawbot"]:
                try:
                    resp = await client.get(
                        f"https://www.reddit.com/r/{sub}/search.json",
                        params={"q": "url", "restrict_sr": "on", "limit": 25},
                    )
                    if resp.status_code != 200:
                        continue
                    data = resp.json()
                    for child in data.get("data", {}).get("children", []):
                        post = child.get("data", {})
                        text = f"{post.get('title', '')} {post.get('selftext', '')} {post.get('url', '')}"
                        for u in _extract_urls(text):
                            if u not in seen and _is_plausible(u):
                                seen.add(u)
                                yield u
                                await asyncio.sleep(0)
                except Exception as e:
                    print(f"[Community] Reddit r/{sub}: {e}")
                await asyncio.sleep(1)

            # HN - Algolia API (free)
            try:
                resp = await client.post(
                    "https://hn.algolia.com/api/v1/search",
                    json={
                        "query": "openclaw OR clawbot",
                        "tags": "story",
                        "hitsPerPage": 50,
                    },
                )
                if resp.status_code == 200:
                    data = resp.json()
                    for hit in data.get("hits", []):
                        text = f"{hit.get('title', '')} {hit.get('url', '')} {hit.get('story_text', '')}"
                        for u in _extract_urls(text):
                            if u not in seen and _is_plausible(u):
                                seen.add(u)
                                yield u
                                await asyncio.sleep(0)
            except Exception as e:
                print(f"[Community] HN: {e}")
