#!/usr/bin/env bash
# ECB euro foreign-exchange reference rates -> gdrive:ecb/
# Migrated from .github/workflows/ecb.yml
source "$(dirname "${BASH_SOURCE[0]}")/lib.sh"

require wget
dir="$(fresh_dir ecb)"
cd "$dir"

log "downloading ECB reference rates"
wget -nv --content-disposition https://www.ecb.europa.eu/stats/eurofxref/eurofxref-daily.xml
wget -nv --content-disposition https://www.ecb.europa.eu/stats/eurofxref/eurofxref.zip
wget -nv --content-disposition https://www.ecb.europa.eu/stats/eurofxref/eurofxref-hist-90d.xml

sync_remote "$dir" gdrive:ecb/
log "ecb-sync complete"
