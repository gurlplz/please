"""Platform subdomain enumeration - generates candidate URLs from common deployment platforms."""

import asyncio
import itertools
import string
from typing import AsyncIterator

# Common subdomain patterns people use for self-hosted apps
COMMON_NAMES = [
    "openclaw", "claw", "clawbot", "bot", "ai", "assistant",
    "chat", "claude", "gpt", "llm", "molt", "moltbot",
    "dev", "staging", "prod", "demo", "test", "app",
    "my", "personal", "home", "local", "server",
]

# Random suffixes for brute force
ALPHANUM = string.ascii_lowercase + string.digits


def _generate_subdomains() -> list[str]:
    """Generate candidate subdomain names."""
    subs = set(COMMON_NAMES.copy())

    # Add common + random combos (e.g. openclaw-dev, claw-abc123)
    for name in COMMON_NAMES[:10]:
        for suffix in ["-dev", "-prod", "-staging", "-demo", "-test", "-app"]:
            subs.add(f"{name}{suffix}")
        for i in range(10):
            subs.add(f"{name}{i}")
            subs.add(f"{name}-{i}")

    # Short random (3-6 chars) - common for temp deployments
    for length in [3, 4, 5]:
        for combo in itertools.islice(itertools.product(ALPHANUM, repeat=length), 500):
            subs.add("".join(combo))

    return list(subs)


class PlatformEnumerator:
    """Enumerates candidate URLs from deployment platform subdomain patterns."""

    PLATFORM_DOMAINS = {
        "railway": "railway.app",
        "render": "onrender.com",
        "fly": "fly.dev",
        "vercel": "vercel.app",
        "heroku": "herokuapp.com",
        "cloudflare": "trycloudflare.com",
        "ngrok": "ngrok-free.app",
        "replit": "replit.dev",
        "glitch": "glitch.me",
    }

    def __init__(self, platforms: list[str] | None = None):
        self.platforms = platforms or list(self.PLATFORM_DOMAINS.keys())
        self._subdomains = _generate_subdomains()

    async def discover(self) -> AsyncIterator[str]:
        """Yield candidate URLs."""
        for platform in self.platforms:
            if platform not in self.PLATFORM_DOMAINS:
                continue
            domain = self.PLATFORM_DOMAINS[platform]
            for sub in self._subdomains:
                # Skip overly long subdomains
                if len(sub) > 30:
                    continue
                url = f"https://{sub}.{domain}"
                yield url
                await asyncio.sleep(0)  # Yield control
