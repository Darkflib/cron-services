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
            raise FileNotFoundError(f"URL configuration file not found: {urls_file}")
        urls = urls_file.read_text().strip().split("\n")
        if not urls:
            raise ValueError(f"No URLs found in {urls_file}")
        return [url.strip() for url in urls if url.strip()]

    async def execute(self) -> dict:
        """Download Ofcom data and upload to GCS."""
        work_dir = self.temp_dir / self.name

        # Load URLs from file
        urls = self._load_urls()
        logger.info(f"Loaded {len(urls)} URLs from {self.URLS_FILE}")

        # Download files
        downloaded = await self.downloader.download_urls(urls, work_dir)

        # Upload to GCS
        uploaded = self.uploader.upload_directory(work_dir, self.gcs_prefix)

        return {
            "downloaded": len(downloaded),
            "uploaded": len(uploaded),
            "files": [f.name for f in downloaded],
        }
