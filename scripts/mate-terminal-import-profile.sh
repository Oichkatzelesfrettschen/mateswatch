#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 2 ]]; then
  echo "usage: $0 <profile-id> <profile-dconf-file>" >&2
  exit 2
fi

profile_id="$1"
profile_file="$2"
profile_path="/org/mate/terminal/profiles/${profile_id}/"

if ! command -v dconf >/dev/null 2>&1; then
  echo "error: dconf not found" >&2
  exit 1
fi

dconf load "${profile_path}" < "${profile_file}"

echo "Imported profile '${profile_id}' from ${profile_file}"

