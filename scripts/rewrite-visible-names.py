#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from theme_common import dconf_quote


TAG_TOKENS = {
    "Dark",
    "Light",
    "HighC",
    "MedC",
    "LowC",
    "Vivid",
    "Muted",
    "Pastel",
    "Warm",
    "Cool",
    "Neutral",
}


def read_kv(text: str) -> dict[str, str]:
    kv: dict[str, str] = {}
    for line in text.splitlines():
        if not line or line.startswith("["):
            continue
        if "=" not in line:
            continue
        k, v = line.split("=", 1)
        kv[k.strip()] = v.strip()
    return kv


def unquote(s: str) -> str:
    if len(s) >= 2 and s[0] == "'" and s[-1] == "'":
        return s[1:-1]
    return s


def looks_like_tags(part: str) -> bool:
    if "·" not in part:
        return False
    tokens = set(part.split("·"))
    return bool(tokens & TAG_TOKENS)


def rewrite_visible_name(old_visible: str) -> str | None:
    # We only rewrite the legacy format:
    #   "TYPE VibeName — Tag·Tag·Tag·Tag — Original"
    # into:
    #   "TYPE Original — VibeName — Tag·Tag·Tag·Tag"
    parts = old_visible.split(" — ")
    if len(parts) != 3:
        return None

    first, mid, last = parts
    if not looks_like_tags(mid):
        # Already new format, or something custom.
        return None
    if len(first) < 4 or first[3] != " ":
        return None
    type_code = first[:3].upper()
    vibe_name = first[4:].strip()
    tags = mid.strip()
    original = last.strip()
    if not original:
        return None

    return f"{type_code} {original} — {vibe_name} — {tags}"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Rewrite legacy mateswatch visible-name format for all schemes."
    )
    parser.add_argument(
        "--schemes-dir",
        default="mate-terminal/schemes",
        help="Root directory containing *.dconf",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would change without writing files",
    )
    args = parser.parse_args()

    root = Path(args.schemes_dir)
    files = sorted(p for p in root.rglob("*.dconf") if p.is_file())
    changed = 0

    for path in files:
        text = path.read_text(encoding="utf-8", errors="replace")
        kv = read_kv(text)
        old_raw = kv.get("visible-name")
        if not old_raw:
            continue
        old_visible = unquote(old_raw)
        new_visible = rewrite_visible_name(old_visible)
        if not new_visible or new_visible == old_visible:
            continue

        changed += 1
        if args.dry_run:
            print(f"{path}: {old_visible!r} -> {new_visible!r}")
            continue

        new_line = f"visible-name={dconf_quote(new_visible)}"
        out_lines = []
        for line in text.splitlines():
            if line.startswith("visible-name="):
                out_lines.append(new_line)
            else:
                out_lines.append(line)
        path.write_text("\n".join(out_lines) + "\n", encoding="utf-8")

    if args.dry_run:
        print(f"Would rewrite {changed} files.")
    else:
        print(f"Rewrote {changed} files.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
