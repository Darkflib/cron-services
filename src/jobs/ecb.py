"""ECB (European Central Bank) forex data sync job."""

import logging

from .base import BaseJob

logger = logging.getLogger(__name__)


class ECBJob(BaseJob):
    """Download ECB forex reference rates and upload to GCS."""

    URLS = [
        "https://www.ecb.europa.eu/stats/eurofxref/eurofxref-daily.xml",
        "https://www.ecb.europa.eu/stats/eurofxref/eurofxref.zip",
        "https://www.ecb.europa.eu/stats/eurofxref/eurofxref-hist-90d.xml",
    ]

    @property
    def name(self) -> str:
        return "ecb"

    @property
    def gcs_prefix(self) -> str:
        return "ecb"

    async def execute(self) -> dict:
        """Download ECB data and upload to GCS."""
        work_dir = self._create_work_dir()

        # Download files
        downloaded = await self.downloader.download_urls(self.URLS, work_dir)

        # Upload to GCS
        uploaded = self.uploader.upload_directory(work_dir, self.gcs_prefix)

        return {
            "downloaded": len(downloaded),
            "uploaded": len(uploaded),
            "files": [f.name for f in downloaded],
        }
