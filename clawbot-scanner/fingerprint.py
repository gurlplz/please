"""Shodan-style fingerprinting: favicon hash, http.title, product detection."""

import base64
import re
from typing import Optional

import mmh3

from config import FAVICON_HASHES, FINGERPRINTS


def compute_favicon_hash(data: bytes) -> Optional[int]:
    """Compute Shodan-style favicon hash (mmh3 of base64 with 76-char newlines)."""
    if not data or len(data) < 10:
        return None
    try:
        b64 = base64.b64encode(data).decode("utf-8")
        with_newlines = re.sub(r"(.{76})", r"\1\n", b64)
        if len(b64) % 76:
            with_newlines += "\n"
        return mmh3.hash(with_newlines)
    except Exception:
        return None


def matches_favicon(data: bytes) -> bool:
    """Check if favicon matches known OpenClaw hashes."""
    h = compute_favicon_hash(data)
    return h in FAVICON_HASHES if h is not None else False


def extract_title(html: str) -> Optional[str]:
    """Extract http.title from HTML."""
    if not html:
        return None
    m = re.search(r"<title[^>]*>([^<]+)</title>", html, re.I | re.S)
    return m.group(1).strip()[:200] if m else None


def matches_title(title: Optional[str]) -> bool:
    """Check if title contains OpenClaw product names."""
    if not title:
        return False
    lower = title.lower()
    return any(p in lower for p in FINGERPRINTS["product"])


def extract_product(headers) -> Optional[str]:
    """Extract product from Server, X-Powered-By, etc."""
    h = dict(headers) if hasattr(headers, "__iter__") else {}
    for key in ["server", "x-powered-by", "x-aspnet-version"]:
        for k, v in h.items():
            if k.lower() == key and v:
                return str(v)[:100]
    return None


def matches_product(product: Optional[str]) -> bool:
    """Check if product header indicates OpenClaw."""
    if not product:
        return False
    lower = product.lower()
    return any(p in lower for p in FINGERPRINTS["product"])
