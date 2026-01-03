#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path

from theme_common import color_to_rgb8, fingerprint, vibe_for_scheme


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


def infer_type(profile_id: str, visible_name: str) -> str:
    v = visible_name.strip()
    if len(v) >= 4 and v[3] == " " and v[:3].isalpha():
        return v[:3].upper()
    if profile_id.startswith("gogh-"):
        return "GOG"
    if profile_id.startswith("kty-"):
        return "KTY"
    if profile_id.startswith("ala-"):
        return "ALA"
    if profile_id.startswith("b16-"):
        return "B16"
    if profile_id.startswith("b24-"):
        return "B24"
    if profile_id.startswith("wzt-"):
        return "WZT"
    if profile_id.startswith("kon-"):
        return "KON"
    if profile_id.lower() == "atom":
        return "MSW"
    return "UNK"


def parse_palette(palette_value: str) -> list[str] | None:
    raw = unquote(palette_value)
    parts = raw.split(":")
    if len(parts) != 16:
        return None
    return [color_to_rgb8(p) for p in parts]


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build a cross-corpus mateswatch index + vibe stats."
    )
    parser.add_argument(
        "--schemes-dir",
        default="mate-terminal/schemes",
        help="Root directory containing *.dconf",
    )
    parser.add_argument(
        "--out-json", default="docs/mateswatch-index.json", help="Output JSON path"
    )
    parser.add_argument(
        "--out-stats",
        default="docs/mateswatch-stats.md",
        help="Output stats markdown path",
    )
    args = parser.parse_args()

    root = Path(args.schemes_dir)
    files = sorted(p for p in root.rglob("*.dconf") if p.is_file())
    if not files:
        raise SystemExit(f"no .dconf files found under {root}")

    entries: list[dict[str, object]] = []
    fp_to_ids: dict[str, list[str]] = defaultdict(list)
    type_counts: Counter[str] = Counter()
    tag_counts: Counter[str] = Counter()

    for path in files:
        profile_id = path.stem
        kv = read_kv(path.read_text(encoding="utf-8", errors="replace"))
        visible = unquote(kv.get("visible-name", profile_id))
        pal_raw = kv.get("palette")
        bg_raw = kv.get("background-color")
        fg_raw = kv.get("foreground-color")
        if pal_raw is None or bg_raw is None or fg_raw is None:
            continue
        palette = parse_palette(pal_raw)
        if palette is None:
            continue
        bg = color_to_rgb8(unquote(bg_raw))
        fg = color_to_rgb8(unquote(fg_raw))

        vib = vibe_for_scheme(bg, fg, palette)
        fp = fingerprint(bg, fg, palette)
        type_code = infer_type(profile_id, visible)

        type_counts[type_code] += 1
        for t in vib.tags:
            tag_counts[t] += 1

        fp_to_ids[fp].append(profile_id)
        entries.append(
            {
                "profile_id": profile_id,
                "type": type_code,
                "visible_name": visible,
                "vibe_name": vib.name,
                "vibe_tags": vib.tags,
                "background": bg,
                "foreground": fg,
                "palette": palette,
                "fingerprint": fp,
                "path": str(path),
            }
        )

    duplicates = {fp: ids for fp, ids in fp_to_ids.items() if len(ids) > 1}

    out_json = Path(args.out_json)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(
        json.dumps(
            {
                "count": len(entries),
                "types": dict(type_counts),
                "tag_counts": dict(tag_counts),
                "duplicate_fingerprints": {
                    k: v
                    for k, v in sorted(duplicates.items(), key=lambda kv: -len(kv[1]))
                },
                "entries": entries,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    out_stats = Path(args.out_stats)
    out_stats.parent.mkdir(parents=True, exist_ok=True)

    lines = []
    lines.append("# mateswatch stats")
    lines.append("")
    lines.append(f"- Profiles indexed: **{len(entries)}**")
    lines.append(f"- Duplicate fingerprints: **{len(duplicates)}**")
    lines.append("")
    lines.append("## By type")
    lines.append("")
    for t, c in type_counts.most_common():
        lines.append(f"- {t}: {c}")
    lines.append("")
    lines.append("## Vibe tags (global)")
    lines.append("")
    for t, c in tag_counts.most_common():
        lines.append(f"- {t}: {c}")
    lines.append("")

    out_stats.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"Wrote {out_json} and {out_stats}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
