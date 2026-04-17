from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class AppHit:
    """One detected application root."""

    path: str
    kind: str
    markers: tuple[str, ...] = ()
    notes: str = ""

    def to_json(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "kind": self.kind,
            "markers": list(self.markers),
            "notes": self.notes,
        }

    @staticmethod
    def from_json(obj: dict[str, Any]) -> "AppHit":
        return AppHit(
            path=str(obj["path"]),
            kind=str(obj["kind"]),
            markers=tuple(obj.get("markers") or ()),
            notes=str(obj.get("notes") or ""),
        )


@dataclass
class ScanReport:
    roots: tuple[str, ...]
    hits: tuple[AppHit, ...]
    ignored_dirs: tuple[str, ...] = field(default_factory=tuple)

    def to_json(self) -> dict[str, Any]:
        return {
            "version": 1,
            "roots": list(self.roots),
            "ignored_dirs": list(self.ignored_dirs),
            "hits": [h.to_json() for h in self.hits],
        }

    @staticmethod
    def from_json(obj: dict[str, Any]) -> ScanReport:
        hits = tuple(AppHit.from_json(h) for h in obj.get("hits") or [])
        return ScanReport(
            roots=tuple(obj.get("roots") or ()),
            hits=hits,
            ignored_dirs=tuple(obj.get("ignored_dirs") or ()),
        )
