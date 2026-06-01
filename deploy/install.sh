#!/usr/bin/env bash
# Deploy the cron-services wfctl workflows onto this host.
#
# Copies the workflow definitions into the wfctl config dir, prepares the
# cache/secret directories, then runs `wfctl validate` and `wfctl plan` so you
# can review the changes BEFORE applying. It deliberately does NOT run
# `wfctl apply` — do that yourself once the plan looks right.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WF_DIR="${WFCTL_CONFIG_DIR:-$HOME/.config/wfctl/workflows}"

echo "Repo root:       $REPO_ROOT"
echo "wfctl workflows: $WF_DIR"
echo

# 1. Prerequisites
command -v wfctl  >/dev/null || { echo "ERROR: wfctl not found (install: uv tool install wfctl)"; exit 1; }
command -v rclone >/dev/null || echo "WARNING: rclone not found on PATH"

# 2. Scripts must be executable (we invoke via bash, but keep the bit tidy)
chmod +x "$REPO_ROOT"/scripts/*.sh

# 3. Cache + secret directories
mkdir -p "$HOME/.cache/cron-services"
mkdir -p "$HOME/.config/cron-services"
if [ ! -f "$HOME/.config/cron-services/maxmind.env" ]; then
  echo "NOTE: create $HOME/.config/cron-services/maxmind.env from deploy/maxmind.env.example (chmod 600)"
fi
if [ ! -f "$HOME/.config/rclone/rclone.conf" ]; then
  echo "NOTE: $HOME/.config/rclone/rclone.conf not found — rclone needs a 'gdrive' remote"
fi

# 4. Install workflow definitions
mkdir -p "$WF_DIR"
cp "$REPO_ROOT"/wfctl/*.yaml "$WF_DIR/"
echo "Copied $(ls "$REPO_ROOT"/wfctl/*.yaml | wc -l) workflow definition(s) to $WF_DIR"
echo

# 5. Validate + plan (no changes applied)
wfctl validate
wfctl plan

cat <<'EOF'

Review the plan above, then to go live:
  loginctl enable-linger "$USER"   # timers fire without an active login
  wfctl apply                      # write units + enable timers
  wfctl run ecb-sync --wait        # smoke-test one job end to end
  wfctl logs ecb-sync              # inspect output
EOF
