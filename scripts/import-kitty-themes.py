#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from theme_common import fingerprint, format_visible_name, generate_mate_profile_dconf, slugify


def parse_conf(path: Path) -> dict[str, str]:
    data: dict[str, str] = {}
    for raw in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        # kitty-themes format: key <spaces> value
        parts = line.split()
        if len(parts) < 2:
            continue
        key = parts[0].strip()
        value = parts[-1].strip()
        data[key] = value
    return data


def display_name_from_stem(stem: str) -> str:
    # Try to keep upstream naming recognizable while still readable.
    s = stem.replace("_", " ").strip()
    return " ".join(s.split())


def main() -> int:
    parser = argparse.ArgumentParser(description="Import dexpota/kitty-themes into MATE Terminal dconf snippets.")
    parser.add_argument("--kitty-dir", default="/tmp/mateswatch-sources/kitty-themes", help="Path to kitty-themes repo")
    parser.add_argument("--output-dir", default="mate-terminal/schemes/kitty", help="Output directory for *.dconf")
    parser.add_argument("--prefix", default="kty-", help="Profile id prefix")
    args = parser.parse_args()

    kitty_dir = Path(args.kitty_dir)
    themes_dir = kitty_dir / "themes"
    if not themes_dir.is_dir():
        raise SystemExit(f"error: expected kitty themes directory at {themes_dir}")

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    entries: list[dict[str, object]] = []
    seen_fp: dict[str, str] = {}

    theme_files = sorted(themes_dir.glob("*.conf"))
    for theme_file in theme_files:
        conf = parse_conf(theme_file)
        bg = conf.get("background")
        fg = conf.get("foreground")
        if not bg or not fg:
            continue
        palette: list[str] = []
        ok = True
        for i in range(16):
            v = conf.get(f"color{i}")
            if not v:
                ok = False
                break
            palette.append(v)
        if not ok:
            continue

        original_name = display_name_from_stem(theme_file.stem)
        visible = format_visible_name("KTY", original_name, bg, fg, palette)
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
                "source": "dexpota/kitty-themes",
                "source_path": str(theme_file),
                "original_name": original_name,
                "profile_id": profile_id,
                "visible_name": visible,
                "fingerprint": fp,
                "duplicate_of": dup_of,
            }
        )

    manifest = {
        "source_repo": "https://github.com/dexpota/kitty-themes",
        "type_code": "KTY",
        "count": len(entries),
        "entries": entries,
    }
    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    print(f"Wrote {len(entries)} kitty themes into {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

