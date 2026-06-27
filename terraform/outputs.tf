output "bucket_name" {
  description = "GCS bucket for data storage"
  value       = google_storage_bucket.data.name
}

output "artifact_registry_repository" {
  description = "Artifact Registry repository URL"
  value       = "${google_artifact_registry_repository.repo.location}-docker.pkg.dev/${google_artifact_registry_repository.repo.project}/${google_artifact_registry_repository.repo.repository_id}"
}

output "service_account_email" {
  description = "Service account email for Cloud Run Jobs"
  value       = google_service_account.job_sa.email
}

output "jobs" {
  description = "Cloud Run Jobs"
  value = {
    for name, job in google_cloud_run_v2_job.jobs : name => {
      name     = job.name
      location = job.location
    }
  }
}

output "schedulers" {
  description = "Cloud Scheduler jobs"
  value = {
    for name, scheduler in google_cloud_scheduler_job.schedulers : name => {
      name     = scheduler.name
      schedule = scheduler.schedule
    }
  }
}
