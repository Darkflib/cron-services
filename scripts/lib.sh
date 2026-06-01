#!/usr/bin/env bash
# Shared helpers for the cron-services sync scripts.
#
# These scripts are invoked by wfctl-managed systemd user units (exec mode
# "command"). They reproduce the download + rclone-sync steps that previously
# lived in the GitHub Actions workflows under .github/workflows/.
#
# Sourcing this file turns on strict mode for the calling script.
set -euo pipefail

# Repo root (scripts/ lives directly under it).
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Where downloads are staged before sync. Override with CRON_SERVICES_CACHE.
CACHE_ROOT="${CRON_SERVICES_CACHE:-$HOME/.cache/cron-services}"

log() { printf '%s %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$*"; }
die() { log "ERROR: $*"; exit 1; }

require() { command -v "$1" >/dev/null 2>&1 || die "required command not found: $1"; }

# Create a clean staging dir for a job and echo its path.
#
# Wiping the dir on every run preserves the delete-extraneous semantics of
# `rclone sync`: the GitHub Actions runners gave us a fresh filesystem each
# time, so a file removed upstream disappeared from the local set and got
# pruned from the remote. A persistent host would otherwise accumulate stale
# files and keep re-uploading them.
fresh_dir() {
  local name="$1"
  local dir="$CACHE_ROOT/$name"
  rm -rf "$dir"
  mkdir -p "$dir"
  printf '%s' "$dir"
}

# rclone sync wrapper. Args: <local-dir> <remote:path>
sync_remote() {
  local src="$1" dst="$2"
  require rclone
  log "rclone sync $src -> $dst"
  rclone sync "$src" "$dst" -v
}
