#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 1 || $# -gt 2 ]]; then
  echo "usage: $0 <profile-id> [--colors-only]" >&2
  exit 2
fi

profile_id="$1"
mode="${2:-}"
profile_path="/org/mate/terminal/profiles/${profile_id}/"

if ! command -v dconf >/dev/null 2>&1; then
  echo "error: dconf not found" >&2
  exit 1
fi

dump="$(dconf dump "${profile_path}")"

if [[ "${mode}" == "--colors-only" ]]; then
  printf '%s\n' "${dump}" | rg -n "^(background-color|foreground-color|palette|bold-color|bold-color-same-as-fg|use-theme-colors|cursor-color)="
  exit 0
fi

printf '%s\n' "${dump}"

