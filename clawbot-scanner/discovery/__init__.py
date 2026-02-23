"""URL discovery modules for OpenClaw instances."""

from .platforms import PlatformEnumerator
from .ct_logs import CTLogCrawler
from .github import GitHubCrawler

__all__ = ["PlatformEnumerator", "CTLogCrawler", "GitHubCrawler"]
