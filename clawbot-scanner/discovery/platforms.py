"""Platform subdomain enumeration - generates candidate URLs from common deployment platforms."""

import asyncio
import itertools
import string
from typing import AsyncIterator

# High-priority: OpenClaw-related (yielded first)
PRIORITY_NAMES = [
    "openclaw", "clawbot", "claw", "moltbot", "clawctl",
    "openclaw-dev", "openclaw-demo", "claw-demo", "clawbot-demo",
]

# Common subdomain patterns for self-hosted apps
COMMON_NAMES = [
    "ai", "assistant", "chat", "claude", "gpt", "llm", "bot",
    "dev", "staging", "prod", "demo", "test", "app",
    "my", "personal", "home", "server",
]

# Random suffixes for brute force
ALPHANUM = string.ascii_lowercase + string.digits


def _generate_subdomains(prioritize: bool = True) -> list[str]:
    """Generate candidate subdomain names. Priority names first if prioritize=True."""
    priority = list(PRIORITY_NAMES) if prioritize else []
    rest = set(COMMON_NAMES.copy())

    for name in COMMON_NAMES[:8]:
        for suffix in ["-dev", "-prod", "-staging", "-demo", "-test", "-app"]:
            rest.add(f"{name}{suffix}")
        for i in range(5):
            rest.add(f"{name}{i}")
            rest.add(f"{name}-{i}")

    # Short random (3-4 chars) - common for temp deployments
    for length in [3, 4]:
        for combo in itertools.islice(itertools.product(ALPHANUM, repeat=length), 300):
            rest.add("".join(combo))

    if prioritize:
        return priority + [s for s in rest if s not in set(priority)]
    return list(rest)


class PlatformEnumerator:
    """Enumerates candidate URLs from deployment platform subdomain patterns."""

    # Ordered by likelihood of self-hosted apps (Railway, Render very common)
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
        "streamlit": "streamlit.app",
        "modal": "modal.run",
    }

    def __init__(self, platforms: list[str] | None = None, prioritize: bool = True):
        self.platforms = platforms or list(self.PLATFORM_DOMAINS.keys())
        self._subdomains = _generate_subdomains(prioritize=prioritize)

    async def discover(self) -> AsyncIterator[str]:
        """Yield candidate URLs. Priority subdomains + platforms first."""
        seen: set[str] = set()
        for platform in self.platforms:
            if platform not in self.PLATFORM_DOMAINS:
                continue
            domain = self.PLATFORM_DOMAINS[platform]
            for sub in self._subdomains:
                if len(sub) > 30:
                    continue
                url = f"https://{sub}.{domain}"
                if url in seen:
                    continue
                seen.add(url)
                yield url
                await asyncio.sleep(0)
