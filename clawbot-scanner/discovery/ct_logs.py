"""Certificate Transparency log crawler - finds domains via crt.sh (free API)."""

import asyncio
import httpx
from typing import AsyncIterator


class CTLogCrawler:
    """Queries crt.sh for domains matching OpenClaw-related patterns."""

    CRT_SH_API = "https://crt.sh"

    # Search patterns that might reveal OpenClaw deployments
    SEARCH_PATTERNS = [
        "%openclaw%",
        "%clawbot%",
        "%clawctl%",
        "%moltbot%",
    ]

    def __init__(self, timeout: int = 30):
        self.timeout = timeout

    async def discover(self) -> AsyncIterator[str]:
        """Query crt.sh and yield unique domain names."""
        seen = set()
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            for pattern in self.SEARCH_PATTERNS:
                try:
                    resp = await client.get(
                        self.CRT_SH_API,
                        params={"q": pattern, "output": "json"},
                    )
                    resp.raise_for_status()
                    data = resp.json()
                except Exception as e:
                    print(f"[CT] Error querying {pattern}: {e}")
                    await asyncio.sleep(5)  # Back off on errors
                    continue

                if not isinstance(data, list):
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
                        seen.add(domain)
                        yield f"https://{domain}"
                        await asyncio.sleep(0)

                await asyncio.sleep(1)  # Be nice to crt.sh
