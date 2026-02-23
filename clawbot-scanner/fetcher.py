"""HTTP fetcher with OpenClaw fingerprinting."""

import asyncio
import time
from dataclasses import dataclass, field
from urllib.parse import urlparse

import httpx

from config import FINGERPRINTS, REQUEST_TIMEOUT, RATE_LIMIT_DELAY


@dataclass
class ScanResult:
    """Result of scanning a URL for OpenClaw."""

    url: str
    is_openclaw: bool
    confidence: float  # 0-1
    signals: list[str] = field(default_factory=list)
    status_code: int | None = None
    error: str | None = None


class OpenClawFetcher:
    """Fetches URLs and fingerprints for OpenClaw instances."""

    def __init__(self, max_concurrent: int = 50, timeout: float = REQUEST_TIMEOUT):
        self.max_concurrent = max_concurrent
        self.timeout = timeout
        self._semaphore = asyncio.Semaphore(max_concurrent)
        self._domain_delays: dict[str, float] = {}

    def _matches_fingerprint(self, text: str) -> bool:
        """Check if response content matches OpenClaw fingerprints."""
        if not text:
            return False
        lower = text.lower()
        return any(fp in lower for fp in FINGERPRINTS["content"])

    def _check_headers(self, headers: httpx.Headers) -> list[str]:
        """Check response headers for OpenClaw signals."""
        signals = []
        for key in headers.keys():
            key_lower = key.lower()
            if any(fp in key_lower for fp in FINGERPRINTS["headers"]):
                signals.append(f"header:{key}")
        return signals

    async def fetch(self, url: str) -> ScanResult:
        """Fetch URL and determine if it's an OpenClaw instance."""
        async with self._semaphore:
            domain = urlparse(url).netloc
            last = self._domain_delays.get(domain, 0)
            delay = max(0, RATE_LIMIT_DELAY - (time.monotonic() - last))
            if delay > 0:
                await asyncio.sleep(delay)
            self._domain_delays[domain] = time.monotonic()

            try:
                async with httpx.AsyncClient(
                    timeout=self.timeout,
                    follow_redirects=True,
                    headers={"User-Agent": "OpenClaw-SecurityScanner/1.0"},
                ) as client:
                    resp = await client.get(url)
                    signals = []
                    confidence = 0.0

                    # Check headers
                    header_signals = self._check_headers(resp.headers)
                    signals.extend(header_signals)
                    if header_signals:
                        confidence += 0.4

                    # Check body
                    text = resp.text
                    if self._matches_fingerprint(text):
                        signals.append("content_match")
                        confidence += 0.5

                    # Root path often serves dashboard - extra confidence
                    parsed = urlparse(url)
                    if parsed.path in ("", "/") and self._matches_fingerprint(text):
                        confidence += 0.2

                    # Normalize confidence
                    confidence = min(1.0, confidence)
                    is_openclaw = confidence >= 0.5

                    return ScanResult(
                        url=url,
                        is_openclaw=is_openclaw,
                        confidence=confidence,
                        signals=signals,
                        status_code=resp.status_code,
                    )
            except Exception as e:
                return ScanResult(
                    url=url,
                    is_openclaw=False,
                    confidence=0.0,
                    signals=[],
                    error=str(e),
                )

    async def fetch_batch(self, urls: list[str]) -> list[ScanResult]:
        """Fetch multiple URLs concurrently."""
        tasks = [self.fetch(url) for url in urls]
        return await asyncio.gather(*tasks, return_exceptions=False)
