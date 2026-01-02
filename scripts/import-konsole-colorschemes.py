#!/usr/bin/env python3
from __future__ import annotations

import argparse
import configparser
import json
from pathlib import Path

from theme_common import fingerprint, format_visible_name, generate_mate_profile_dconf, slugify


def rgb_triplet_to_hex(value: str) -> str:
    parts = [p.strip() for p in value.split(",")]
    if len(parts) != 3:
        raise ValueError(f"expected r,g,b (got {value!r})")
    r, g, b = (int(p) for p in parts)
    return f"#{r:02x}{g:02x}{b:02x}"


def parse_colorscheme(path: Path) -> tuple[str, str, str, list[str]] | None:
    cp = configparser.ConfigParser(interpolation=None)
    cp.read(path, encoding="utf-8")

    name = cp.get("General", "Description", fallback=path.stem).strip()
    bg = cp.get("Background", "Color", fallback=None)
    fg = cp.get("Foreground", "Color", fallback=None)
    if bg is None or fg is None:
        return None

    try:
        bg_hex = rgb_triplet_to_hex(bg)
        fg_hex = rgb_triplet_to_hex(fg)
    except ValueError:
        return None

    normal: list[str] = []
    bright: list[str] = []
    for i in range(8):
        sec = f"Color{i}"
        sec_i = f"Color{i}Intense"
        if not cp.has_option(sec, "Color"):
            return None
        try:
            normal.append(rgb_triplet_to_hex(cp.get(sec, "Color")))
            if cp.has_option(sec_i, "Color"):
                bright.append(rgb_triplet_to_hex(cp.get(sec_i, "Color")))
            else:
                bright.append(normal[-1])
        except ValueError:
            return None

    palette = normal + bright
    if len(palette) != 16:
        return None
    return name, fg_hex, bg_hex, palette


def iter_inputs(paths: list[str]) -> list[Path]:
    files: list[Path] = []
    for p in paths:
        path = Path(p)
        if path.is_dir():
            files.extend(sorted(path.glob("*.colorscheme")))
        else:
            files.append(path)
    return files


def main() -> int:
    parser = argparse.ArgumentParser(description="Import Konsole *.colorscheme files into MATE Terminal dconf snippets.")
    parser.add_argument("paths", nargs="+", help="One or more .colorscheme files or directories")
    parser.add_argument("--output-dir", default="mate-terminal/schemes/konsole", help="Output directory for *.dconf")
    parser.add_argument("--prefix", default="kon-", help="Profile id prefix")
    args = parser.parse_args()

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    entries: list[dict[str, object]] = []
    seen_fp: dict[str, str] = {}
    used_ids: set[str] = set()

    for src in iter_inputs(args.paths):
        if not src.is_file():
            continue
        parsed = parse_colorscheme(src)
        if parsed is None:
            continue
        original_name, fg, bg, palette = parsed
        visible = format_visible_name("KON", original_name, bg, fg, palette)

        base_id = f"{args.prefix}{slugify(original_name)}"
        profile_id = base_id
        if profile_id in used_ids:
            profile_id = f"{base_id}-{slugify(src.stem)}"
        used_ids.add(profile_id)

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
                "source": "konsole .colorscheme",
                "source_path": str(src),
                "original_name": original_name,
                "profile_id": profile_id,
                "visible_name": visible,
                "fingerprint": fp,
                "duplicate_of": dup_of,
            }
        )

    (out_dir / "manifest.json").write_text(
        json.dumps(
            {"type_code": "KON", "count": len(entries), "entries": entries},
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print(f"Wrote {len(entries)} konsole schemes into {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

