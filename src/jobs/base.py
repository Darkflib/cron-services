"""Base job class for all scheduled tasks."""

import logging
import shutil
from abc import ABC, abstractmethod
from pathlib import Path

from ..config import settings
from ..downloader import FileDownloader
from ..storage import GCSUploader

logger = logging.getLogger(__name__)


class BaseJob(ABC):
    """Base class for all scheduled jobs."""

    def __init__(self):
        """Initialize job with common dependencies."""
        self.downloader = FileDownloader()
        self.uploader = GCSUploader()
        self.temp_dir = Path(settings.temp_dir)

    @property
    @abstractmethod
    def name(self) -> str:
        """Job name."""

    @property
    @abstractmethod
    def gcs_prefix(self) -> str:
        """GCS path prefix for uploads."""

    @abstractmethod
    async def execute(self) -> dict:
        """Execute the job.

        Returns:
            Dict with job results
        """

    def _create_work_dir(self) -> Path:
        """Create a temporary work directory."""
        work_dir = self.temp_dir / self.name
        work_dir.mkdir(parents=True, exist_ok=True)
        return work_dir

    def _cleanup_work_dir(self, work_dir: Path) -> None:
        """Clean up temporary work directory."""
        try:
            if work_dir.exists():
                shutil.rmtree(work_dir)
                logger.info("Cleaned up %s", work_dir)
        except OSError as e:
            logger.warning("Failed to clean up %s: %s", work_dir, e)

    async def run(self) -> dict:
        """Run the job with setup and cleanup.

        Returns:
            Dict with job results and status
        """
        work_dir = self._create_work_dir()
        try:
            logger.info("Starting job: %s", self.name)
            result = await self.execute()
            logger.info("Completed job: %s", self.name)
            return {"status": "success", "job": self.name, **result}
        except Exception as e:
            logger.exception("Job %s failed: %s", self.name, e)
            return {"status": "error", "job": self.name, "error": str(e)}
        finally:
            self._cleanup_work_dir(work_dir)
