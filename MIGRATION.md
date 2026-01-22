# Migration Guide: GitHub Actions to GCP Cloud Run

This document describes the migration from GitHub Actions workflows to GCP Cloud Run Jobs.

## Before Migration

### Checklist

- [ ] GCP project created with billing enabled
- [ ] Required GCP APIs enabled
- [ ] `gcloud` CLI installed and configured
- [ ] Terraform installed (>= 1.5)
- [ ] MaxMind licence key obtained
- [ ] Backup of current GitHub Actions workflows

### Understand Current Setup

The GitHub Actions workflows:

1. **scheduled.yml** - Kept repo active (commits date every 5 days)
2. **ecb.yml** - Downloads ECB data, syncs to Google Drive via rclone
3. **geonames.yml** - Downloads geonames data, syncs to Google Drive
4. **maxmind.yml** - Downloads MaxMind data, syncs to Google Drive
5. **ofcom.yml** - Downloads Ofcom data, syncs to Google Drive

All workflows used:
- Ubuntu runner
- GitHub Secrets for credentials
- rclone for Google Drive sync

## Migration Steps

### Step 1: Enable GCP APIs

```bash
export PROJECT_ID="your-project-id"
gcloud config set project ${PROJECT_ID}

gcloud services enable \
  run.googleapis.com \
  cloudscheduler.googleapis.com \
  storage.googleapis.com \
  secretmanager.googleapis.com \
  artifactregistry.googleapis.com
```

### Step 2: Deploy Infrastructure

```bash
cd terraform

# Create terraform.tfvars
cat > terraform.tfvars <<EOF
project_id = "${PROJECT_ID}"
region     = "us-central1"
EOF

# Initialize and apply
terraform init
terraform apply
```

This creates:
- GCS bucket for data storage
- Artifact Registry repository
- Service account with necessary permissions
- Secret Manager secret for MaxMind key
- 4 Cloud Run Jobs (one per service)
- 4 Cloud Scheduler jobs (one per schedule)

### Step 3: Set Secrets

```bash
# Add MaxMind license key
echo -n "YOUR_MAXMIND_LICENSE_KEY" | gcloud secrets versions add maxmind-license-key --data-file=-

# Verify secret
gcloud secrets versions access latest --secret=maxmind-license-key
```

### Step 4: Build and Deploy Container

```bash
# Get Artifact Registry URL from Terraform
export IMAGE_URL=$(terraform output -raw artifact_registry_repository)/cron-services:latest

# Configure authentication
gcloud auth configure-docker $(echo ${IMAGE_URL} | cut -d'/' -f1)

# Build container (from repository root)
cd ..
podman build -t ${IMAGE_URL} .

# Push to Artifact Registry
podman push ${IMAGE_URL}
```

### Step 5: Test Jobs Manually

```bash
# Test each job
gcloud run jobs execute cron-ecb --region us-central1 --wait
gcloud run jobs execute cron-geonames --region us-central1 --wait
gcloud run jobs execute cron-maxmind --region us-central1 --wait
gcloud run jobs execute cron-ofcom --region us-central1 --wait

# Check logs
gcloud logging read "resource.type=cloud_run_job" --limit 100
```

### Step 6: Verify Data in GCS

```bash
# Get bucket name
export BUCKET_NAME=$(cd terraform && terraform output -raw bucket_name)

# List uploaded files
gsutil ls -r gs://${BUCKET_NAME}/

# Verify each service's data
gsutil ls gs://${BUCKET_NAME}/ecb/
gsutil ls gs://${BUCKET_NAME}/geonames/
gsutil ls gs://${BUCKET_NAME}/maxmind/
gsutil ls gs://${BUCKET_NAME}/codelist/
```

### Step 7: Monitor Scheduled Runs

```bash
# List schedulers
gcloud scheduler jobs list --location us-central1

# View next run times
gcloud scheduler jobs describe cron-ecb --location us-central1

# Manually trigger a scheduler (optional)
gcloud scheduler jobs run cron-ecb --location us-central1
```

### Step 8: Migrate Google Drive Data (Optional)

If you want to migrate existing data from Google Drive to GCS:

```bash
# Install rclone locally
# Configure Google Drive and GCS remotes

# Sync data
rclone sync gdrive:ecb/ gs://${BUCKET_NAME}/ecb/
rclone sync gdrive:geonames/ gs://${BUCKET_NAME}/geonames/
rclone sync gdrive:maxmind/ gs://${BUCKET_NAME}/maxmind/
rclone sync gdrive:codelist/ gs://${BUCKET_NAME}/codelist/
```

### Step 9: Disable GitHub Actions

Once confident in GCP setup:

```bash
# Disable workflows in GitHub
gh workflow disable ecb.yml
gh workflow disable geonames.yml
gh workflow disable maxmind.yml
gh workflow disable ofcom.yml
gh workflow disable scheduled.yml
```

Or delete workflow files:

```bash
git rm .github/workflows/*.yml
git commit -m "Migrate to GCP Cloud Run Jobs"
git push
```

## Post-Migration

### Monitoring Setup

Create log-based metrics:

```bash
# Job success rate metric
gcloud logging metrics create job_success_rate \
  --description="Cloud Run Job success rate" \
  --log-filter='resource.type="cloud_run_job"
    jsonPayload.message="Completed job"'

# Job failure metric
gcloud logging metrics create job_failures \
  --description="Cloud Run Job failures" \
  --log-filter='resource.type="cloud_run_job"
    severity>=ERROR'
```

### Alerting Setup

Create alert policies for job failures:

```bash
# Example: Alert on job failures
# (Best done via GCP Console or Terraform)
```

### Cost Optimization

1. Adjust job resources based on actual usage:
   ```bash
   # Edit terraform/main.tf and adjust cpu/memory limits
   ```

2. Review GCS lifecycle policies:
   ```bash
   # Current: Deletes objects after 90 days
   # Adjust in terraform/main.tf if needed
   ```

3. Monitor costs:
   ```bash
   # View Cloud Run costs
   gcloud billing projects describe ${PROJECT_ID}
   ```

## Rollback Plan

If issues arise, you can quickly rollback:

1. Re-enable GitHub Actions workflows:
   ```bash
   gh workflow enable ecb.yml
   ```

2. Keep GCP resources for testing/debugging

3. Data in GCS remains accessible

## Comparison Table

| Aspect | GitHub Actions | GCP Cloud Run |
|--------|---------------|---------------|
| **Cost** | Free (public repos) | ~$10-40/month |
| **Execution** | GitHub runners | Serverless containers |
| **Storage** | Google Drive (via rclone) | GCS (native) |
| **Secrets** | GitHub Secrets | Secret Manager |
| **Monitoring** | GitHub UI | Cloud Logging/Monitoring |
| **Scheduling** | Cron syntax in YAML | Cloud Scheduler |
| **Retries** | Manual config | Built-in |
| **Timeout** | 6 hours max | Configurable (1 hour default) |
| **Concurrency** | Per repo limits | Project quotas |
| **Local Testing** | act tool | Podman/Docker |

## Benefits of Migration

1. **No workflow deactivation**: No need for dummy commits to keep workflows active
2. **Better monitoring**: Native GCP logging and monitoring
3. **Native GCS integration**: No rclone configuration needed
4. **Scalability**: Better resource allocation and scaling
5. **Security**: Service accounts with granular IAM permissions
6. **Cost transparency**: Clear billing and cost attribution
7. **Local testing**: Easy to test with containers
8. **Python ecosystem**: Modern Python 3.13 with uv

## Troubleshooting

### Issue: Job fails with permission denied

**Solution**: Check service account IAM permissions
```bash
gcloud projects get-iam-policy ${PROJECT_ID} \
  --flatten="bindings[].members" \
  --filter="bindings.members:serviceAccount:cron-services@*"
```

### Issue: Secret not found

**Solution**: Verify secret exists and service account has access
```bash
gcloud secrets describe maxmind-license-key
gcloud secrets get-iam-policy maxmind-license-key
```

### Issue: Container fails to build

**Solution**: Ensure Python 3.13 and uv are available
```bash
podman build --no-cache -t test .
```

### Issue: Downloads timeout

**Solution**: Increase job timeout in terraform/main.tf
```hcl
timeout = "3600s"  # Increase if needed
```

## Support

For issues:
1. Check job logs: `gcloud logging read`
2. Review Terraform state: `terraform show`
3. Test locally: `make run-ecb`
4. Open an issue in the repository

## Next Steps

After successful migration:

1. Archive old workflow files for reference
2. Update documentation
3. Set up monitoring alerts
4. Review and optimize costs monthly
5. Consider adding more jobs as needed
