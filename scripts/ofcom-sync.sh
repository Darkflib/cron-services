#!/usr/bin/env bash
# Ofcom UK telephone numbering codelist -> gdrive:codelist/
# Migrated from .github/workflows/ofcom.yml
#
# The original workflow noted that wget hit 403s here, so it used curl. We keep
# curl and add -f (fail on HTTP errors so the unit exits non-zero) and -L
# (follow redirects) for unattended robustness.
source "$(dirname "${BASH_SOURCE[0]}")/lib.sh"

require curl
require file
dir="$(fresh_dir codelist)"
cd "$dir"

log "downloading Ofcom telephone numbering codelist"
curl -fSL \
  "https://www.ofcom.org.uk/siteassets/resources/documents/phones-telecoms-and-internet/information-for-industry/numbering/regular-updates/telephone-numbers/codelist.zip" \
  -o codelist.zip
file codelist.zip

sync_remote "$dir" gdrive:codelist/
log "ofcom-sync complete"
