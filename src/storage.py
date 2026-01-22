"""Google Cloud Storage operations."""

import logging
import os
import shutil
from pathlib import Path
from unittest.mock import MagicMock

USE_LOCAL_MOCK = os.getenv("USE_LOCAL_MOCK", "").lower() in ("true", "1", "yes")

if USE_LOCAL_MOCK:
    print("⚠️ RUNNING IN LOCAL MOCK MODE - Writing to ./local_storage")
    storage = MagicMock()
    storage.Client = MagicMock

    GoogleAPIError = Exception
else:
    from google.cloud import storage
    from google.api_core.exceptions import GoogleAPIError

from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from .config import settings

logger = logging.getLogger(__name__)


class GCSUploader:
    """Handle uploads to Google Cloud Storage."""

    def __init__(
        self,
        bucket_name: str | None = None,
    ) -> None:
        """Initialize GCS client."""
        if USE_LOCAL_MOCK:
            self.client = storage.Client()
            self.bucket_name = bucket_name or "mock-bucket"
            self.bucket = self.client.bucket(self.bucket_name)
            self._mock_mode = True
        else:
            self.client = storage.Client(project=settings.gcp_project_id)
            self.bucket_name = bucket_name or settings.gcs_bucket
            self.bucket = self.client.bucket(self.bucket_name)
            self._mock_mode = False

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True,
        retry=retry_if_exception_type(GoogleAPIError),
    )
    def upload_file(self, local_path: Path, gcs_path: str) -> None:
        """Upload a file to GCS with retry logic.

        Args:
            local_path: Local file path to upload
            gcs_path: Destination path in GCS bucket

        Raises:
            FileNotFoundError: If local_path does not exist
        """
        if not local_path.exists():
            raise FileNotFoundError(f"Local file not found: {local_path}")

        # Ensure no double slash in GCS path
        gcs_path = gcs_path.lstrip("/")

        if self._mock_mode:
            local_storage_dir = Path("./local_storage")
            local_storage_dir.mkdir(exist_ok=True)
            dest_path = local_storage_dir / Path(local_path).name
            shutil.copy(local_path, dest_path)
            logger.info(f"Mock upload: {local_path} -> {dest_path}")
            logger.info(f"Uploaded {local_path.name} to gs://{self.bucket_name}/{gcs_path}")
        else:
            blob = self.bucket.blob(gcs_path)
            blob.upload_from_filename(str(local_path))
            logger.info(f"Uploaded {local_path.name} to gs://{self.bucket_name}/{gcs_path}")

    def upload_directory(self, local_dir: Path, gcs_prefix: str) -> list[str]:
        """Upload all files from a directory to GCS.

        Args:
            local_dir: Local directory path
            gcs_prefix: Prefix path in GCS bucket

        Returns:
            List of uploaded GCS paths

        Raises:
            NotADirectoryError: If local_dir is not a directory
        """
        if not local_dir.is_dir():
            raise NotADirectoryError(f"Not a directory: {local_dir}")

        # Ensure no double slash in GCS prefix
        gcs_prefix = gcs_prefix.rstrip("/")
        uploaded_files = []

        for file_path in local_dir.iterdir():
            if file_path.is_file():
                gcs_path = f"{gcs_prefix}/{file_path.name}"
                self.upload_file(file_path, gcs_path)
                uploaded_files.append(gcs_path)

        logger.info(f"Uploaded {len(uploaded_files)} files to gs://{self.bucket_name}/{gcs_prefix}")
        return uploaded_files
