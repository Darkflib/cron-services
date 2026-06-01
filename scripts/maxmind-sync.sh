#!/usr/bin/env bash
# MaxMind GeoLite2 databases -> gdrive:maxmind/
# Migrated from .github/workflows/maxmind.yml
#
# Requires MAXMIND_KEY in the environment (supplied via wfctl EnvironmentFile,
# see deploy/maxmind.env.example). The license key is substituted into the URL
# list at run time and never stored in the repo.
source "$(dirname "${BASH_SOURCE[0]}")/lib.sh"

require wget
require sed
: "${MAXMIND_KEY:?MAXMIND_KEY must be set (see deploy/maxmind.env.example)}"

dir="$(fresh_dir maxmind)"
cd "$dir"

log "downloading MaxMind GeoLite2 databases"
sed "s/YOUR_LICENSE_KEY/${MAXMIND_KEY}/g" "$REPO_ROOT/maxmind-urls.txt" \
  | xargs -n1 -P2 wget -nv --content-disposition

sync_remote "$dir" gdrive:maxmind/
log "maxmind-sync complete"
