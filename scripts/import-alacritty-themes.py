#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from theme_common import (
    fingerprint,
    format_visible_name,
    generate_mate_profile_dconf,
    slugify,
)

try:
    import tomllib  # py3.11+
except Exception:  # pragma: no cover
    tomllib = None  # type: ignore


ORDER = ["black", "red", "green", "yellow", "blue", "magenta", "cyan", "white"]


def read_header_name(path: Path) -> str | None:
    for raw in path.read_text(encoding="utf-8", errors="replace").splitlines()[:30]:
        line = raw.strip()
        if line.lower().startswith("# name:"):
            return line.split(":", 1)[1].strip()
    return None


def display_name_from_filename(path: Path) -> str:
    return " ".join(path.stem.replace("_", " ").replace(".", " ").split())


def parse_theme(path: Path) -> tuple[str, str, str, list[str]] | None:
    if tomllib is None:
        raise SystemExit("error: tomllib not available (need Python 3.11+)")

    data = tomllib.loads(path.read_text(encoding="utf-8"))
    colors = data.get("colors") or {}
    primary = (colors.get("primary") or {}) if isinstance(colors, dict) else {}
    normal = (colors.get("normal") or {}) if isinstance(colors, dict) else {}
    bright = (colors.get("bright") or {}) if isinstance(colors, dict) else {}

    bg = primary.get("background")
    fg = primary.get("foreground")
    if not isinstance(bg, str) or not isinstance(fg, str):
        return None

    pal: list[str] = []
    for k in ORDER:
        v = normal.get(k)
        if not isinstance(v, str):
            return None
        pal.append(v)
    for k in ORDER:
        v = bright.get(k)
        if not isinstance(v, str):
            return None
        pal.append(v)
    if len(pal) != 16:
        return None

    name = read_header_name(path) or display_name_from_filename(path)
    return name, fg, bg, pal


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Import rajasegar/alacritty-themes into MATE Terminal dconf snippets."
    )
    parser.add_argument(
        "--alacritty-dir",
        default="/tmp/mateswatch-sources/alacritty-themes",
        help="Path to alacritty-themes repo",
    )
    parser.add_argument(
        "--output-dir",
        default="mate-terminal/schemes/alacritty",
        help="Output directory for *.dconf",
    )
    parser.add_argument("--prefix", default="ala-", help="Profile id prefix")
    args = parser.parse_args()

    root = Path(args.alacritty_dir)
    themes_dir = root / "themes"
    if not themes_dir.is_dir():
        raise SystemExit(f"error: expected theme directory at {themes_dir}")

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    entries: list[dict[str, object]] = []
    seen_fp: dict[str, str] = {}

    theme_files = sorted(themes_dir.glob("*.toml"))
    for theme_file in theme_files:
        parsed = parse_theme(theme_file)
        if parsed is None:
            continue
        original_name, fg, bg, palette = parsed
        visible = format_visible_name("ALA", original_name, bg, fg, palette)
        profile_id = f"{args.prefix}{slugify(theme_file.stem)}"

        fp = fingerprint(bg, fg, palette)
        dup_of = seen_fp.get(fp)
        if dup_of is None:
            seen_fp[fp] = profile_id

        dconf_text = generate_mate_profile_dconf(
            visible_name=visible,
            use_theme_colors=False,
            foreground=fg,
            background=bg,
            palette=palette,
        )
        (out_dir / f"{profile_id}.dconf").write_text(dconf_text, encoding="utf-8")

        entries.append(
            {
                "source": "rajasegar/alacritty-themes",
                "source_path": str(theme_file),
                "original_name": original_name,
                "profile_id": profile_id,
                "visible_name": visible,
                "fingerprint": fp,
                "duplicate_of": dup_of,
            }
        )

    manifest = {
        "source_repo": "https://github.com/rajasegar/alacritty-themes",
        "type_code": "ALA",
        "count": len(entries),
        "entries": entries,
    }
    (out_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )

    print(f"Wrote {len(entries)} alacritty themes into {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
