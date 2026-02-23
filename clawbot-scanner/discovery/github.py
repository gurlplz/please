"""GitHub crawler - finds URLs from repos, issues, and code."""

import asyncio
import base64
import re
import httpx
from typing import AsyncIterator


class GitHubCrawler:
    """Searches GitHub for OpenClaw-related content and extracts URLs."""

    GITHUB_API = "https://api.github.com"
    # GitHub allows 60 unauthenticated requests/hour, 5000/hour with token
    RATE_LIMIT_DELAY = 2.0  # Conservative for unauthenticated

    # URL pattern - catches http(s) URLs
    URL_PATTERN = re.compile(
        r"https?://[a-zA-Z0-9][-a-zA-Z0-9.]*[a-zA-Z0-9](?::[0-9]+)?(?:/[^\s\)\]\"']*)?",
        re.IGNORECASE,
    )

    def __init__(self, token: str | None = None, timeout: int = 30):
        self.token = token
        self.timeout = timeout
        self._headers = {"Accept": "application/vnd.github.v3+json"}
        if token:
            self._headers["Authorization"] = f"Bearer {token}"

    async def discover(self) -> AsyncIterator[str]:
        """Search GitHub and yield extracted URLs."""
        seen = set()
        async with httpx.AsyncClient(
            timeout=self.timeout,
            headers=self._headers,
            follow_redirects=True,
        ) as client:
            # Search code for openclaw configs, docker-compose, deploy URLs
            search_queries = [
                "openclaw docker-compose",
                "openclaw deploy url",
                "clawbot railway",
                "openclaw onrender",
                "openclaw vercel",
                "clawctl deploy",
                "moltbot fly.dev",
            ]

            for q in search_queries:
                try:
                    resp = await client.get(
                        f"{self.GITHUB_API}/search/code",
                        params={"q": q, "per_page": 30},
                    )
                    if resp.status_code == 403:
                        print("[GitHub] Rate limited - consider adding GITHUB_TOKEN")
                        break
                    resp.raise_for_status()
                    data = resp.json()
                except Exception as e:
                    print(f"[GitHub] Error: {e}")
                    continue

                for item in data.get("items", [])[:15]:
                    try:
                        # Fetch file content
                        content_url = item.get("url")
                        if not content_url:
                            continue
                        file_resp = await client.get(content_url)
                        file_resp.raise_for_status()
                        content = file_resp.json().get("content", "")
                        if content:
                            raw = base64.b64decode(content).decode("utf-8", errors="ignore")
                            for url in self._extract_urls(raw):
                                if url not in seen and self._is_plausible(url):
                                    seen.add(url)
                                    yield url
                                    await asyncio.sleep(0)
                    except Exception:
                        pass

                await asyncio.sleep(self.RATE_LIMIT_DELAY)

    def _extract_urls(self, text: str) -> list[str]:
        """Extract URLs from text."""
        urls = []
        for m in self.URL_PATTERN.finditer(text):
            url = m.group(0).rstrip(".,;:)")
            urls.append(url)
        return urls

    def _is_plausible(self, url: str) -> bool:
        """Filter to plausible deployment URLs."""
        url_lower = url.lower()
        skip = [
            "github.com", "npmjs.com", "npm.org", "docs.", "example.com",
            "localhost", "raw.githubusercontent", "img.shields", "badge",
        ]
        return not any(s in url_lower for s in skip) and "http" in url_lower
