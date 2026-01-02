#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from theme_common import fingerprint, format_visible_name, generate_mate_profile_dconf, slugify


def main() -> int:
    parser = argparse.ArgumentParser(description="Import WezTerm built-in color schemes into MATE Terminal dconf.")
    parser.add_argument("--wezterm-dir", default="/tmp/mateswatch-sources/wezterm", help="Path to wezterm repo")
    parser.add_argument("--output-dir", default="mate-terminal/schemes/wezterm", help="Output directory for *.dconf")
    parser.add_argument("--prefix", default="wzt-", help="Profile id prefix")
    args = parser.parse_args()

    wezterm_dir = Path(args.wezterm_dir)
    data_path = wezterm_dir / "docs" / "colorschemes" / "data.json"
    if not data_path.is_file():
        raise SystemExit(f"error: expected {data_path}")

    data = json.loads(data_path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise SystemExit("error: wezterm data.json unexpected format (expected a list)")

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    entries: list[dict[str, object]] = []
    seen_fp: dict[str, str] = {}
    used_ids: set[str] = set()

    for item in data:
        if not isinstance(item, dict):
            continue
        colors = item.get("colors")
        meta = item.get("metadata")
        if not isinstance(colors, dict) or not isinstance(meta, dict):
            continue

        name = meta.get("name")
        if not isinstance(name, str) or not name.strip():
            continue

        bg = colors.get("background")
        fg = colors.get("foreground")
        ansi = colors.get("ansi")
        brights = colors.get("brights")
        if not isinstance(bg, str) or not isinstance(fg, str):
            continue
        if not isinstance(ansi, list) or not isinstance(brights, list) or len(ansi) != 8 or len(brights) != 8:
            continue
        if not all(isinstance(x, str) for x in ansi + brights):
            continue

        palette = list(ansi) + list(brights)
        visible = format_visible_name("WZT", name.strip(), bg, fg, palette)

        base_id = f"{args.prefix}{slugify(name)}"
        profile_id = base_id
        if profile_id in used_ids:
            profile_id = f"{base_id}-{slugify(meta.get('author', '') if isinstance(meta.get('author'), str) else '')}"
            profile_id = profile_id.rstrip("-")
        if profile_id in used_ids:
            # last resort: disambiguate by fingerprint prefix
            profile_id = f"{base_id}-{fingerprint(bg, fg, palette)[:8]}"
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
                "source": "wez/wezterm (docs/colorschemes/data.json)",
                "source_path": str(data_path),
                "original_name": name.strip(),
                "profile_id": profile_id,
                "visible_name": visible,
                "fingerprint": fp,
                "duplicate_of": dup_of,
                "author": meta.get("author"),
                "origin_url": meta.get("origin_url"),
                "aliases": meta.get("aliases"),
            }
        )

    (out_dir / "manifest.json").write_text(
        json.dumps(
            {
                "source_repo": "https://github.com/wez/wezterm",
                "source_path": str(data_path),
                "type_code": "WZT",
                "count": len(entries),
                "entries": entries,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    print(f"Wrote {len(entries)} wezterm schemes into {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

