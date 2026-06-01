# Migrating cron-services to wfctl

This repo's scheduled jobs are being moved from **GitHub Actions** onto a
persistent host managed by [`wfctl`](https://github.com/darkflib/wfctl), which
renders declarative YAML into systemd `--user` service + timer units.

## What changed

Each old GitHub Actions workflow becomes a shell script (in `scripts/`) plus a
wfctl workflow definition (in `wfctl/`). The download + `rclone sync` logic is
unchanged; only the execution substrate moves.

| Old workflow | Script | wfctl id | Schedule (was cron) | rclone target |
|---|---|---|---|---|
| `ecb.yml` | `scripts/ecb-sync.sh` | `ecb-sync` | `*-*-* 18:00:00` (`0 18 * * *`) | `gdrive:ecb/` |
| `maxmind.yml` | `scripts/maxmind-sync.sh` | `maxmind-sync` | `*-*-* 05:20:00` (`20 5 * * *`) | `gdrive:maxmind/` |
| `geonames.yml` | `scripts/geonames-sync.sh` | `geonames-sync` | `*-*-05 05:20:00` (`20 5 5 * *`) | `gdrive:geonames/` |
| `ofcom.yml` | `scripts/ofcom-sync.sh` | `ofcom-sync` | `*-*-05 05:20:00` (`20 5 5 * *`) | `gdrive:codelist/` |
| `scheduled.yml` | — | — | dropped (GitHub-only heartbeat) | — |

> All wfctl definitions assume the home directory is `/home/mike`. If you deploy
> as a different user, adjust the absolute paths in `wfctl/*.yaml` and the
> `PATH` variable accordingly.

## Notable differences from the GitHub Actions version

- **Clean staging dir per run.** `scripts/lib.sh` wipes the download dir before
  each run so `rclone sync`'s delete-extraneous behaviour matches the old
  ephemeral runners.
- **Secrets live on the host, not in GitHub.**
  - `RCLONE_CONF` → write once to `~/.config/rclone/rclone.conf`.
  - `MAXMIND_KEY` → `~/.config/cron-services/maxmind.env` (see
    `deploy/maxmind.env.example`), wired in via wfctl `environment.files`.
- **rclone OAuth token refresh.** The Google Drive backend rewrites refreshed
  tokens back into `rclone.conf`, so the workflows use the `basic` security
  profile (keeps `$HOME` writable) rather than `readonly-home`/`strict`.
- **Ofcom uses `curl -fSL`** (fail on HTTP error + follow redirects) so a bad
  response makes the unit exit non-zero instead of syncing an error page.

## Host prerequisites (one-time)

1. Linux with systemd; `loginctl enable-linger "$USER"` so timers run without
   an active login session.
2. Install `rclone`, `wget`, `curl`, `file`.
3. Install `wfctl` (`uv tool install wfctl`).
4. Place `~/.config/rclone/rclone.conf` (with a `gdrive` remote) and
   `~/.config/cron-services/maxmind.env`.
5. `wfctl doctor` to sanity-check the environment.

## Deploy

```bash
./deploy/install.sh      # copies definitions, validates, shows the plan
# review the plan, then:
wfctl apply              # write units + enable timers
wfctl run ecb-sync --wait
wfctl logs ecb-sync
```

## Cutover

The GitHub Actions workflows are intentionally **left running** during
migration. Run both in parallel for a cycle and compare the Google Drive
output, then retire the Actions workflows (delete `.github/workflows/*.yml`,
remove the `RCLONE_CONF` / `MAXMIND_KEY` GitHub secrets).
