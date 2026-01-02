#!/usr/bin/env bash
set -euo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${root}"

echo "== validate scheme snippets =="
find mate-terminal/schemes -type f -name '*.dconf' -printf '%h\n' | sort -u | while read -r d; do
  python3 scripts/validate-mate-terminal-schemes.py --dir "$d"
done

echo "OK"
