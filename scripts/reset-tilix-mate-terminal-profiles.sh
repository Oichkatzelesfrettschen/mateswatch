#!/usr/bin/env bash
set -euo pipefail

prefixes=("tilix-" "tilix-user-" "gogh-")

usage() {
  cat <<'EOF'
usage: reset-tilix-mate-terminal-profiles.sh [--dry-run]

Removes bulk-generated profiles created by:

- `scripts/sync-tilix-to-mate-terminal.py` (tilix-* and tilix-user-*)
- `scripts/import-gogh-to-mate-terminal.py` + your own imports (gogh-*)

by running:

  dconf reset -f /org/mate/terminal/profiles/<profile-id>/

It matches profile IDs that start with:
  - tilix-
  - tilix-user-
  - gogh-
EOF
}

dry_run="false"
if [[ "${1:-}" == "--dry-run" ]]; then
  dry_run="true"
elif [[ "${1:-}" != "" ]]; then
  usage >&2
  exit 2
fi

if ! command -v dconf >/dev/null 2>&1; then
  echo "error: dconf not found" >&2
  exit 1
fi

while IFS= read -r profile_id; do
  [[ -z "${profile_id}" ]] && continue
  if [[ "${dry_run}" == "true" ]]; then
    echo "dconf reset -f /org/mate/terminal/profiles/${profile_id}/"
  else
    dconf reset -f "/org/mate/terminal/profiles/${profile_id}/"
  fi
done < <(
  dconf list /org/mate/terminal/profiles/ \
    | sed 's#/$##' \
    | while IFS= read -r name; do
        for p in "${prefixes[@]}"; do
          if [[ "${name}" == ${p}* ]]; then
            echo "${name}"
            break
          fi
        done
      done \
    | sort
)
