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


def _prioritize_urls(urls: list[str]) -> list[str]:
    """Sort URLs: OpenClaw-related subdomains first, then by platform likelihood."""
    def score(url: str) -> tuple[int, str]:
        lower = url.lower()
        # Priority keywords in subdomain
        if "openclaw" in lower: return (0, url)
        if "clawbot" in lower or "clawctl" in lower: return (1, url)
        if "claw" in lower or "molt" in lower: return (2, url)
        # Platform priority (railway, render most common)
        if "railway" in lower: return (3, url)
        if "onrender" in lower: return (4, url)
        if "fly.dev" in lower: return (5, url)
        return (6, url)
    return [u for _, u in sorted((score(u), u) for u in urls)]


async def run_discovery_parallel(sources: list[str], github_token: str | None) -> list[str]:
    """Run discovery sources in parallel and merge results."""
    urls: set[str] = set()

    async def collect(agen, name: str) -> list[str]:
        out = []
        try:
            async for u in agen:
                out.append(u)
        except Exception as e:
            print(f"    {name}: Error - {e}")
        return out

    tasks = []
    if "platforms" in sources:
        tasks.append(("platforms", collect(PlatformEnumerator().discover(), "platforms")))
    if "ct" in sources:
        tasks.append(("ct", collect(CTLogCrawler().discover(), "ct")))
    if "github" in sources:
        tasks.append(("github", collect(GitHubCrawler(token=github_token).discover(), "github")))

    print("[*] Running discovery (parallel)...")
    results = await asyncio.gather(*[t[1] for t in tasks])
    for (name, _), result in zip(tasks, results):
        for u in result:
            urls.add(u)
        print(f"    {name}: +{len(result)} URLs")

    return list(urls)


async def run_scan(
    urls: list[str],
    output_path: Path,
    batch_size: int = 50,
    show_progress: bool = True,
) -> list[ScanResult]:
    """Scan URLs and write results."""
    fetcher = OpenClawFetcher(max_concurrent=batch_size)
    found: list[ScanResult] = []

    try:
        from tqdm import tqdm
        iterator = tqdm(
            range(0, len(urls), batch_size),
            desc="Scanning",
            unit="batch",
            disable=not show_progress,
        )
    except ImportError:
        iterator = range(0, len(urls), batch_size)

    with open(output_path, "a") as f:
        for i in iterator:
            batch = urls[i : i + batch_size]
            if not hasattr(iterator, "set_postfix"):
                print(f"[*] Scanning {i + 1}-{i + len(batch)} / {len(urls)}...")

            batch_results = await fetcher.fetch_batch(batch)
            for r in batch_results:
                if r.is_openclaw:
                    found.append(r)
                    record = {
                        "url": r.url,
                        "confidence": r.confidence,
                        "signals": r.signals,
                        "status_code": r.status_code,
                        "insecure": r.insecure,
                    }
                    f.write(json.dumps(record) + "\n")
                    f.flush()
                    insecure_tag = " [INSECURE]" if r.insecure else ""
                    print(f"    [+] FOUND: {r.url} (conf={r.confidence:.2f}){insecure_tag}")

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
    parser.add_argument(
        "--no-progress",
        action="store_true",
        help="Disable progress bar",
    )
    args = parser.parse_args()

    print("[*] OpenClaw Insecure Instance Scanner")
    print("[*] Custom crawlers (no Shodan/Censys)")

    urls = await run_discovery_parallel(args.sources, args.github_token)
    urls = _prioritize_urls(urls)

    if args.limit:
        urls = urls[: args.limit]
        print(f"[*] Limited to {args.limit} URLs")
    print(f"[*] Total: {len(urls)} candidate URLs")

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
    found = await run_scan(
        urls, args.output, args.batch_size, show_progress=not args.no_progress
    )

    insecure_count = sum(1 for r in found if r.insecure)
    print(f"\n[*] Done. Found {len(found)} OpenClaw instances ({insecure_count} insecure)")
    print(f"[*] Results: {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
