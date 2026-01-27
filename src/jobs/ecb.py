"""ECB (European Central Bank) forex data sync job."""

import logging
from pathlib import Path

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

    async def execute(self, work_dir: Path) -> dict:
        """Download ECB data and upload to GCS."""

        # Download files
        downloaded = await self.downloader.download_urls(self.URLS, work_dir)
        failed_downloads = [d for d in downloaded if isinstance(d, Exception)]
        successful_downloads = [d for d in downloaded if not isinstance(d, Exception)]

        # Upload to GCS
        if failed_downloads:
            logger.error("%d downloads failed: %s", len(failed_downloads), list(failed_downloads))
        uploaded = self.uploader.upload_directory(work_dir, self.gcs_prefix)

        result = {
            "downloaded": len(successful_downloads),
            "uploaded": len(uploaded),
            "files": [f.name for f in successful_downloads],
        }

        if failed_downloads:
            result["errors"] = [str(e) for e in failed_downloads]

        return result
