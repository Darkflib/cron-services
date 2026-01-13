"""MaxMind GeoIP data sync job."""

import logging
from pathlib import Path

from ..config import settings
from .base import BaseJob

logger = logging.getLogger(__name__)


class MaxMindJob(BaseJob):
    """Download MaxMind GeoLite2 databases and upload to GCS."""

    URLS_FILE = "maxmind-urls.txt"

    @property
    def name(self) -> str:
        return "maxmind"

    @property
    def gcs_prefix(self) -> str:
        return "maxmind"

    def _load_urls(self) -> list[str]:
        """Load URLs from configuration file and inject license key."""
        urls_file = Path(__file__).parent.parent.parent / self.URLS_FILE
        urls = urls_file.read_text().strip().split("\n")

        # Replace placeholder with actual license key
        license_key = settings.maxmind_license_key
        if not license_key:
            msg = "MaxMind license key not configured"
            raise ValueError(msg)

        return [url.strip().replace("YOUR_LICENSE_KEY", license_key) for url in urls if url.strip()]

    async def execute(self) -> dict:
        """Download MaxMind data and upload to GCS."""
        work_dir = self._create_work_dir()

        # Load URLs with license key injected
        urls = self._load_urls()
        logger.info(f"Loaded {len(urls)} URLs from {self.URLS_FILE}")

        # Download files
        downloaded = await self.downloader.download_urls(urls, work_dir, max_concurrent=4)

        # Upload to GCS
        uploaded = self.uploader.upload_directory(work_dir, self.gcs_prefix)

        return {
            "downloaded": len(downloaded),
            "uploaded": len(uploaded),
            "files": [f.name for f in downloaded],
        }
