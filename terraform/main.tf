terraform {
  required_version = ">= 1.5"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 6.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# GCS bucket for data storage
resource "google_storage_bucket" "data" {
  name          = "${var.project_id}-cron-services-data"
  location      = var.region
  force_destroy = false

  uniform_bucket_level_access = true

  versioning {
    enabled = true
  }

  lifecycle_rule {
    condition {
      age = 90
    }
    action {
      type = "Delete"
    }
  }
}

# Artifact Registry repository for container images
resource "google_artifact_registry_repository" "repo" {
  location      = var.region
  repository_id = "cron-services"
  description   = "Container images for cron services"
  format        = "DOCKER"
}

# Service account for Cloud Run Jobs
resource "google_service_account" "job_sa" {
  account_id   = "cron-services"
  display_name = "Cron Services Service Account"
  description  = "Service account for running cron service jobs"
}

# Grant GCS access to service account
resource "google_storage_bucket_iam_member" "job_sa_storage" {
  bucket = google_storage_bucket.data.name
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${google_service_account.job_sa.email}"
}

# Secret for MaxMind license key
resource "google_secret_manager_secret" "maxmind_license" {
  secret_id = "maxmind-license-key"

  replication {
    auto {}
  }
}

# Grant secret access to service account
resource "google_secret_manager_secret_iam_member" "job_sa_secret" {
  secret_id = google_secret_manager_secret.maxmind_license.id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.job_sa.email}"
}

# Cloud Run Jobs
locals {
  jobs = {
    ecb = {
      schedule = "0 18 * * *" # Daily at 18:00 UTC
      env_vars = {}
    }
    geonames = {
      schedule = "20 5 5 * *" # Monthly on 5th at 05:20 UTC
      env_vars = {}
    }
    maxmind = {
      schedule = "20 5 * * *" # Daily at 05:20 UTC
      env_vars = {
        CRON_MAXMIND_LICENSE_KEY = google_secret_manager_secret.maxmind_license.id
      }
    }
    ofcom = {
      schedule = "20 5 5 * *" # Monthly on 5th at 05:20 UTC
      env_vars = {}
    }
  }
}

resource "google_cloud_run_v2_job" "jobs" {
  for_each = local.jobs

  name     = "cron-${each.key}"
  location = var.region

  template {
    template {
      service_account = google_service_account.job_sa.email

      containers {
        image = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.repo.repository_id}/cron-services:latest"
        args  = [each.key]

        resources {
          limits = {
            cpu    = "1"
            memory = "512Mi"
          }
        }

        env {
          name  = "CRON_GCP_PROJECT_ID"
          value = var.project_id
        }

        env {
          name  = "CRON_GCS_BUCKET"
          value = google_storage_bucket.data.name
        }

        # Add secret environment variable for MaxMind
        dynamic "env" {
          for_each = each.value.env_vars
          content {
            name = env.key
            value_source {
              secret_key_ref {
                secret  = env.value
                version = "latest"
              }
            }
          }
        }
      }

      max_retries = 3
      timeout     = "3600s" # 1 hour
    }
  }

  lifecycle {
    ignore_changes = [
      client,
      client_version,
    ]
  }
}

# Cloud Scheduler jobs to trigger Cloud Run Jobs
resource "google_cloud_scheduler_job" "schedulers" {
  for_each = local.jobs

  name             = "cron-${each.key}"
  description      = "Trigger ${each.key} sync job"
  schedule         = each.value.schedule
  time_zone        = "UTC"
  attempt_deadline = "3600s"
  region           = var.region

  retry_config {
    retry_count = 3
  }

  http_target {
    http_method = "POST"
    uri         = "https://${var.region}-run.googleapis.com/apis/run.googleapis.com/v1/namespaces/${var.project_id}/jobs/${google_cloud_run_v2_job.jobs[each.key].name}:run"

    oauth_token {
      service_account_email = google_service_account.job_sa.email
    }
  }

  depends_on = [google_cloud_run_v2_job.jobs]
}
