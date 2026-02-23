"""Enumerate data exposed by insecure OpenClaw instances."""

import json
import re
from dataclasses import dataclass, field
from urllib.parse import urljoin

import httpx

from config import REQUEST_TIMEOUT


@dataclass
class EnumeratedData:
    """Structured data enumerated from an insecure instance."""

    url: str
    endpoints: dict[str, dict] = field(default_factory=dict)  # path -> {status, headers, snippet}
    headers: dict[str, str] = field(default_factory=dict)
    title: str | None = None
    meta: dict[str, str] = field(default_factory=dict)
    content_snippet: str | None = None
    json_responses: dict[str, object] = field(default_factory=dict)
    error: str | None = None


# Paths to probe for enumeration
ENUM_PATHS = [
    "/",
    "/v1/chat/completions",
    "/v1/responses",
    "/tools/invoke",
    "/config",
    "/api/config",
    "/config.json",
    "/health",
    "/status",
    "/openclaw",
    "/dashboard",
]

# Sensitive patterns - redact from output
SENSITIVE_PATTERNS = [
    (re.compile(r'(api[_-]?key|token|secret|password)\s*[:=]\s*["\']?[^\s"\']+', re.I), r'\1=***REDACTED***'),
    (re.compile(r'["\']([a-zA-Z0-9]{20,})["\']'), r'"***REDACTED***"'),  # Long strings
]


def _redact(text: str) -> str:
    """Redact sensitive-looking content from text."""
    for pattern, repl in SENSITIVE_PATTERNS:
        text = pattern.sub(repl, text)
    return text


def _extract_title(html: str) -> str | None:
    """Extract page title from HTML."""
    m = re.search(r'<title[^>]*>([^<]+)</title>', html, re.I | re.S)
    return m.group(1).strip()[:200] if m else None


def _extract_meta(html: str) -> dict[str, str]:
    """Extract meta tags from HTML."""
    meta = {}
    for m in re.finditer(r'<meta\s+([^>]+)>', html, re.I):
        attrs = m.group(1)
        name = re.search(r'name=["\']([^"\']+)["\']', attrs, re.I)
        content = re.search(r'content=["\']([^"\']+)["\']', attrs, re.I)
        if name and content:
            meta[name.group(1)] = content.group(1)[:100]
    return meta


class InsecureEnumerator:
    """Enumerates data exposed by insecure OpenClaw instances."""

    def __init__(self, timeout: float = REQUEST_TIMEOUT):
        self.timeout = timeout

    async def enumerate(self, url: str) -> EnumeratedData:
        """Probe insecure instance and collect exposed data."""
        result = EnumeratedData(url=url)
        base = url.rstrip("/") + "/"

        async with httpx.AsyncClient(
            timeout=self.timeout,
            follow_redirects=True,
            headers={"User-Agent": "OpenClaw-SecurityScanner/1.0"},
        ) as client:
            for path in ENUM_PATHS:
                full_url = urljoin(base, path.lstrip("/"))
                try:
                    if path == "/tools/invoke":
                        resp = await client.post(full_url, json={"tool": "ping"})
                    else:
                        resp = await client.get(full_url)

                    ep_data = {
                        "status": resp.status_code,
                        "headers": dict(resp.headers),
                        "content_type": resp.headers.get("content-type", "")[:50],
                    }

                    # Snippet (redacted)
                    text = resp.text[:500] if resp.text else ""
                    if text:
                        ep_data["snippet"] = _redact(text)[:300]

                    # JSON parse if applicable
                    ct = resp.headers.get("content-type", "")
                    if "json" in ct and resp.text:
                        try:
                            data = json.loads(resp.text)
                            # Store structure, not values (keys only for nested)
                            ep_data["json_keys"] = list(data.keys()) if isinstance(data, dict) else []
                            result.json_responses[path] = ep_data["json_keys"]
                        except Exception:
                            pass

                    result.endpoints[path] = ep_data

                    # From root, extract title/meta
                    if path == "/" and resp.status_code == 200:
                        result.title = _extract_title(resp.text)
                        result.meta = _extract_meta(resp.text)
                        result.content_snippet = _redact(resp.text[:500])
                        result.headers = dict(resp.headers)

                except Exception as e:
                    result.endpoints[path] = {"error": str(e)}

        return result

    def to_dict(self, data: EnumeratedData) -> dict:
        """Convert to serializable dict."""
        # Truncate headers for output
        safe_headers = {}
        for k, v in data.headers.items():
            if k.lower() in ("authorization", "cookie", "set-cookie"):
                continue
            safe_headers[k] = str(v)[:200] if v else ""

        return {
            "url": data.url,
            "title": data.title,
            "meta": data.meta,
            "headers": safe_headers,
            "content_snippet": data.content_snippet[:500] if data.content_snippet else None,
            "endpoints": {
                path: {
                    "status": ep.get("status"),
                    "content_type": ep.get("content_type"),
                    "json_keys": ep.get("json_keys"),
                    "snippet": ep.get("snippet"),
                    "error": ep.get("error"),
                }
                for path, ep in data.endpoints.items()
            },
            "json_responses": data.json_responses,
        }
