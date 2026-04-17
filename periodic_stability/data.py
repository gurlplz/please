from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from .constants import DEFAULT_DATA_URL


def fetch_periodic_table_json(
    url: str = DEFAULT_DATA_URL,
    *,
    cache_path: str | Path | None = None,
    timeout_s: float = 60.0,
) -> list[dict[str, Any]]:
    """
    Load ``pTable.json``-shaped data (list of element dicts).

    If ``cache_path`` is set, read from disk when present; otherwise download and optionally write.
    """
    if cache_path is not None:
        cache_path = Path(cache_path)
        if cache_path.is_file():
            return json.loads(cache_path.read_text(encoding="utf-8"))

    req = urllib.request.Request(url, headers={"User-Agent": "periodic-stability/0.1"})
    try:
        with urllib.request.urlopen(req, timeout=timeout_s) as resp:
            raw = resp.read()
    except urllib.error.URLError as e:
        raise RuntimeError(f"Failed to download periodic table data from {url!r}: {e}") from e

    text = raw.decode("utf-8")
    data = json.loads(text)
    if cache_path is not None:
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        tmp = cache_path.with_suffix(cache_path.suffix + ".tmp")
        tmp.write_text(text, encoding="utf-8")
        os.replace(tmp, cache_path)
    return data
