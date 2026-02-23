"""Certificate Transparency log crawler - finds domains via crt.sh (free API)."""

import asyncio
import httpx
from typing import AsyncIterator


class CTLogCrawler:
    """Queries crt.sh for domains matching OpenClaw-related patterns."""

    CRT_SH_API = "https://crt.sh"

    SEARCH_PATTERNS = ["%openclaw%", "%clawbot%", "%clawctl%", "%moltbot%"]

    def __init__(self, timeout: int = 30, max_retries: int = 3):
        self.timeout = timeout
        self.max_retries = max_retries

    async def _query(self, client: httpx.AsyncClient, pattern: str) -> list | None:
        """Query crt.sh with retries."""
        for attempt in range(self.max_retries):
            try:
                resp = await client.get(
                    self.CRT_SH_API,
                    params={"q": pattern, "output": "json"},
                )
                resp.raise_for_status()
                data = resp.json()
                return data if isinstance(data, list) else None
            except Exception as e:
                if attempt == self.max_retries - 1:
                    print(f"[CT] Error querying {pattern}: {e}")
                    return None
                await asyncio.sleep(2 ** (attempt + 1))

        return None

    async def discover(self) -> AsyncIterator[str]:
        """Query crt.sh and yield unique domain names."""
        seen: set[str] = set()
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            for pattern in self.SEARCH_PATTERNS:
                data = await self._query(client, pattern)
                if not data:
                    continue

                for entry in data:
                    name = entry.get("name_value") or entry.get("common_name", "")
                    for part in name.replace("\n", " ").split():
                        domain = part.strip().lower()
                        if not domain or domain.startswith("*"):
                            continue
                        if domain in seen:
                            continue
                        if any(c in domain for c in [" ", "\n", ","]):
                            continue
                        # Skip wildcard-only
                        if domain.count("*") > 0 and len(domain) < 5:
                            continue
                        seen.add(domain)
                        yield f"https://{domain}"
                        await asyncio.sleep(0)

                await asyncio.sleep(1.5)  # Be nice to crt.sh
