#!/usr/bin/env python3
import argparse
import re
import sys
from pathlib import Path


HEX16 = re.compile(r"^'#(?:[0-9A-F]{4}){3}'$")
HEX8 = re.compile(r"^'#[0-9a-f]{6}'$")


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


def validate_file(path: Path) -> list[str]:
    errors: list[str] = []
    text = path.read_text(encoding="utf-8")
    if not text.startswith("[/]\n") and text.strip() != "[/]":
        errors.append("missing leading [/]")
    kv = read_kv(text)

    if "visible-name" not in kv:
        errors.append("missing visible-name")
    if kv.get("use-theme-colors") != "false":
        errors.append(
            f"use-theme-colors must be false (got {kv.get('use-theme-colors')!r})"
        )

    fg = kv.get("foreground-color")
    bg = kv.get("background-color")
    if fg is None or not HEX16.match(fg):
        errors.append(f"foreground-color must be 16-bit quoted hex (got {fg!r})")
    if bg is None or not HEX16.match(bg):
        errors.append(f"background-color must be 16-bit quoted hex (got {bg!r})")

    cursor = kv.get("cursor-color")
    if cursor is None or not HEX8.match(cursor):
        errors.append(f"cursor-color must be 8-bit quoted hex (got {cursor!r})")

    palette = kv.get("palette")
    if palette is None:
        errors.append("missing palette")
    else:
        parts = (
            palette.strip("'").split(":")
            if palette.startswith("'") and palette.endswith("'")
            else []
        )
        if len(parts) != 16:
            errors.append(f"palette must contain 16 colors (got {len(parts)})")
        else:
            for p in parts:
                if not re.match(r"^#(?:[0-9A-F]{4}){3}$", p):
                    errors.append(f"palette color not 16-bit hex: {p!r}")
                    break

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate generated MATE Terminal dconf scheme snippets."
    )
    parser.add_argument(
        "--dir",
        default="mate-terminal/schemes/gogh",
        help="Directory containing *.dconf files",
    )
    args = parser.parse_args()

    root = Path(args.dir)
    files = sorted(p for p in root.glob("*.dconf") if p.is_file())
    if not files:
        sys.stderr.write(f"no .dconf files found in {root}\n")
        return 2

    failed = 0
    for path in files:
        errs = validate_file(path)
        if errs:
            failed += 1
            sys.stderr.write(f"{path}:\n")
            for e in errs[:6]:
                sys.stderr.write(f"  - {e}\n")

    if failed:
        sys.stderr.write(f"validation failures: {failed}/{len(files)}\n")
        return 1

    print(f"ok: {len(files)} files validated in {root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
