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
from discovery.ip_discovery import IPDiscovery
from enumerator import InsecureEnumerator
from fetcher import OpenClawFetcher, ScanResult


def _prioritize_urls(urls: list[str]) -> list[str]:
    """Sort URLs: OpenClaw-related subdomains first, then by platform likelihood."""
    def score(url: str) -> tuple[int, str]:
        lower = url.lower()
        # Priority keywords in subdomain
        if "openclaw" in lower: return (0, url)
        if "clawbot" in lower or "clawctl" in lower: return (1, url)
        if "claw" in lower or "molt" in lower: return (2, url)
        # Direct IPs - prioritize (often find more exposed instances)
        if "://" in url:
            host = url.split("://", 1)[1].split("/")[0].split(":")[0]
            if host and host[0].isdigit():
                return (2, url)
        # Platform priority
        if "railway" in lower: return (3, url)
        if "onrender" in lower: return (4, url)
        if "fly.dev" in lower: return (5, url)
        if "netlify" in lower or "pages.dev" in lower: return (5, url)
        return (6, url)
    return [u for _, u in sorted((score(u), u) for u in urls)]


async def run_discovery_parallel(
    sources: list[str],
    github_token: str | None,
    platforms: list[str] | None = None,
    wordlist_path: Path | str | None = None,
    url_file: Path | str | None = None,
    ip_file: Path | str | None = None,
    fetch_cloud_ips: bool = False,
) -> list[str]:
    """Run discovery sources in parallel and merge results."""
    urls: set[str] = set()

    # Custom URL file
    if url_file:
        path = Path(url_file)
        if path.exists():
            custom = [
                line.strip() for line in path.read_text().splitlines()
                if line.strip() and (line.startswith("http://") or line.startswith("https://"))
            ]
            for u in custom:
                urls.add(u)
            print(f"    url-file: +{len(custom)} URLs")

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
        enum = PlatformEnumerator(
            platforms=platforms,
            wordlist_path=wordlist_path,
        )
        tasks.append(("platforms", collect(enum.discover(), "platforms")))
    if "ct" in sources:
        tasks.append(("ct", collect(CTLogCrawler().discover(), "ct")))
    if "github" in sources:
        tasks.append(("github", collect(GitHubCrawler(token=github_token).discover(), "github")))
    if "ip" in sources or ip_file or fetch_cloud_ips:
        ip_discovery = IPDiscovery(
            ip_file=ip_file,
            fetch_cloud=fetch_cloud_ips,
        )
        tasks.append(("ip", collect(ip_discovery.discover(), "ip")))

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


async def run_enumeration(
    insecure_urls: list[str],
    output_path: Path,
) -> int:
    """Enumerate data from insecure instances."""
    enumerator = InsecureEnumerator()
    count = 0

    for url in insecure_urls:
        try:
            data = await enumerator.enumerate(url)
            record = enumerator.to_dict(data)
            with open(output_path, "a") as f:
                f.write(json.dumps(record, default=str) + "\n")
            count += 1
            print(f"    [ENUM] {url}")
        except Exception as e:
            print(f"    [ENUM] {url}: ERROR - {e}")

    return count


async def main():
    parser = argparse.ArgumentParser(description="OpenClaw insecure instance scanner")
    parser.add_argument(
        "--sources",
        nargs="+",
        default=["platforms", "ct", "github"],
        choices=["platforms", "ct", "github", "ip"],
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
    parser.add_argument(
        "--platforms",
        nargs="+",
        default=None,
        help="Platforms to enumerate (default: all). E.g. railway render vercel",
    )
    parser.add_argument(
        "--wordlist",
        type=Path,
        default=None,
        help="Custom subdomain wordlist file (one per line)",
    )
    parser.add_argument(
        "--url-file",
        type=Path,
        default=None,
        help="File with custom URLs to scan (one per line, http/https)",
    )
    parser.add_argument(
        "--ip-file",
        type=Path,
        default=None,
        help="File with IPs to scan (one per line, expands to IP:port for 3000,18789,8080,5000,80,443)",
    )
    parser.add_argument(
        "--fetch-cloud-ips",
        action="store_true",
        help="Fetch AWS IP ranges and sample for scanning (adds IP discovery)",
    )
    parser.add_argument(
        "--enumerate",
        action="store_true",
        help="Enumerate data from insecure instances (endpoints, config, etc.)",
    )
    parser.add_argument(
        "--enum-output",
        type=Path,
        default=Path("enumerated.jsonl"),
        help="Output file for enumerated data (default: enumerated.jsonl)",
    )
    parser.add_argument(
        "--enumerate-from",
        type=Path,
        default=None,
        help="Enumerate from existing results file (skip scan, only enumerate insecure)",
    )
    args = parser.parse_args()

    print("[*] OpenClaw Insecure Instance Scanner")
    print("[*] Custom crawlers (no Shodan/Censys)")

    # Enumerate-only mode (from existing results)
    if args.enumerate_from and args.enumerate_from.exists():
        insecure_urls = []
        for line in args.enumerate_from.read_text().splitlines():
            if not line.strip():
                continue
            try:
                rec = json.loads(line)
                if rec.get("insecure") and rec.get("url"):
                    insecure_urls.append(rec["url"])
            except json.JSONDecodeError:
                continue
        insecure_urls = list(dict.fromkeys(insecure_urls))
        if insecure_urls:
            print(f"[*] Enumerating {len(insecure_urls)} insecure instances from {args.enumerate_from}")
            args.enum_output.parent.mkdir(parents=True, exist_ok=True)
            await run_enumeration(insecure_urls, args.enum_output)
            print(f"[*] Done. Output: {args.enum_output}")
        else:
            print("[!] No insecure instances in file")
        return 0

    urls = await run_discovery_parallel(
        args.sources,
        args.github_token,
        platforms=args.platforms,
        wordlist_path=args.wordlist,
        url_file=args.url_file,
        ip_file=args.ip_file,
        fetch_cloud_ips=args.fetch_cloud_ips,
    )
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
    insecure_urls = [r.url for r in found if r.insecure]

    if args.enumerate and insecure_urls:
        print(f"\n[*] Enumerating data from {len(insecure_urls)} insecure instances...")
        args.enum_output.parent.mkdir(parents=True, exist_ok=True)
        enum_count = await run_enumeration(insecure_urls, args.enum_output)
        print(f"    Enumerated {enum_count} instances -> {args.enum_output}")

    print(f"\n[*] Done. Found {len(found)} OpenClaw instances ({insecure_count} insecure)")
    print(f"[*] Results: {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
