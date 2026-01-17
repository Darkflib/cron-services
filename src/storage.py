"""Google Cloud Storage operations."""

import logging
from pathlib import Path

from google.cloud import storage
from tenacity import retry, stop_after_attempt, wait_exponential

from .config import settings

logger = logging.getLogger(__name__)


class GCSUploader:
    """Handle uploads to Google Cloud Storage."""

    def __init__(self, bucket_name: str | None = None):
        """Initialize GCS client."""
        self.client = storage.Client(project=settings.gcp_project_id)
        self.bucket_name = bucket_name or settings.gcs_bucket
        self.bucket = self.client.bucket(self.bucket_name)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True,
    )
    def upload_file(self, local_path: Path, gcs_path: str) -> None:
        """Upload a file to GCS with retry logic.

        Args:
            local_path: Local file path to upload
            gcs_path: Destination path in GCS bucket
        """
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
        """
        uploaded_files = []

        for file_path in local_dir.iterdir():
            if file_path.is_file():
                gcs_path = f"{gcs_prefix}/{file_path.name}"
                self.upload_file(file_path, gcs_path)
                uploaded_files.append(gcs_path)

        logger.info(f"Uploaded {len(uploaded_files)} files to gs://{self.bucket_name}/{gcs_prefix}")
        return uploaded_files
