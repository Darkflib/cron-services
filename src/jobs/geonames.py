"""Geonames data sync job."""

import logging
from pathlib import Path

from .base import BaseJob

logger = logging.getLogger(__name__)


class GeonamesJob(BaseJob):
    """Download Geonames geographical database and upload to GCS."""

    URLS_FILE = "geonames-urls.txt"

    @property
    def name(self) -> str:
        return "geonames"

    @property
    def gcs_prefix(self) -> str:
        return "geonames"

    def _load_urls(self) -> list[str]:
        """Load URLs from configuration file."""
        urls_file = Path(__file__).parent.parent.parent / self.URLS_FILE
        if not urls_file.exists():
            error_msg = "Geonames URLs configuration file not found: " + str(urls_file)
            raise FileNotFoundError(error_msg)
        # Read and split the file, then filter out empty/whitespace-only entries
        urls = [url.strip() for url in urls_file.read_text().split("\n") if url.strip()]
        if not urls:
            error_msg = "No URLs found in " + str(urls_file)
            raise ValueError(error_msg)
        return urls

    async def execute(self, work_dir: Path) -> dict:
        """Download Geonames data and upload to GCS."""

        # Load URLs from file
        urls = self._load_urls()
        logger.info("Loaded %d URLs from %s", len(urls), self.URLS_FILE)

        # Download files with more parallelism
        downloaded = await self.downloader.download_urls(urls, work_dir, max_concurrent=6)

        # Upload to GCS
        uploaded = self.uploader.upload_directory(work_dir, self.gcs_prefix)

        return {
            "downloaded": len(downloaded),
            "uploaded": len(uploaded),
            "files": [f.name for f in downloaded],
        }
