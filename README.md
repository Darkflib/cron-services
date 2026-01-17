# Cron Services

Scheduled data sync services migrated from GitHub Actions to GCP Cloud Run Jobs with Cloud Scheduler.

## Overview

This repository contains Python-based jobs that download and sync data from various sources to Google Cloud Storage:

- **ECB**: European Central Bank forex reference rates (daily at 18:00 UTC)
- **Geonames**: Geographical database (monthly on 5th at 05:20 UTC)
- **MaxMind**: GeoLite2 IP geolocation databases (daily at 05:20 UTC)
- **Ofcom**: UK telephone numbering data (monthly on 5th at 05:20 UTC)

## Architecture

- **Python 3.13** with **uv** for dependency management
- **Docker/Podman** containers for reproducible builds
- **GCP Cloud Run Jobs** for serverless execution
- **GCP Cloud Scheduler** for triggering jobs on schedule
- **GCS** for data storage (replaces Google Drive)
- **Secret Manager** for API keys

## Local Development

### Prerequisites

- Python 3.13
- [uv](https://github.com/astral-sh/uv) package manager
- Podman or Docker (for container testing)
- GCP credentials configured

### Setup

```bash
# Install dependencies
make install

# Or with dev dependencies
make dev
```

### Running Jobs Locally

```bash
# Set environment variables
export CRON_GCP_PROJECT_ID="your-project-id"
export CRON_GCS_BUCKET="your-bucket-name"
export CRON_MAXMIND_LICENSE_KEY="your-license-key"

# Run a specific job
make run-ecb
make run-geonames
make run-maxmind
make run-ofcom

# Or directly with uv
uv run python -m src.cli ecb
```

### Testing with Podman

```bash
# Build container
make build-podman

# Run a job in container
podman run --rm \
  -e CRON_GCP_PROJECT_ID="your-project-id" \
  -e CRON_GCS_BUCKET="your-bucket-name" \
  -e CRON_MAXMIND_LICENSE_KEY="your-license-key" \
  cron-services:latest ecb
```

## GCP Deployment

### Prerequisites

- GCP project with billing enabled
- Terraform >= 1.5
- `gcloud` CLI configured
- Required GCP APIs enabled:
  - Cloud Run API
  - Cloud Scheduler API
  - Cloud Storage API
  - Secret Manager API
  - Artifact Registry API

### Enable Required APIs

```bash
gcloud services enable \
  run.googleapis.com \
  cloudscheduler.googleapis.com \
  storage.googleapis.com \
  secretmanager.googleapis.com \
  artifactregistry.googleapis.com
```

### Build and Push Container

```bash
# Set variables
export PROJECT_ID="your-project-id"
export REGION="us-central1"
export IMAGE_URL="${REGION}-docker.pkg.dev/${PROJECT_ID}/cron-services/cron-services:latest"

# Configure Docker/Podman for Artifact Registry
gcloud auth configure-docker ${REGION}-docker.pkg.dev

# Build and push
podman build -t ${IMAGE_URL} .
podman push ${IMAGE_URL}
```

### Deploy with Terraform

```bash
cd terraform

# Copy and edit variables
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars with your project_id and region

# Initialize Terraform
terraform init

# Plan deployment
terraform plan

# Apply infrastructure
terraform apply
```

### Set MaxMind License Key

```bash
# Add your MaxMind license key to Secret Manager
echo -n "your-license-key" | gcloud secrets versions add maxmind-license-key --data-file=-
```

### Manual Job Execution

```bash
# Trigger a job manually
gcloud run jobs execute cron-ecb --region us-central1

# View job logs
gcloud logging read "resource.type=cloud_run_job AND resource.labels.job_name=cron-ecb" --limit 50
```

## Configuration

Environment variables (all prefixed with `CRON_`):

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `CRON_GCP_PROJECT_ID` | GCP project ID | Yes | - |
| `CRON_GCS_BUCKET` | GCS bucket for data storage | Yes | - |
| `CRON_MAXMIND_LICENSE_KEY` | MaxMind license key | For maxmind job | - |
| `CRON_TEMP_DIR` | Temporary directory for downloads | No | `/tmp` |

## Job Details

### ECB (European Central Bank)

Downloads daily forex reference rates:
- `eurofxref-daily.xml` - Latest rates
- `eurofxref.zip` - Historical archive
- `eurofxref-hist-90d.xml` - Last 90 days

**Schedule**: Daily at 18:00 UTC

### Geonames

Downloads geographical database files (21 files):
- Country info, city data, feature codes, timezones, etc.
- URLs defined in `geonames-urls.txt`

**Schedule**: Monthly on 5th at 05:20 UTC

### MaxMind

Downloads GeoLite2 IP geolocation databases:
- ASN, City, and Country editions
- Both binary (.tar.gz) and CSV formats
- Checksums (.sha256) for verification

**Schedule**: Daily at 05:20 UTC
**Requires**: MaxMind license key

### Ofcom

Downloads UK telephone numbering codelist:
- Official Ofcom telephone number allocations

**Schedule**: Monthly on 5th at 05:20 UTC

## Migration from GitHub Actions

The original GitHub Actions workflows have been replaced with this GCP-based solution:

| Old Workflow | New Job | Notes |
|--------------|---------|-------|
| `scheduled.yml` | *(removed)* | No longer needed (kept repo active) |
| `ecb.yml` | `cron-ecb` | Migrated to Cloud Run Job |
| `geonames.yml` | `cron-geonames` | Migrated to Cloud Run Job |
| `maxmind.yml` | `cron-maxmind` | Migrated to Cloud Run Job |
| `ofcom.yml` | `cron-ofcom` | Migrated to Cloud Run Job |

**Key Changes**:
- GitHub Actions → GCP Cloud Run Jobs
- Google Drive (rclone) → Google Cloud Storage (native SDK)
- GitHub Secrets → GCP Secret Manager
- No more repo activity commits needed

## Development

### Code Structure

```
src/
├── __init__.py
├── cli.py              # CLI entry point
├── config.py           # Environment configuration
├── downloader.py       # Async file downloads
├── storage.py          # GCS upload operations
└── jobs/
    ├── __init__.py     # Job registry
    ├── base.py         # Base job class
    ├── ecb.py          # ECB job
    ├── geonames.py     # Geonames job
    ├── maxmind.py      # MaxMind job
    └── ofcom.py        # Ofcom job
```

### Linting and Formatting

```bash
# Run linting
make lint

# Auto-format code
make format
```

### Testing

```bash
make test
```

## Monitoring

View logs for a specific job:

```bash
# Recent logs
gcloud logging read "resource.type=cloud_run_job AND resource.labels.job_name=cron-ecb" \
  --limit 50 \
  --format json

# Follow logs in real-time
gcloud logging tail "resource.type=cloud_run_job" --format=json
```

View job execution history:

```bash
gcloud run jobs executions list --job cron-ecb --region us-central1
```

## Troubleshooting

### Job Fails to Start

1. Check service account permissions
2. Verify environment variables are set
3. Check Secret Manager access for MaxMind key

### Downloads Fail

1. Check network connectivity
2. Verify source URLs are still valid
3. Check retry logic in logs

### GCS Upload Fails

1. Verify service account has `storage.objectAdmin` role
2. Check bucket exists and is in correct region
3. Review IAM permissions

## Cost Estimation

Approximate monthly costs (us-central1):

- Cloud Run Jobs: ~$5-10 (based on execution time)
- Cloud Scheduler: ~$0.30 (4 jobs)
- Cloud Storage: Variable (depends on data size, typically $5-20/month)
- Secret Manager: ~$0.06 (1 secret)
- Artifact Registry: ~$0.10 (storage)

**Total**: ~$10-40/month depending on data storage

## License

MIT
