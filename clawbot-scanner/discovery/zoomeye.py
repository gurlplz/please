"""Zoomeye discovery - Shodan alternative, free tier with API key.

Get API key: https://www.zoomeye.org/profile
Set ZOOMEYE_API_KEY env var.
"""

import asyncio
import httpx
from typing import AsyncIterator

ZOOMEYE_API = "https://api.zoomeye.org"

# Shodan-style queries: title (http.title), body (http.html), product
SEARCH_QUERIES = [
    'title="openclaw"',
    'title="clawbot"',
    'title="clawctl"',
    'body="openclaw"',
    'body="clawbot"',
    'body="control-ui"',
    'body="openclaw" +port:"3000"',
    'body="openclaw" +port:"18789"',
    'body="clawbot" +port:"3000"',
]


class ZoomeyeCrawler:
    """Searches Zoomeye for OpenClaw instances (free tier, requires API key)."""

    def __init__(self, api_key: str | None = None, timeout: int = 30):
        self.api_key = api_key
        self.timeout = timeout

    async def discover(self) -> AsyncIterator[str]:
        """Search Zoomeye and yield IP:port URLs."""
        if not self.api_key:
            print("[Zoomeye] Skip: set ZOOMEYE_API_KEY for Zoomeye search")
            return

        seen: set[str] = set()
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            for query in SEARCH_QUERIES[:4]:  # Limit to avoid quota
                try:
                    resp = await client.get(
                        f"{ZOOMEYE_API}/host/search",
                        params={"query": query, "page": 1, "size": 50},
                        headers={"API-KEY": self.api_key},
                    )
                    if resp.status_code == 401:
                        print("[Zoomeye] Invalid API key")
                        return
                    if resp.status_code == 403:
                        print("[Zoomeye] Quota exceeded or no search access")
                        return
                    resp.raise_for_status()
                    data = resp.json()
                except Exception as e:
                    print(f"[Zoomeye] Error: {e}")
                    continue

                for match in data.get("matches", []):
                    ip = match.get("ip")
                    port = match.get("port")
                    if not port and "portinfo" in match:
                        port = match["portinfo"].get("port")
                    if not ip:
                        continue
                    if port:
                        url = f"http://{ip}:{port}"
                    else:
                        for p in [3000, 18789, 8080, 5000]:
                            url = f"http://{ip}:{p}"
                            if url not in seen:
                                seen.add(url)
                                yield url
                                await asyncio.sleep(0)
                        continue
                    if url not in seen:
                        seen.add(url)
                        yield url
                        await asyncio.sleep(0)

                await asyncio.sleep(1)
