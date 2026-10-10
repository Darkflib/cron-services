# cron-services

Retired. These workflows downloaded reference data (ECB rates, MaxMind GeoLite2, GeoNames,
Ofcom number allocations) on a schedule and synced it to Google Drive, without checking what
they had downloaded.

[Darkflib/refdata](https://github.com/Darkflib/refdata) replaces them: it fetches, validates,
converts and publishes the same four sources, keeps the last good release when an upstream
misbehaves, and alerts when data goes stale. It is deployed from wwff-tech/gitops.

The history is kept for reference. The Google Drive folders are no longer updated.
