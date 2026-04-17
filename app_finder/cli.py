from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .analyze import load_report, summarize_report, write_hits_csv, write_kind_csv
from .scanner import DEFAULT_IGNORE_DIRS, discover


def _cmd_discover(args: argparse.Namespace) -> int:
    roots = list(args.root)
    ign = frozenset(DEFAULT_IGNORE_DIRS)
    if args.extra_ignore:
        ign = frozenset(ign | set(args.extra_ignore))
    report = discover(roots, ignore_dirs=ign, max_depth=args.max_depth)
    out = Path(args.output)
    out.write_text(json.dumps(report.to_json(), indent=2), encoding="utf-8")
    print(f"Wrote {len(report.hits)} application(s) to {out}", file=sys.stderr)
    return 0


def _cmd_analyze(args: argparse.Namespace) -> int:
    report = load_report(args.input)
    summary = summarize_report(report)
    text = json.dumps(summary, indent=2)
    if args.output:
        Path(args.output).write_text(text + "\n", encoding="utf-8")
    else:
        print(text)
    if args.hits_csv:
        write_hits_csv(report.hits, args.hits_csv)
    if args.kind_csv:
        write_kind_csv(summary, args.kind_csv)
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        description="Discover applications by marker files and analyze JSON scan reports.",
    )
    sub = p.add_subparsers(dest="cmd", required=True)

    d = sub.add_parser("discover", help="Scan directories and write a JSON report.")
    d.add_argument("root", nargs="+", help="Root directory(ies) to scan.")
    d.add_argument(
        "-o",
        "--output",
        required=True,
        help="Output JSON path (scan report).",
    )
    d.add_argument(
        "--max-depth",
        type=int,
        default=None,
        help="Maximum depth below each root (default: unlimited).",
    )
    d.add_argument(
        "--extra-ignore",
        nargs="*",
        default=(),
        help="Additional directory names to skip while walking.",
    )
    d.set_defaults(func=_cmd_discover)

    a = sub.add_parser("analyze", help="Summarize a JSON report from discover.")
    a.add_argument("input", help="Scan report JSON path.")
    a.add_argument(
        "-o",
        "--output",
        help="Write summary JSON to this path (default: print to stdout).",
    )
    a.add_argument(
        "--hits-csv",
        help="Optional path to write one row per detected application.",
    )
    a.add_argument(
        "--kind-csv",
        help="Optional path to write counts grouped by application kind.",
    )
    a.set_defaults(func=_cmd_analyze)

    ns = p.parse_args(argv)
    return int(ns.func(ns))


if __name__ == "__main__":
    raise SystemExit(main())
