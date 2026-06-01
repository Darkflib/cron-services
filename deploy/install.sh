#!/usr/bin/env bash
# Deploy the cron-services wfctl workflows onto this host.
#
# Renders the workflow templates in wfctl/templates/ into the wfctl config dir,
# substituting this checkout's location and $HOME so the absolute paths in the
# generated definitions are correct wherever the repo is cloned. Then runs
# `wfctl validate` and `wfctl plan` so you can review the changes BEFORE
# applying. It deliberately does NOT run `wfctl apply` — do that yourself once
# the plan looks right.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WF_DIR="${WFCTL_CONFIG_DIR:-$HOME/.config/wfctl/workflows}"
TPL_DIR="$REPO_ROOT/wfctl/templates"
SECRET_DIR="$HOME/.config/cron-services"

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
mkdir -p "$SECRET_DIR"

# Seed the MaxMind secret file from the example so `wfctl validate` (which
# checks EnvironmentFile existence) passes. It contains a placeholder key —
# edit it before the maxmind-sync job will actually work.
if [ ! -f "$SECRET_DIR/maxmind.env" ]; then
  install -m 600 "$REPO_ROOT/deploy/maxmind.env.example" "$SECRET_DIR/maxmind.env"
  echo "Created $SECRET_DIR/maxmind.env (PLACEHOLDER key — edit it with your real MAXMIND_KEY)"
fi
if [ ! -f "$HOME/.config/rclone/rclone.conf" ]; then
  echo "NOTE: $HOME/.config/rclone/rclone.conf not found — rclone needs a 'gdrive' remote"
fi

# 4. Render workflow definitions from templates.
#    @@REPO_ROOT@@ -> this checkout, @@HOME@@ -> $HOME. Using '#' as the sed
#    delimiter so the substituted paths (which contain '/') don't clash.
mkdir -p "$WF_DIR"
rendered=0
for tpl in "$TPL_DIR"/*.yaml; do
  name="$(basename "$tpl")"
  sed -e "s#@@REPO_ROOT@@#${REPO_ROOT}#g" \
      -e "s#@@HOME@@#${HOME}#g" \
      "$tpl" > "$WF_DIR/$name"
  rendered=$((rendered + 1))
done
echo "Rendered $rendered workflow definition(s) to $WF_DIR"
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
