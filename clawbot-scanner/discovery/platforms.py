"""Platform subdomain enumeration - generates candidate URLs from deployment platforms."""

import asyncio
import itertools
import string
from pathlib import Path
from typing import AsyncIterator

# High-priority: OpenClaw-related (yielded first)
PRIORITY_NAMES = [
    "openclaw", "clawbot", "claw", "moltbot", "clawctl",
    "openclaw-dev", "openclaw-demo", "claw-demo", "clawbot-demo",
    "open-claw", "claw-bot", "claw-assistant",
]

# Common subdomain patterns for self-hosted apps
COMMON_NAMES = [
    "ai", "assistant", "chat", "claude", "gpt", "llm", "bot",
    "dev", "staging", "prod", "demo", "test", "app",
    "my", "personal", "home", "server", "agent", "claw",
]

# Extended wordlist for broader coverage
EXTENDED_NAMES = [
    "api", "web", "ui", "dashboard", "admin", "portal",
    "sandbox", "playground", "experiment", "trial",
    "node", "gateway", "proxy", "bridge",
]

# Random suffixes for brute force
ALPHANUM = string.ascii_lowercase + string.digits


def _generate_subdomains(prioritize: bool = True, extended: bool = True) -> list[str]:
    """Generate candidate subdomain names."""
    priority = list(PRIORITY_NAMES) if prioritize else []
    rest = set(COMMON_NAMES.copy())
    if extended:
        rest.update(EXTENDED_NAMES)

    for name in COMMON_NAMES[:10]:
        for suffix in ["-dev", "-prod", "-staging", "-demo", "-test", "-app", "-api"]:
            rest.add(f"{name}{suffix}")
        for i in range(8):
            rest.add(f"{name}{i}")
            rest.add(f"{name}-{i}")

    # Short random (3-4 chars)
    for length in [3, 4]:
        for combo in itertools.islice(itertools.product(ALPHANUM, repeat=length), 400):
            rest.add("".join(combo))

    if prioritize:
        return priority + [s for s in rest if s not in set(priority)]
    return list(rest)


class PlatformEnumerator:
    """Enumerates candidate URLs from deployment platform subdomain patterns."""

    # Expanded: ordered by likelihood for self-hosted apps
    PLATFORM_DOMAINS = {
        # High-traffic free tiers
        "railway": "railway.app",
        "render": "onrender.com",
        "fly": "fly.dev",
        "vercel": "vercel.app",
        "netlify": "netlify.app",
        "heroku": "herokuapp.com",
        # Tunnels / quick share
        "cloudflare": "trycloudflare.com",
        "ngrok": "ngrok-free.app",
        # Dev / hobby
        "replit": "replit.dev",
        "glitch": "glitch.me",
        "streamlit": "streamlit.app",
        "modal": "modal.run",
        # Cloud providers
        "pages": "pages.dev",  # Cloudflare Pages
        "deno": "deno.dev",  # Deno Deploy
        "amplify": "amplifyapp.com",  # AWS Amplify
        "azure": "azurewebsites.net",
        "surge": "surge.sh",
        # Code hosts
        "github": "github.io",
        "gitlab": "gitlab.io",
        "codeberg": "codeberg.page",
        # Other
        "koyeb": "koyeb.app",
        "pythonanywhere": "pythonanywhere.com",
        "codesandbox": "csb.app",  # CodeSandbox
        "stackblitz": "webcontainer.io",
        "observable": "observablehq.com",
        "gradio": "gradio.live",
        "huggingface": "hf.space",  # Hugging Face Spaces
    }

    def __init__(
        self,
        platforms: list[str] | None = None,
        prioritize: bool = True,
        extended: bool = True,
        wordlist_path: Path | str | None = None,
    ):
        self.platforms = platforms or list(self.PLATFORM_DOMAINS.keys())
        self._subdomains = _generate_subdomains(prioritize=prioritize, extended=extended)

        # Load custom wordlist if provided
        if wordlist_path:
            path = Path(wordlist_path)
            if path.exists():
                extra = [line.strip() for line in path.read_text().splitlines() if line.strip()]
                self._subdomains = list(dict.fromkeys(self._subdomains + extra))

    async def discover(self) -> AsyncIterator[str]:
        """Yield candidate URLs."""
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
