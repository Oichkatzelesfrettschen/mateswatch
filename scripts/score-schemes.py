#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from theme_common import parse_rgb8, relative_contrast, rgb_to_hsv, srgb_to_luminance01


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


def parse_palette(palette_value: str) -> list[str] | None:
    raw = unquote(palette_value)
    parts = raw.split(":")
    if len(parts) != 16:
        return None
    # palette entries are #RRRRGGGGBBBB; take first 2 bytes of each component
    out: list[str] = []
    for p in parts:
        p = p.strip()
        if len(p) == 13 and p.startswith("#"):
            out.append(f"#{p[1:3]}{p[5:7]}{p[9:11]}".lower())
        else:
            return None
    return out


def score_scheme(bg_hex: str, fg_hex: str, palette: list[str]) -> dict[str, float]:
    br, bg, bb = parse_rgb8(bg_hex)
    fr, fg, fb = parse_rgb8(fg_hex)
    bg_l = srgb_to_luminance01(br, bg, bb)
    fg_l = srgb_to_luminance01(fr, fg, fb)
    cr = relative_contrast(bg_l, fg_l)

    # Palette “spread”: pairwise max-channel diff average on core hues (red/green/yellow/blue).
    core = [palette[i] for i in (1, 2, 3, 4, 9, 10, 11, 12)]
    pts = [parse_rgb8(c) for c in core]
    diffs = []
    for i in range(len(pts)):
        for j in range(i + 1, len(pts)):
            a = pts[i]
            b = pts[j]
            diffs.append(max(abs(a[0] - b[0]), abs(a[1] - b[1]), abs(a[2] - b[2])))
    spread = sum(diffs) / max(1, len(diffs))

    # Background “tint”: saturation of background (prefer lower for terminal backgrounds).
    h, s, v = rgb_to_hsv(br, bg, bb)
    _ = h
    _ = v

    return {
        "contrast_ratio": cr,
        "palette_core_spread": spread,
        "background_saturation": s,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Heuristic scoring for schemes (not a visual proof)."
    )
    parser.add_argument(
        "--schemes-dir",
        default="mate-terminal/schemes",
        help="Root directory containing *.dconf",
    )
    parser.add_argument(
        "--out", default="docs/mateswatch-scheme-scores.json", help="Output JSON report"
    )
    args = parser.parse_args()

    root = Path(args.schemes_dir)
    files = sorted(p for p in root.rglob("*.dconf") if p.is_file())
    rows: list[dict[str, object]] = []
    for path in files:
        kv = read_kv(path.read_text(encoding="utf-8", errors="replace"))
        pal_raw = kv.get("palette")
        bg_raw = kv.get("background-color")
        fg_raw = kv.get("foreground-color")
        vis = unquote(kv.get("visible-name", path.stem))
        if not pal_raw or not bg_raw or not fg_raw:
            continue
        palette = parse_palette(pal_raw)
        if not palette:
            continue
        bg = unquote(bg_raw)
        fg = unquote(fg_raw)
        bg8 = (
            f"#{bg[1:3]}{bg[5:7]}{bg[9:11]}".lower()
            if len(bg) == 13 and bg.startswith("#")
            else bg.lower()
        )
        fg8 = (
            f"#{fg[1:3]}{fg[5:7]}{fg[9:11]}".lower()
            if len(fg) == 13 and fg.startswith("#")
            else fg.lower()
        )
        s = score_scheme(bg8, fg8, palette)
        rows.append({"profile_id": path.stem, "visible_name": vis, **s})

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        json.dumps({"count": len(rows), "rows": rows}, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
