# Application discovery tools

Small Python utilities to **find software projects** on disk (by common marker files such as `package.json`, `pyproject.toml`, or `Dockerfile`) and **analyze** the JSON reports the scanner produces.

## Install

```bash
pip install -e .
```

## Discover

Scan one or more roots and write a machine-readable report:

```bash
app-finder discover /path/to/code -o scan.json
```

Optional flags:

- `--max-depth N` — limit recursion depth under each root.
- `--extra-ignore dirname` — add directory names to skip (defaults include `node_modules`, `.git`, `venv`, and others).

## Analyze

Summarize a report (counts by kind, marker frequency):

```bash
app-finder analyze scan.json
```

Export artifacts:

```bash
app-finder analyze scan.json -o summary.json --hits-csv apps.csv --kind-csv kinds.csv
```

## Library use

```python
from app_finder.scanner import discover
from app_finder.analyze import summarize_report

report = discover(["/path/to/code"])
summary = summarize_report(report)
```

## Notes

- Detection is **heuristic**: a directory is listed if it contains recognizable marker files. Nested projects each appear as separate hits.
- Classification prefers more specific markers (for example `manage.py` for Django) when multiple markers coexist.
