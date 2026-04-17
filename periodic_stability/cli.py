from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .analyze import load_rows_json, summarize, write_csv
from .compute import build_rows
from .constants import DEFAULT_DATA_URL
from .data import fetch_periodic_table_json


def _cmd_build(args: argparse.Namespace) -> int:
    elements = fetch_periodic_table_json(
        args.url,
        cache_path=args.cache,
        timeout_s=args.timeout,
    )
    rows = build_rows(elements)
    payload = [r.to_json_dict() for r in rows]
    out = Path(args.output)
    out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    if args.csv:
        write_csv(rows, args.csv)
    print(
        f"Wrote {len(rows)} element row(s) to {out}"
        + (f" and {args.csv}" if args.csv else ""),
        file=sys.stderr,
    )
    return 0


def _cmd_analyze(args: argparse.Namespace) -> int:
    rows = load_rows_json(args.input)
    summary = summarize(rows)
    text = json.dumps(summary, indent=2)
    if args.output:
        Path(args.output).write_text(text + "\n", encoding="utf-8")
    else:
        print(text)
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        description=(
            "Build a table of Periodic Stability metrics (PSI = IE1/r, volumetric IE/V, "
            "Mulliken/hardness-style combinations) and analyze exported JSON."
        ),
    )
    sub = p.add_subparsers(dest="cmd", required=True)

    b = sub.add_parser("build", help="Download periodic data and write computed rows as JSON.")
    b.add_argument(
        "-o",
        "--output",
        default="periodic_stability_rows.json",
        help="Output JSON path (default: periodic_stability_rows.json).",
    )
    b.add_argument(
        "--csv",
        help="Optional CSV path with the same rows.",
    )
    b.add_argument(
        "--url",
        default=DEFAULT_DATA_URL,
        help="URL to pTable.json-compatible data.",
    )
    b.add_argument(
        "--cache",
        default=None,
        help="Optional path to cache downloaded JSON for offline reuse.",
    )
    b.add_argument(
        "--timeout",
        type=float,
        default=60.0,
        help="HTTP timeout in seconds.",
    )
    b.set_defaults(func=_cmd_build)

    a = sub.add_parser("analyze", help="Summarize a rows JSON file from build.")
    a.add_argument("input", help="Input JSON path produced by build.")
    a.add_argument(
        "-o",
        "--output",
        help="Write summary JSON to this path (default: print to stdout).",
    )
    a.set_defaults(func=_cmd_analyze)

    ns = p.parse_args(argv)
    return int(ns.func(ns))


if __name__ == "__main__":
    raise SystemExit(main())
