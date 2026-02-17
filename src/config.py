"""Configuration management for cron services."""

import os


class Settings:
    """Application settings loaded from environment variables."""

    gcp_project_id: str
    gcs_bucket: str
    maxmind_license_key: str
    temp_dir: str

    def __init__(self):
        # GCP Configuration
        self.gcp_project_id = os.getenv("CRON_GCP_PROJECT_ID", "")
        self.gcs_bucket = os.getenv("CRON_GCS_BUCKET", "")

        # MaxMind Configuration
        self.maxmind_license_key = os.getenv("CRON_MAXMIND_LICENSE_KEY", "")

        # Job Configuration
        self.temp_dir = os.getenv("CRON_TEMP_DIR", "/tmp")

        self._validate()

    def _validate(self):
        """Validate that required configuration is present."""
        missing = []
        if not self.gcp_project_id:
            missing.append("CRON_GCP_PROJECT_ID")
        if not self.gcs_bucket:
            missing.append("CRON_GCS_BUCKET")
        if not self.maxmind_license_key:
            missing.append("CRON_MAXMIND_LICENSE_KEY")
        if missing:
            missing_vars_msg = "Missing required environment variables: " + ", ".join(missing)
            raise ValueError(missing_vars_msg)


settings = Settings()
