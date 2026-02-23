"""Crawl OpenClaw index/directory sites - extract URLs without Shodan subscription."""

import asyncio
import re
import httpx
from typing import AsyncIterator

# Index sites associated with OpenClaw/clawbot - curated directories, awesome lists
INDEX_SITES = [
    "https://openclawdirectory.dev/",
    "https://openclawsearch.com/",
    "https://openclawsearch.com/directory.html",
    "https://thewh1teagle.github.io/awesome-openclaw/",
    "https://awesome.tryopenclaw.asia/",
    "https://github.com/rohitg00/awesome-openclaw",
    "https://github.com/openclaw/openclaw",
    "https://raw.githubusercontent.com/rohitg00/awesome-openclaw/main/README.md",
    "https://raw.githubusercontent.com/openclaw/openclaw/main/README.md",
]

# URL pattern - http(s) URLs including IP:port
URL_PATTERN = re.compile(
    r"https?://(?:(?:[a-zA-Z0-9][-a-zA-Z0-9.]*[a-zA-Z0-9])|(?:\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}))(?::\d+)?(?:/[^\s\)\]\"'<>]*)?",
    re.IGNORECASE,
)

# IP:port pattern - valid IPv4 (each octet 0-255)
IP_PORT_PATTERN = re.compile(
    r"\b((?:25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)\.(?:25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)\.(?:25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)\.(?:25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d))(?::(\d{2,5}))?\b",
)


def _extract_urls(text: str) -> list[str]:
    """Extract URLs from text."""
    urls = []
    for m in URL_PATTERN.finditer(text):
        url = m.group(0).rstrip(".,;:)").rstrip("\\")
        urls.append(url)
    return urls


def _extract_ip_ports(text: str) -> list[tuple[str, int]]:
    """Extract IP:port pairs from text. Port defaults to common ports if missing."""
    pairs = []
    seen_ips: set[str] = set()
    for m in IP_PORT_PATTERN.finditer(text):
        ip, port = m.group(1), m.group(2)
        if ip in seen_ips and not port:
            continue
        seen_ips.add(ip)
        if port:
            pairs.append((ip, int(port)))
        else:
            for p in [3000, 18789, 8080, 5000]:
                pairs.append((ip, p))
    return pairs


# Blog/content site patterns - NOT app deployments
BLOG_PATTERNS = [
    "medium.com", "substack.com", "udemy.com", "eventbrite",
    "/blog/", "/articles/", "/news/", "/p/", "/post/", "/course/",
    "slashgear", "securityweek", "axios.com", "alibabacloud.com",
    "phemex.com", "elest.io", "northflank.com", "lightning.ai",
    "get-open-claw.com", "ibm.com/think", "sciencefocus",
    "evolutionaihub", "apidog.com/blog", "deepwiki.com",
    "claude-world.com", "ryanshook.org", "socradar.io", "stackviv.ai",
    "aimaker.substack", "amankhan1.substack", "mlearning.substack",
    "upwork.com/services", "sf.aitinkerers", "moltbook-ai.com/blog",
]


def _is_plausible(url: str) -> bool:
    """Filter to plausible deployment URLs - exclude blogs, articles, courses."""
    url_lower = url.lower().rstrip("\\")
    skip = [
        "github.com", "npmjs.com", "npm.org", "docs.", "example.com",
        "localhost", "raw.githubusercontent", "img.shields", "badge",
        "wikipedia.org", "twitter.com", "youtube.com", "discord.gg",
        "cdn.", "fonts.", "assets.", "static.", "analytics.",
        "schema.org", "w3.org", "creativecommons.org", "og-image",
        "og-default", "svg", "png", "jpg", "woff", "ttf",
    ]
    if any(s in url_lower for s in skip):
        return False
    if any(b in url_lower for b in BLOG_PATTERNS):
        return False
    # Prefer: openclaw/claw domains, IPs, deployment platforms
    if "openclaw" in url_lower or "clawbot" in url_lower or "clawhub" in url_lower:
        return True
    if "://" in url_lower and url_lower.split("://", 1)[1][0].isdigit():
        return True  # IP
    if any(p in url_lower for p in ["railway", "render", "vercel", "netlify", "fly.dev", "heroku", "ngrok"]):
        return True
    return "http" in url_lower


class IndexSiteCrawler:
    """Crawls OpenClaw index/directory sites and extracts URLs/IPs."""

    def __init__(self, timeout: int = 30):
        self.timeout = timeout

    async def discover(self) -> AsyncIterator[str]:
        """Fetch index sites and yield extracted URLs."""
        seen: set[str] = set()
        async with httpx.AsyncClient(
            timeout=self.timeout,
            follow_redirects=True,
            headers={"User-Agent": "OpenClaw-SecurityScanner/1.0"},
        ) as client:
            for url in INDEX_SITES:
                try:
                    resp = await client.get(url)
                    resp.raise_for_status()
                    text = resp.text
                except Exception as e:
                    print(f"[Index] {url}: {e}")
                    continue

                # Extract URLs
                for u in _extract_urls(text):
                    if u not in seen and _is_plausible(u):
                        seen.add(u)
                        yield u
                        await asyncio.sleep(0)

                # Extract raw IP:port (convert to http URL)
                for ip, port in _extract_ip_ports(text):
                    u = f"http://{ip}:{port}"
                    if u not in seen:
                        seen.add(u)
                        yield u
                        await asyncio.sleep(0)

                await asyncio.sleep(1)  # Be nice
