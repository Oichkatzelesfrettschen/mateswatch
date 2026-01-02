#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from theme_common import (
    fingerprint,
    format_visible_name,
    generate_mate_profile_dconf,
    slugify,
)


SCHEME_NAME = re.compile(r"^#\s*Scheme name:\s*(.+?)\s*$")
COLOR_ASSIGN = re.compile(
    r'^color(\d{2})="([0-9a-fA-F]{2}/[0-9a-fA-F]{2}/[0-9a-fA-F]{2}|\$color\d{2})"'
)
FG_ASSIGN = re.compile(
    r'^color_foreground="([0-9a-fA-F]{2}/[0-9a-fA-F]{2}/[0-9a-fA-F]{2})"'
)
BG_ASSIGN = re.compile(
    r'^color_background="([0-9a-fA-F]{2}/[0-9a-fA-F]{2}/[0-9a-fA-F]{2})"'
)


def rrggbb_from_slashes(value: str) -> str:
    return "#" + value.replace("/", "").lower()


def display_name_from_filename(filename: str) -> str:
    stem = filename
    for prefix in ("base16-", "base24-"):
        if stem.startswith(prefix):
            stem = stem[len(prefix) :]
            break
    if stem.endswith(".sh"):
        stem = stem[:-3]
    return " ".join(stem.replace("-", " ").replace("_", " ").split())


def parse_script(path: Path) -> tuple[str, str, str, list[str]] | None:
    scheme_name = None
    colors_raw: dict[int, str] = {}
    fg = None
    bg = None
    for raw in path.read_text(encoding="utf-8", errors="replace").splitlines()[:120]:
        line = raw.strip()
        m = SCHEME_NAME.match(line)
        if m:
            scheme_name = m.group(1).strip()
            continue
        m = COLOR_ASSIGN.match(line)
        if m:
            idx = int(m.group(1), 10)
            if 0 <= idx <= 21:
                colors_raw[idx] = m.group(2)
            continue
        m = FG_ASSIGN.match(line)
        if m:
            fg = rrggbb_from_slashes(m.group(1))
            continue
        m = BG_ASSIGN.match(line)
        if m:
            bg = rrggbb_from_slashes(m.group(1))
            continue

    if fg is None or bg is None:
        return None

    def resolve(idx: int, seen: set[int]) -> str | None:
        if idx in seen:
            return None
        seen.add(idx)
        raw = colors_raw.get(idx)
        if raw is None:
            return None
        if raw.startswith("$color") and len(raw) == 8 and raw[-2:].isdigit():
            return resolve(int(raw[-2:], 10), seen)
        return rrggbb_from_slashes(raw)

    pal: list[str] = []
    for i in range(16):
        v = resolve(i, set())
        if v is None:
            return None
        pal.append(v)
    name = scheme_name or display_name_from_filename(path.name)
    return name, fg, bg, pal


def import_family(
    *, family: str, type_code: str, prefix: str, scripts_dir: Path, out_dir: Path
) -> int:
    out_dir.mkdir(parents=True, exist_ok=True)
    entries: list[dict[str, object]] = []
    seen_fp: dict[str, str] = {}

    scripts = sorted(scripts_dir.glob(f"{family}-*.sh"))
    for script in scripts:
        parsed = parse_script(script)
        if parsed is None:
            continue
        original_name, fg, bg, palette = parsed
        visible = format_visible_name(type_code, original_name, bg, fg, palette)
        profile_id = f"{prefix}{slugify(script.stem)}"

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
                "source": "tinted-theming/tinted-shell",
                "source_path": str(script),
                "original_name": original_name,
                "profile_id": profile_id,
                "visible_name": visible,
                "fingerprint": fp,
                "duplicate_of": dup_of,
            }
        )

    (out_dir / "manifest.json").write_text(
        json.dumps(
            {
                "source_repo": "https://github.com/tinted-theming/tinted-shell",
                "type_code": type_code,
                "family": family,
                "count": len(entries),
                "entries": entries,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print(f"Wrote {len(entries)} {family} themes into {out_dir}")
    return len(entries)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Import tinted-shell base16/base24 scripts into MATE Terminal dconf."
    )
    parser.add_argument(
        "--tinted-dir",
        default="/tmp/mateswatch-sources/tinted-shell",
        help="Path to tinted-shell repo",
    )
    parser.add_argument(
        "--out-base16",
        default="mate-terminal/schemes/tinted/base16",
        help="Output directory for base16",
    )
    parser.add_argument(
        "--out-base24",
        default="mate-terminal/schemes/tinted/base24",
        help="Output directory for base24",
    )
    parser.add_argument(
        "--prefix-base16", default="b16-", help="Profile id prefix for base16"
    )
    parser.add_argument(
        "--prefix-base24", default="b24-", help="Profile id prefix for base24"
    )
    args = parser.parse_args()

    tinted_dir = Path(args.tinted_dir)
    scripts_dir = tinted_dir / "scripts"
    if not scripts_dir.is_dir():
        raise SystemExit(f"error: expected scripts directory at {scripts_dir}")

    import_family(
        family="base16",
        type_code="B16",
        prefix=args.prefix_base16,
        scripts_dir=scripts_dir,
        out_dir=Path(args.out_base16),
    )
    import_family(
        family="base24",
        type_code="B24",
        prefix=args.prefix_base24,
        scripts_dir=scripts_dir,
        out_dir=Path(args.out_base24),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
