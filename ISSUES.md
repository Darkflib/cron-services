# Code Review Issues

This document tracks issues raised during code review that have not yet been addressed, organized by directory path and file.

## Summary of Addressed Issues

### High Priority (Completed)
- **MIGRATION.md**: Replace echo with secure method for MaxMind license key - Uses temp file with umask 077
- **cli.py**: Add exception handling around job execution - Wrapped job.run() in try/except, validates result is dict
- **downloader.py**: Use streaming for large files - Implemented async streaming with response.aiter_bytes() to avoid loading entire files into memory
- **terraform/main.tf**: Update Cloud Run v2 Jobs API endpoint - Changed URI from v1 to v2 format, added OAuth scope

### Medium Priority (Completed)
- **MIGRATION.md**: Make registry hostname extraction more robust - Replaced fragile cut command with sed for URL parsing
- **README.md**: Add Artifact Registry repository creation step - Added gcloud artifacts repositories create step before push
- **README.md**: Use ${REGION} variable consistently - Replaced hardcoded us-central1 with ${REGION} in gcloud run commands
- **downloader.py**: Make filename extraction safer - Added urllib.parse for safe URL extraction, collision handling with counter suffix, hashlib.md5 fallback
- **src/jobs/base.py**: Add error handling to _cleanup_work_dir - Wrapped shutil.rmtree in try/except to catch OSError
- **src/jobs/geonames.py**: Add error handling for file operations - Added FileNotFoundError check for missing geonames-urls.txt

### Skipped
- **src/jobs/base.py**: Pass work_dir to execute() methods - Skipped because jobs already use `self.temp_dir / self.name` which provides the work directory path, making the explicit parameter unnecessary

## Remaining Issues

### Low Priority

### MIGRATION.md
- Add rclone configuration steps before sync commands
  - The guide mentions installing and configuring rclone but doesn't provide actual configuration steps
  - Users may not know how to set up gdrive: remote for Google Drive or how to authenticate with GCS
  - Consider adding steps for configuring Google Drive remote and GCS remote

## Issue Tracking Template

For new issues, use the following format:

```markdown
### [Directory/File]

**Issue Title**
- Description of the issue
- Priority: [High|Medium|Low]
- Status: [Open|In Progress|Done]

**Suggested Fix** (if applicable)
- Steps or code changes to resolve the issue
```
