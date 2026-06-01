#!/usr/bin/env bash
# Geonames dumps -> gdrive:geonames/
# Migrated from .github/workflows/geonames.yml
source "$(dirname "${BASH_SOURCE[0]}")/lib.sh"

require wget
dir="$(fresh_dir geonames)"
cd "$dir"

log "downloading Geonames dumps"
xargs -n1 -P2 wget -nv --content-disposition < "$REPO_ROOT/geonames-urls.txt"

sync_remote "$dir" gdrive:geonames/
log "geonames-sync complete"
