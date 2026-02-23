"""GitHub crawler - finds URLs from repos, issues, and code."""

import asyncio
import base64
import re
import httpx
from typing import AsyncIterator


class GitHubCrawler:
    """Searches GitHub for OpenClaw-related content and extracts URLs."""

    GITHUB_API = "https://api.github.com"
    RATE_LIMIT_DELAY = 2.0

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
        """Search GitHub code, issues, and discussions for URLs."""
        seen = set()

        # Code search - expanded queries
        code_queries = [
            "openclaw docker-compose",
            "openclaw deploy url",
            "clawbot railway",
            "openclaw onrender",
            "openclaw vercel",
            "clawctl deploy",
            "moltbot fly.dev",
            "openclaw netlify",
            "openclaw heroku",
            "openclaw ngrok",
            "openclaw run.app",
            "clawbot pages.dev",
        ]

        async with httpx.AsyncClient(
            timeout=self.timeout,
            headers=self._headers,
            follow_redirects=True,
        ) as client:
            for q in code_queries:
                async for url in self._search_code(client, q, seen):
                    yield url

            # Repo search - find OpenClaw-related repos, check README
            repo_queries = ["openclaw", "clawbot", "open-claw"]
            for q in repo_queries:
                async for url in self._search_repos(client, q, seen):
                    yield url

    async def _search_code(
        self, client: httpx.AsyncClient, query: str, seen: set
    ) -> AsyncIterator[str]:
        """Search code and extract URLs."""
        try:
            resp = await client.get(
                f"{self.GITHUB_API}/search/code",
                params={"q": query, "per_page": 50},
            )
            if resp.status_code == 403:
                print("[GitHub] Rate limited - add GITHUB_TOKEN for higher limits")
                return
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            print(f"[GitHub] Error: {e}")
            return

        for item in data.get("items", [])[:25]:
            try:
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

    async def _search_repos(
        self, client: httpx.AsyncClient, query: str, seen: set
    ) -> AsyncIterator[str]:
        """Search repos and extract URLs from README."""
        try:
            resp = await client.get(
                f"{self.GITHUB_API}/search/repositories",
                params={"q": query, "sort": "stars", "per_page": 20},
            )
            if resp.status_code == 403:
                return
            resp.raise_for_status()
            data = resp.json()
        except Exception:
            return

        for repo in data.get("items", [])[:15]:
            try:
                readme_url = (
                    f"{self.GITHUB_API}/repos/{repo['full_name']}/readme"
                )
                readme_resp = await client.get(readme_url)
                if readme_resp.status_code != 200:
                    continue
                content = readme_resp.json().get("content", "")
                if content:
                    raw = base64.b64decode(content).decode("utf-8", errors="ignore")
                    for url in self._extract_urls(raw):
                        if url not in seen and self._is_plausible(url):
                            seen.add(url)
                            yield url
                            await asyncio.sleep(0)
            except Exception:
                pass

            await asyncio.sleep(0.5)

        await asyncio.sleep(self.RATE_LIMIT_DELAY)

    def _extract_urls(self, text: str) -> list[str]:
        """Extract URLs from text."""
        return [
            m.group(0).rstrip(".,;:)")
            for m in self.URL_PATTERN.finditer(text)
        ]

    def _is_plausible(self, url: str) -> bool:
        """Filter to plausible deployment URLs."""
        url_lower = url.lower()
        skip = [
            "github.com", "npmjs.com", "npm.org", "docs.", "example.com",
            "localhost", "raw.githubusercontent", "img.shields", "badge",
            "wikipedia.org", "twitter.com", "youtube.com", "discord.gg",
        ]
        return not any(s in url_lower for s in skip) and "http" in url_lower
