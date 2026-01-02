#!/usr/bin/env bash
set -euo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${root}"

echo "== python: syntax =="
python3 -m compileall -q scripts || {
  echo "python compile failed" >&2
  exit 1
}

if command -v ruff >/dev/null 2>&1; then
  echo "== python: ruff =="
  ruff check scripts
else
  echo "!! ruff not found (skipping)" >&2
fi

if command -v black >/dev/null 2>&1; then
  echo "== python: black (check) =="
  black --check scripts
else
  echo "!! black not found (skipping)" >&2
fi

sh_files=(
  scripts/*.sh
  packaging/deb/*.sh
)

if command -v shellcheck >/dev/null 2>&1; then
  echo "== shell: shellcheck =="
  shellcheck -S warning "${sh_files[@]}"
else
  echo "!! shellcheck not found (skipping)" >&2
fi

if command -v shfmt >/dev/null 2>&1; then
  echo "== shell: shfmt (check) =="
  shfmt -d -i 2 -ci -bn "${sh_files[@]}"
else
  echo "!! shfmt not found (skipping)" >&2
fi

echo "OK"
