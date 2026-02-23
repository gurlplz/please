#!/usr/bin/env python3
"""
OpenClaw Insecure Instance Scanner

Custom crawler that discovers and fingerprints exposed OpenClaw instances
without using Shodan/Censys. Uses platform enumeration, CT logs, and GitHub.
"""

import argparse
import asyncio
import json
import os
import sys
from pathlib import Path

# Ensure we can import from project root
sys.path.insert(0, str(Path(__file__).resolve().parent))

from config import RESULTS_FILE
from discovery.platforms import PlatformEnumerator
from discovery.ct_logs import CTLogCrawler
from discovery.github import GitHubCrawler
from fetcher import OpenClawFetcher, ScanResult


async def run_discovery(sources: list[str], github_token: str | None) -> list[str]:
    """Run all discovery sources and collect URLs."""
    urls: set[str] = set()

    if "platforms" in sources:
        print("[*] Enumerating platform subdomains...")
        async for url in PlatformEnumerator().discover():
            urls.add(url)

    if "ct" in sources:
        print("[*] Querying Certificate Transparency (crt.sh)...")
        async for url in CTLogCrawler().discover():
            urls.add(url)

    if "github" in sources:
        print("[*] Searching GitHub for OpenClaw configs...")
        async for url in GitHubCrawler(token=github_token).discover():
            urls.add(url)

    return list(urls)


async def run_scan(urls: list[str], output_path: Path, batch_size: int = 50) -> list[ScanResult]:
    """Scan URLs and write results."""
    fetcher = OpenClawFetcher(max_concurrent=batch_size)
    results: list[ScanResult] = []
    found: list[ScanResult] = []

    with open(output_path, "a") as f:
        for i in range(0, len(urls), batch_size):
            batch = urls[i : i + batch_size]
            print(f"[*] Scanning {i + 1}-{i + len(batch)} / {len(urls)}...")
            batch_results = await fetcher.fetch_batch(batch)
            for r in batch_results:
                results.append(r)
                if r.is_openclaw:
                    found.append(r)
                    line = json.dumps({
                        "url": r.url,
                        "confidence": r.confidence,
                        "signals": r.signals,
                        "status_code": r.status_code,
                    }) + "\n"
                    f.write(line)
                    f.flush()
                    print(f"    [+] FOUND: {r.url} (confidence={r.confidence:.2f})")

    return found


async def main():
    parser = argparse.ArgumentParser(description="OpenClaw insecure instance scanner")
    parser.add_argument(
        "--sources",
        nargs="+",
        default=["platforms", "ct", "github"],
        choices=["platforms", "ct", "github"],
        help="Discovery sources to use",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=Path,
        default=Path(RESULTS_FILE),
        help="Output file for results (JSONL)",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=50,
        help="Concurrent requests per batch",
    )
    parser.add_argument(
        "--github-token",
        default=os.environ.get("GITHUB_TOKEN"),
        help="GitHub token for higher rate limits (optional, or set GITHUB_TOKEN)",
    )
    parser.add_argument(
        "--discovery-only",
        action="store_true",
        help="Only run discovery, don't scan",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Limit number of URLs to scan (for testing)",
    )
    args = parser.parse_args()

    print("[*] OpenClaw Insecure Instance Scanner")
    print("[*] Using custom crawlers (no Shodan/Censys)")

    urls = await run_discovery(args.sources, args.github_token)
    if args.limit:
        urls = urls[: args.limit]
        print(f"[*] Limited to {args.limit} URLs")
    print(f"[*] Discovered {len(urls)} candidate URLs")

    if not urls:
        print("[!] No URLs to scan. Try different sources or check connectivity.")
        return 1

    if args.discovery_only:
        for u in urls[:100]:
            print(f"  {u}")
        if len(urls) > 100:
            print(f"  ... and {len(urls) - 100} more")
        return 0

    args.output.parent.mkdir(parents=True, exist_ok=True)
    found = await run_scan(urls, args.output, args.batch_size)

    print(f"\n[*] Done. Found {len(found)} OpenClaw instances. Results in {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
