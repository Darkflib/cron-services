"""MaxMind GeoIP data sync job."""

import logging
from pathlib import Path
from urllib.parse import urlparse, parse_qs, urlunparse, urlencode

from ..config import settings
from .base import BaseJob

logger = logging.getLogger(__name__)


def _sanitize_url(url: str) -> str:
    """Remove or mask sensitive query parameters from URL for logging.

    Args:
        url: URL to sanitize

    Returns:
        Sanitized URL with sensitive parameters masked
    """
    parsed = urlparse(url)
    if not parsed.query:
        return url

    query_params = parse_qs(parsed.query)
    # Mask common sensitive parameters
    sensitive_params = {"license_key", "license_key", "key", "token", "auth"}
    for param in sensitive_params:
        if param in query_params:
            query_params[param] = ["***"]

    sanitized_query = urlencode(query_params, doseq=True)
    sanitized = urlunparse((parsed.scheme, parsed.netloc, parsed.path,
                           parsed.params, sanitized_query, parsed.fragment))
    return sanitized


class MaxMindJob(BaseJob):
    """Download MaxMind GeoLite2 databases and upload to GCS."""

    URLS_FILE = "maxmind-urls.txt"

    def __init__(self):
        """Initialize job with downloader that hides sensitive URLs."""
        super().__init__()
        # Override downloader to prevent logging URLs with license keys
        self.downloader = FileDownloader(log_urls=False)

    @property
    def name(self) -> str:
        return "maxmind"

    @property
    def gcs_prefix(self) -> str:
        return "maxmind"

    def _load_urls(self) -> list[str]:
        """Load URLs from configuration file and inject license key."""
        # Validate license key first (fail fast)
        license_key = settings.maxmind_license_key
        if not license_key:
            msg = "MaxMind license key not configured"
            raise ValueError(msg)

        urls_file = Path(__file__).parent.parent.parent / self.URLS_FILE
        if not urls_file.exists():
            error_msg = "MaxMind URLs file not found: " + str(urls_file)
            raise FileNotFoundError(error_msg)

        # Read and split the file, then filter out empty/whitespace-only entries
        urls = [url.strip().replace("YOUR_LICENSE_KEY", license_key) for url in urls_file.read_text().split("\n") if url.strip()]
        if not urls:
            error_msg = "No URLs found in " + str(urls_file)
            raise ValueError(error_msg)
        return urls

    async def execute(self, work_dir: Path) -> dict:
        """Download MaxMind data and upload to GCS."""

        # Load URLs with license key injected
        urls = self._load_urls()
        logger.info("Loaded %d URLs from %s", len(urls), self.URLS_FILE)

        # Sanitize URLs for logging (license key is masked)
        for url in urls:
            logger.info("Downloading: %s", _sanitize_url(url))

        # Download files
        downloaded = await self.downloader.download_urls(urls, work_dir, max_concurrent=4)

        # Upload to GCS
        uploaded = self.uploader.upload_directory(work_dir, self.gcs_prefix)

        return {
            "downloaded": len(downloaded),
            "uploaded": len(uploaded),
            "files": [f.name for f in downloaded],
        }
