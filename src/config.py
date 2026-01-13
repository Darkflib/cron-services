"""Configuration management for cron services."""

import os


class Settings:
    """Application settings loaded from environment variables."""

    def __init__(self):
        # GCP Configuration
        self.gcp_project_id = os.getenv("CRON_GCP_PROJECT_ID", "")
        self.gcs_bucket = os.getenv("CRON_GCS_BUCKET", "")

        # MaxMind Configuration
        self.maxmind_license_key = os.getenv("CRON_MAXMIND_LICENSE_KEY", "")

        # Job Configuration
        self.temp_dir = os.getenv("CRON_TEMP_DIR", "/tmp")


settings = Settings()
