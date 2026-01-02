#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
usage: test-mate-terminal-profiles-live.sh <profile-id> [profile-id ...]

Integration test (local desktop required):
  - Temporarily appends the given profile IDs to:
      gsettings org.mate.terminal.global profile-list
  - Launches mate-terminal with each profile id:
      mate-terminal --disable-factory --profile=<id> --command true
  - Fails if mate-terminal reports "No such profile"
  - Restores the original profile-list on exit

EOF
}

if [[ $# -lt 1 ]]; then
  usage >&2
  exit 2
fi

if ! command -v gsettings >/dev/null 2>&1; then
  echo "error: gsettings not found" >&2
  exit 1
fi
if ! command -v mate-terminal >/dev/null 2>&1; then
  echo "error: mate-terminal not found" >&2
  exit 1
fi
if ! command -v dconf >/dev/null 2>&1; then
  echo "error: dconf not found" >&2
  exit 1
fi

orig="$(gsettings get org.mate.terminal.global profile-list)"
restore() {
  gsettings set org.mate.terminal.global profile-list "${orig}" >/dev/null 2>&1 || true
}
trap restore EXIT HUP INT QUIT PIPE TERM

merged="${orig%]}"
if [[ "${merged}" == "[" ]]; then
  merged="["
fi

for id in "$@"; do
  if [[ "${orig}" != *"'${id}'"* ]]; then
    if [[ "${merged}" == "[" ]]; then
      merged="['${id}'"
    else
      merged="${merged}, '${id}'"
    fi
  fi
done
merged="${merged}]"

gsettings set org.mate.terminal.global profile-list "${merged}"

fail=0
for id in "$@"; do
  # mate-terminal's --profile expects the profile's *visible-name*.
  # Our imported profiles often use IDs like "gogh-atom" with visible-name "Gogh: Atom".
  visible="$(dconf read "/org/mate/terminal/profiles/${id}/visible-name" 2>/dev/null || true)"
  if [[ -n "${visible}" ]]; then
    # visible is a GVariant string like "'Gogh: Atom'"; strip surrounding single quotes.
    visible="${visible#\'}"
    visible="${visible%\'}"
  else
    visible="${id}"
  fi

  out="$(timeout 4 mate-terminal --disable-factory --profile="${visible}" --command true 2>&1 || true)"
  if echo "${out}" | rg -q "No such profile"; then
    echo "FAIL: ${id} (visible-name: ${visible}): ${out}" >&2
    fail=1
  fi
done

exit "${fail}"
