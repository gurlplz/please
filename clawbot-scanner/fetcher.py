"""HTTP fetcher with OpenClaw fingerprinting and security assessment."""

import asyncio
import time
from dataclasses import dataclass, field
from urllib.parse import urljoin, urlparse

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
    insecure: bool = False  # No auth, exposed dashboard
    paths_checked: list[str] = field(default_factory=list)


class OpenClawFetcher:
    """Fetches URLs and fingerprints for OpenClaw instances."""

    # Paths to probe - order matters (root first)
    PROBE_PATHS = ["/", "/openclaw", "/v1/chat/completions", "/dashboard"]

    def __init__(
        self,
        max_concurrent: int = 50,
        timeout: float = REQUEST_TIMEOUT,
        max_retries: int = 2,
    ):
        self.max_concurrent = max_concurrent
        self.timeout = timeout
        self.max_retries = max_retries
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

    def _has_auth(self, headers: httpx.Headers, status: int) -> bool:
        """Check if response indicates authentication is required."""
        # 401/403 = auth required (good)
        if status in (401, 403):
            return True
        # WWW-Authenticate header = auth required
        if "www-authenticate" in {k.lower() for k in headers.keys()}:
            return True
        return False

    async def _fetch_one(
        self,
        client: httpx.AsyncClient,
        url: str,
        path: str = "/",
    ) -> tuple[str, httpx.Response | None, str | None]:
        """Fetch single URL/path. Returns (path, response, error)."""
        full_url = urljoin(url.rstrip("/") + "/", path.lstrip("/"))
        try:
            resp = await client.get(full_url)
            return (path, resp, None)
        except Exception as e:
            return (path, None, str(e))

    async def fetch(self, url: str) -> ScanResult:
        """Fetch URL and determine if it's an OpenClaw instance."""
        async with self._semaphore:
            domain = urlparse(url).netloc
            last = self._domain_delays.get(domain, 0)
            delay = max(0, RATE_LIMIT_DELAY - (time.monotonic() - last))
            if delay > 0:
                await asyncio.sleep(delay)
            self._domain_delays[domain] = time.monotonic()

            signals: list[str] = []
            confidence = 0.0
            insecure = False
            paths_checked: list[str] = []
            best_status: int | None = None

            for attempt in range(self.max_retries + 1):
                try:
                    async with httpx.AsyncClient(
                        timeout=self.timeout,
                        follow_redirects=True,
                        headers={"User-Agent": "OpenClaw-SecurityScanner/1.0"},
                    ) as client:
                        # Probe root first
                        path, resp, err = await self._fetch_one(client, url, "/")
                        if err:
                            return ScanResult(
                                url=url,
                                is_openclaw=False,
                                confidence=0.0,
                                signals=[],
                                error=err,
                            )

                        paths_checked.append("/")
                        best_status = resp.status_code

                        # Check headers
                        header_signals = self._check_headers(resp.headers)
                        signals.extend(header_signals)
                        if header_signals:
                            confidence += 0.3

                        # Check body
                        text = resp.text
                        if self._matches_fingerprint(text):
                            signals.append("content_match")
                            confidence += 0.5

                        # Root path with fingerprint = dashboard
                        parsed = urlparse(url)
                        if parsed.path in ("", "/") and self._matches_fingerprint(text):
                            confidence += 0.2
                            paths_checked.append("(dashboard)")
                            # 200 without auth = potentially insecure
                            if not self._has_auth(resp.headers, resp.status_code):
                                insecure = True
                                signals.append("no_auth")

                        # Probe API paths - MUST get gateway response (not 404) = live instance
                        # Reject: 404, or 200 with HTML (catch-all/static server)
                        api_live = False
                        for api_path in ["/v1/chat/completions", "/v1/responses"]:
                            _, api_resp, _ = await self._fetch_one(client, url, api_path)
                            if not api_resp or api_resp.status_code == 404:
                                continue
                            ct = (api_resp.headers.get("content-type") or "").lower()
                            # 200 with HTML = catch-all, not real API
                            if api_resp.status_code == 200 and "text/html" in ct:
                                continue
                            paths_checked.append(api_path)
                            if api_resp.status_code in (401, 403, 405):
                                signals.append("api_endpoint")
                                confidence += 0.4
                                api_live = True
                                break
                            elif api_resp.status_code == 200:
                                signals.append("api_open")
                                confidence += 0.3
                                insecure = True
                                api_live = True
                                break
                            elif api_resp.status_code in (400, 422) and "json" in ct:
                                api_live = True
                                signals.append("api_endpoint")
                                break

                        confidence = min(1.0, confidence)
                        # Require API liveness - reject static pages, dead tunnels, docs
                        is_openclaw = confidence >= 0.5 and api_live

                        return ScanResult(
                            url=url,
                            is_openclaw=is_openclaw,
                            confidence=confidence,
                            signals=signals,
                            status_code=best_status,
                            insecure=insecure,
                            paths_checked=paths_checked,
                        )

                except Exception as e:
                    if attempt == self.max_retries:
                        return ScanResult(
                            url=url,
                            is_openclaw=False,
                            confidence=0.0,
                            signals=[],
                            error=str(e),
                        )
                    await asyncio.sleep(0.5 * (2**attempt))

            return ScanResult(
                url=url,
                is_openclaw=False,
                confidence=0.0,
                signals=signals,
                status_code=best_status,
            )

    async def fetch_batch(self, urls: list[str]) -> list[ScanResult]:
        """Fetch multiple URLs concurrently."""
        tasks = [self.fetch(url) for url in urls]
        return await asyncio.gather(*tasks, return_exceptions=False)
