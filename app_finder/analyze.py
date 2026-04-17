from __future__ import annotations

import csv
import json
from collections import Counter
from collections.abc import Iterable
from pathlib import Path

from .models import AppHit, ScanReport


def load_report(path: str | Path) -> ScanReport:
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    return ScanReport.from_json(raw)


def summarize_hits(hits: Iterable[AppHit]) -> dict[str, object]:
    hit_list = list(hits)
    kinds = Counter(h.kind for h in hit_list)
    markers = Counter(m for h in hit_list for m in h.markers)
    return {
        "total_apps": len(hit_list),
        "by_kind": dict(sorted(kinds.items(), key=lambda kv: (-kv[1], kv[0]))),
        "marker_frequency": dict(sorted(markers.items(), key=lambda kv: (-kv[1], kv[0]))),
    }


def summarize_report(report: ScanReport) -> dict[str, object]:
    hits = list(report.hits)
    kinds = Counter(h.kind for h in hits)
    markers = Counter(m for h in hits for m in h.markers)
    return {
        "roots": list(report.roots),
        "total_apps": len(hits),
        "by_kind": dict(sorted(kinds.items(), key=lambda kv: (-kv[1], kv[0]))),
        "marker_frequency": dict(sorted(markers.items(), key=lambda kv: (-kv[1], kv[0]))),
        "ignored_dir_count": len(report.ignored_dirs),
    }


def write_kind_csv(summary: dict[str, object], out_path: str | Path) -> None:
    out_path = Path(out_path)
    rows = list((summary.get("by_kind") or {}).items())
    with out_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["kind", "count"])
        for kind, count in rows:
            w.writerow([kind, count])


def write_hits_csv(hits: Iterable[AppHit], out_path: str | Path) -> None:
    out_path = Path(out_path)
    with out_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(
            f,
            fieldnames=["path", "kind", "markers", "notes"],
        )
        w.writeheader()
        for h in hits:
            w.writerow(
                {
                    "path": h.path,
                    "kind": h.kind,
                    "markers": ";".join(h.markers),
                    "notes": h.notes,
                }
            )
