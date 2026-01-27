"""Ofcom UK telephone numbering data sync job."""

import logging
from pathlib import Path

from .base import BaseJob

logger = logging.getLogger(__name__)


class OfcomJob(BaseJob):
    """Download Ofcom codelist and upload to GCS."""

    URLS_FILE = "ofcom-urls.txt"

    @property
    def name(self) -> str:
        return "ofcom"

    @property
    def gcs_prefix(self) -> str:
        return "codelist"

    def _load_urls(self) -> list[str]:
        """Load URLs from configuration file."""
        urls_file = Path(__file__).parent.parent.parent / self.URLS_FILE
        if not urls_file.exists():
            error_msg = "URL configuration file not found: " + str(urls_file)
            raise FileNotFoundError(error_msg)
        # Read and split the file, then filter out empty/whitespace-only entries
        urls = [url.strip() for url in urls_file.read_text().split("\n") if url.strip()]
        if not urls:
            error_msg = "No URLs found in " + str(urls_file)
            raise ValueError(error_msg)
        return urls

    async def execute(self, work_dir: Path) -> dict:
        """Download Ofcom data and upload to GCS."""

        # Load URLs from file
        urls = self._load_urls()
        logger.info("Loaded %d URLs from %s", len(urls), self.URLS_FILE)

        # Download files
        downloaded = await self.downloader.download_urls(urls, work_dir)

        # Upload to GCS
        uploaded = self.uploader.upload_directory(work_dir, self.gcs_prefix)

        return {
            "downloaded": len(downloaded),
            "uploaded": len(uploaded),
            "files": [f.name for f in downloaded],
        }
