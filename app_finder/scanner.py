from __future__ import annotations

import os

from .models import AppHit, ScanReport

DEFAULT_IGNORE_DIRS: frozenset[str] = frozenset(
    {
        ".git",
        ".hg",
        ".svn",
        "__pycache__",
        ".venv",
        "venv",
        ".tox",
        "node_modules",
        "bower_components",
        "dist",
        "build",
        "target",
        ".next",
        ".nuxt",
        ".cache",
        "vendor",
    }
)

# Marker file -> application kind (first match wins per directory).
MARKERS: tuple[tuple[str, str], ...] = (
    ("docker-compose.yml", "docker_compose"),
    ("docker-compose.yaml", "docker_compose"),
    ("compose.yml", "docker_compose"),
    ("compose.yaml", "docker_compose"),
    ("Dockerfile", "docker_image"),
    ("pyproject.toml", "python"),
    ("setup.py", "python"),
    ("setup.cfg", "python"),
    ("Pipfile", "python"),
    ("requirements.txt", "python"),
    ("manage.py", "django"),
    ("streamlit_app.py", "streamlit"),
    (".streamlit/config.toml", "streamlit"),
    ("package.json", "node"),
    ("Cargo.toml", "rust"),
    ("go.mod", "go"),
    ("pom.xml", "java_maven"),
    ("build.gradle", "java_gradle"),
    ("build.gradle.kts", "java_gradle"),
    ("Gemfile", "ruby"),
    ("composer.json", "php"),
    ("mix.exs", "elixir"),
    ("flake.nix", "nix"),
    ("Chart.yaml", "helm_chart"),
)


def _markers_in_dir(dirpath: str) -> tuple[str, ...]:
    found: list[str] = []
    for name, _kind in MARKERS:
        candidate = os.path.join(dirpath, name)
        if os.path.isfile(candidate) or (name.startswith(".") and os.path.isdir(candidate)):
            found.append(name)
    return tuple(found)


def _classify_dir(dirpath: str, markers: tuple[str, ...]) -> tuple[str, str]:
    """Return (kind, notes)."""
    marker_set = set(markers)
    if "manage.py" in marker_set:
        return "django", "manage.py"
    if ".streamlit/config.toml" in marker_set or "streamlit_app.py" in marker_set:
        return "streamlit", "streamlit markers"
    if "docker-compose.yml" in marker_set or "docker-compose.yaml" in marker_set:
        return "docker_compose", "compose file"
    if "compose.yml" in marker_set or "compose.yaml" in marker_set:
        return "docker_compose", "compose v2 file"
    if "Dockerfile" in marker_set and not (
        marker_set
        & {
            "pyproject.toml",
            "package.json",
            "go.mod",
            "Cargo.toml",
            "pom.xml",
        }
    ):
        return "docker_image", "Dockerfile only"
    if "package.json" in marker_set:
        return "node", "package.json"
    if "Cargo.toml" in marker_set:
        return "rust", "Cargo.toml"
    if "go.mod" in marker_set:
        return "go", "go.mod"
    if "pom.xml" in marker_set:
        return "java_maven", "pom.xml"
    if "build.gradle" in marker_set or "build.gradle.kts" in marker_set:
        return "java_gradle", "gradle build"
    if "pyproject.toml" in marker_set or "setup.py" in marker_set or "Pipfile" in marker_set:
        return "python", "python packaging"
    if "requirements.txt" in marker_set:
        return "python", "requirements.txt"
    return "unknown", "unclassified markers"


def discover(
    roots: Iterable[str],
    *,
    ignore_dirs: frozenset[str] | None = None,
    max_depth: int | None = None,
) -> ScanReport:
    """
    Walk each root and emit one AppHit per directory that contains marker files.

    ``max_depth`` is relative to each root (0 = root only, None = unlimited).
    """
    ign = ignore_dirs or DEFAULT_IGNORE_DIRS
    norm_roots = tuple(os.path.abspath(os.path.expanduser(r)) for r in roots)
    hits: list[AppHit] = []
    seen: set[str] = set()

    def walk(root: str, depth: int) -> None:
        root = os.path.abspath(os.path.expanduser(root))
        if not os.path.isdir(root):
            return
        try:
            entries = os.listdir(root)
        except OSError:
            return
        markers = _markers_in_dir(root)
        if markers:
            kind, notes = _classify_dir(root, markers)
            real = os.path.realpath(root)
            if real not in seen:
                seen.add(real)
                hits.append(AppHit(path=real, kind=kind, markers=markers, notes=notes))
        if max_depth is not None and depth >= max_depth:
            return
        for name in entries:
            if name in ign:
                continue
            path = os.path.join(root, name)
            if os.path.islink(path):
                try:
                    path = os.path.realpath(path)
                except OSError:
                    continue
            if not os.path.isdir(path):
                continue
            walk(path, depth + 1)

    for r in norm_roots:
        walk(r, 0)

    hits.sort(key=lambda h: h.path)
    return ScanReport(roots=norm_roots, hits=tuple(hits), ignored_dirs=tuple(sorted(ign)))
