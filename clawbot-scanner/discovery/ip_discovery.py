"""IP-based discovery - direct IP addresses where OpenClaw often runs exposed."""

import asyncio
import ipaddress
import random
from pathlib import Path
from typing import AsyncIterator

import httpx

from config import DEFAULT_PORTS

# Ports to probe on IPs (OpenClaw defaults + common web)
IP_PORTS = [3000, 18789, 8080, 5000, 80, 443]

# Cloud provider IP range URLs (public, free)
CLOUD_IP_SOURCES = {
    "aws": "https://ip-ranges.amazonaws.com/ip-ranges.json",
    # GCP/DO require different formats - AWS is largest, start there
}


def _parse_ip(line: str) -> str | None:
    """Extract IP from line. Supports IP, IP:port, CIDR."""
    line = line.strip().split("#")[0].strip()
    if not line:
        return None
    # IP:port - use just IP
    if ":" in line and not line.startswith("["):
        parts = line.rsplit(":", 1)
        if len(parts) == 2 and parts[1].isdigit():
            line = parts[0]
    try:
        ipaddress.ip_address(line)
        return line
    except ValueError:
        pass
    try:
        # CIDR - use first host
        net = ipaddress.ip_network(line, strict=False)
        return str(next(net.hosts())) if net.num_addresses > 2 else str(net.network_address)
    except ValueError:
        return None


def _sample_from_cidr(cidr: str, n: int = 5) -> list[str]:
    """Sample n random IPs from a CIDR block."""
    try:
        net = ipaddress.ip_network(cidr, strict=False)
        if net.num_addresses < 2:
            return [str(net.network_address)]
        addrs = list(net.hosts())
        if len(addrs) <= n:
            return [str(a) for a in addrs]
        return [str(random.choice(addrs)) for _ in range(n)]
    except ValueError:
        return []


class IPDiscovery:
    """Discovers OpenClaw instances on direct IP addresses."""

    def __init__(
        self,
        ip_file: Path | str | None = None,
        ports: list[int] | None = None,
        fetch_cloud: bool = False,
        cloud_sample: int = 500,
    ):
        self.ip_file = Path(ip_file) if ip_file else None
        self.ports = ports or IP_PORTS
        self.fetch_cloud = fetch_cloud
        self.cloud_sample = cloud_sample

    async def _get_cloud_ips(self) -> list[str]:
        """Fetch AWS IP ranges and sample."""
        ips: set[str] = set()
        async with httpx.AsyncClient(timeout=30) as client:
            try:
                resp = await client.get(CLOUD_IP_SOURCES["aws"])
                resp.raise_for_status()
                data = resp.json()
            except Exception as e:
                print(f"[IP] Error fetching cloud ranges: {e}")
                return []

            prefixes = data.get("prefixes", [])
            cidrs = [p["ip_prefix"] for p in prefixes if "ip_prefix" in p]
            # Sample from each CIDR - cap per CIDR to spread coverage
            per_cidr = max(1, self.cloud_sample // len(cidrs)) if cidrs else 0
            for cidr in cidrs[:200]:  # Limit CIDRs to avoid huge lists
                for ip in _sample_from_cidr(cidr, min(per_cidr, 3)):
                    ips.add(ip)
                if len(ips) >= self.cloud_sample:
                    break

        return list(ips)[: self.cloud_sample]

    async def discover(self) -> AsyncIterator[str]:
        """Yield http://IP:port URLs."""
        ips: set[str] = set()

        # From file
        if self.ip_file and self.ip_file.exists():
            for line in self.ip_file.read_text().splitlines():
                ip = _parse_ip(line)
                if ip:
                    ips.add(ip)

        # From cloud
        if self.fetch_cloud:
            cloud_ips = await self._get_cloud_ips()
            for ip in cloud_ips:
                ips.add(ip)

        for ip in ips:
            for port in self.ports:
                # Use http for direct IPs (avoids SSL cert issues)
                url = f"http://{ip}:{port}"
                yield url
                await asyncio.sleep(0)
