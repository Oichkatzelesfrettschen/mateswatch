#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "${repo_root}"

deb="$(ls -1 dist/mateswatch_*_all.deb | tail -n 1)"
echo "Using deb: ${deb}"

dpkg -i "${deb}" || true
apt-get update
apt-get install -y -f

command -v mateswatch >/dev/null
test -d /usr/share/mateswatch/mate-terminal/schemes
test -L /usr/share/mate-terminal/profiles/mateswatch

echo "Theme count (installed schemes):"
find /usr/share/mateswatch/mate-terminal/schemes -name '*.dconf' | wc -l

theme_id="$(mateswatch list | head -n 1)"
if [[ -z "${theme_id}" ]]; then
  echo "No themes found via mateswatch list" >&2
  exit 2
fi
echo "Importing theme id: ${theme_id}"

dbus-run-session -- mateswatch import "${theme_id}" --add-to-profile-list --set-default

echo "Render-fidelity sample (installed schemes):"
dbus-run-session -- ./scripts/test-mateswatch-render.py \
  --schemes-dir /usr/share/mateswatch/mate-terminal/schemes \
  --count 5 --seed 1

