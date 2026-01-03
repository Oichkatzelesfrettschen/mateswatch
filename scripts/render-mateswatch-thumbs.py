#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import os
import random
import re
import sys
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from theme_common import parse_rgb8, relative_contrast, srgb_to_luminance01


HEX16 = re.compile(r"^#?[0-9a-fA-F]{12}$")


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


def color16_to_rgb8(color: str) -> str | None:
    c = unquote(color).strip()
    if not c.startswith("#"):
        return None
    if not HEX16.match(c):
        return None
    return f"#{c[1:3]}{c[5:7]}{c[9:11]}".lower()


def parse_palette(palette_value: str) -> list[str] | None:
    raw = unquote(palette_value)
    parts = raw.split(":")
    if len(parts) != 16:
        return None
    out: list[str] = []
    for p in parts:
        c = color16_to_rgb8(p.strip())
        if c is None:
            return None
        out.append(c)
    return out


def stable_bucket(value: str, *, buckets: int) -> int:
    h = hashlib.sha1(value.encode("utf-8")).hexdigest()
    return int(h[:8], 16) % buckets


def parse_size(s: str) -> tuple[int, int]:
    m = re.match(r"^(\d+)x(\d+)$", s.strip())
    if not m:
        raise ValueError(f"invalid size: {s!r} (expected WxH)")
    return int(m.group(1)), int(m.group(2))


def luminance01(hex_rgb: str) -> float:
    r, g, b = parse_rgb8(hex_rgb)
    return srgb_to_luminance01(r, g, b)


def pick_text_color(bg_hex: str) -> tuple[int, int, int]:
    l = luminance01(bg_hex)
    return (0, 0, 0) if l > 0.55 else (255, 255, 255)


def to_rgb(hex_rgb: str) -> tuple[int, int, int]:
    r, g, b = parse_rgb8(hex_rgb)
    return r, g, b


def load_font(size: int, *, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = []
    if bold:
        candidates.extend(
            [
                "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf",
                "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
            ]
        )
    else:
        candidates.extend(
            [
                "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
                "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            ]
        )
    for p in candidates:
        try:
            return ImageFont.truetype(p, size=size)
        except OSError:
            continue
    return ImageFont.load_default()


@dataclass(frozen=True)
class Scheme:
    profile_id: str
    visible_name: str
    background: str
    foreground: str
    palette: list[str]


def parse_scheme(path: Path) -> Scheme | None:
    kv = read_kv(path.read_text(encoding="utf-8", errors="replace"))
    pal_raw = kv.get("palette")
    bg_raw = kv.get("background-color")
    fg_raw = kv.get("foreground-color")
    if not pal_raw or not bg_raw or not fg_raw:
        return None
    palette = parse_palette(pal_raw)
    if palette is None:
        return None
    bg = color16_to_rgb8(bg_raw)
    fg = color16_to_rgb8(fg_raw)
    if bg is None or fg is None:
        return None
    visible = unquote(kv.get("visible-name", path.stem))
    return Scheme(
        profile_id=path.stem,
        visible_name=visible,
        background=bg,
        foreground=fg,
        palette=palette,
    )


def draw_text_with_shadow(
    draw: ImageDraw.ImageDraw,
    xy: tuple[int, int],
    text: str,
    *,
    font: ImageFont.ImageFont,
    fill: tuple[int, int, int],
    shadow: tuple[int, int, int],
) -> None:
    x, y = xy
    # Soft outline/shadow for legibility across extreme palettes.
    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1)):
        draw.text((x + dx, y + dy), text, font=font, fill=shadow)
    draw.text((x, y), text, font=font, fill=fill)


def render_thumb(
    scheme: Scheme,
    *,
    size: tuple[int, int],
) -> Image.Image:
    w, h = size
    img = Image.new("RGB", (w, h), to_rgb(scheme.background))
    draw = ImageDraw.Draw(img)

    # Layout (designed for scan-first thumbnails):
    # - Top: BG and FG bars with large labels
    # - Middle: 4x4 labeled palette grid
    # - Bottom: token strip using palette-mapped colors
    pad = 10
    gap = 8
    bar_h = 34
    title_h = 22
    token_h = 34
    grid_h = h - (pad * 2 + title_h + bar_h * 2 + gap * 3 + token_h)
    grid_h = max(120, grid_h)

    font_title = load_font(16, bold=True)
    font_small = load_font(13, bold=False)
    font_cell = load_font(13, bold=True)

    y = pad
    # Title (truncated): visible name tends to be long; keep the start only.
    title = scheme.visible_name.strip()
    if len(title) > 64:
        title = title[:61].rstrip() + "…"
    draw_text_with_shadow(
        draw,
        (pad, y),
        title,
        font=font_title,
        fill=to_rgb(scheme.foreground),
        shadow=pick_text_color(scheme.background),
    )
    y += title_h

    # BG bar
    bg_rect = (pad, y, w - pad, y + bar_h)
    draw.rectangle(bg_rect, fill=to_rgb(scheme.background))
    bg_label = f"BG {scheme.background}"
    draw_text_with_shadow(
        draw,
        (pad + 10, y + 8),
        bg_label,
        font=font_small,
        fill=to_rgb(scheme.foreground),
        shadow=pick_text_color(scheme.background),
    )
    y += bar_h + 2

    # FG bar
    fg_rect = (pad, y, w - pad, y + bar_h)
    draw.rectangle(fg_rect, fill=to_rgb(scheme.foreground))
    fg_label = f"FG {scheme.foreground}"
    draw_text_with_shadow(
        draw,
        (pad + 10, y + 8),
        fg_label,
        font=font_small,
        fill=to_rgb(scheme.background),
        shadow=pick_text_color(scheme.foreground),
    )
    y += bar_h + gap

    # Palette grid 4x4
    grid_top = y
    grid_left = pad
    grid_right = w - pad
    grid_bottom = grid_top + grid_h
    grid_w = grid_right - grid_left
    cell_w = grid_w // 4
    cell_h = (grid_bottom - grid_top) // 4

    # Map grid to pairs: show normal/bright together (0 with 8, 1 with 9, …).
    pair_indices = [(i, i + 8) for i in range(8)]
    order = [pair_indices[0], pair_indices[1], pair_indices[2], pair_indices[3],
             pair_indices[4], pair_indices[5], pair_indices[6], pair_indices[7]]

    # Place as 4x4: first row = 0/8..3/11, second row = 4/12..7/15
    placements = [
        (0, 0, order[0][0]), (1, 0, order[0][1]),
        (2, 0, order[1][0]), (3, 0, order[1][1]),
        (0, 1, order[2][0]), (1, 1, order[2][1]),
        (2, 1, order[3][0]), (3, 1, order[3][1]),
        (0, 2, order[4][0]), (1, 2, order[4][1]),
        (2, 2, order[5][0]), (3, 2, order[5][1]),
        (0, 3, order[6][0]), (1, 3, order[6][1]),
        (2, 3, order[7][0]), (3, 3, order[7][1]),
    ]
    for gx, gy, idx in placements:
        x0 = grid_left + gx * cell_w
        y0 = grid_top + gy * cell_h
        x1 = x0 + cell_w - 2
        y1 = y0 + cell_h - 2
        c = scheme.palette[idx]
        draw.rectangle((x0, y0, x1, y1), fill=to_rgb(c))
        # Label: slot number, big enough to see while scrolling.
        label = str(idx)
        tc = pick_text_color(c)
        shadow = (0, 0, 0) if tc == (255, 255, 255) else (255, 255, 255)
        draw_text_with_shadow(
            draw, (x0 + 6, y0 + 6), label, font=font_cell, fill=tc, shadow=shadow
        )

    # Subtle grid outline
    draw.rectangle((grid_left, grid_top, grid_right - 1, grid_bottom - 1), outline=(255, 255, 255))

    y = grid_bottom + gap

    # Token strip: pure perceptual cue for “does this palette work for common code categories?”
    bg_rgb = to_rgb(scheme.background)
    draw.rectangle((pad, y, w - pad, y + token_h), fill=bg_rgb)
    # Use palette indices chosen to be stable across themes (not “correct” syntax mapping, but comparable).
    token_map = [
        ("// comment", 8),
        (" int", 12),
        (" main", 5),
        ("(", 7),
        ("void", 6),
        (")", 7),
        (" {", 7),
        (" return", 12),
        (" 42", 3),
        ("; }", 7),
        ("  \"str\"", 2),
    ]
    x = pad + 10
    y_text = y + 9
    for t, idx in token_map:
        col = to_rgb(scheme.palette[idx])
        draw.text((x, y_text), t, font=font_small, fill=col)
        x += draw.textlength(t, font=font_small)

    # Contrast ratio label in bottom-right.
    cr = relative_contrast(luminance01(scheme.background), luminance01(scheme.foreground))
    cr_label = f"CR {cr:.2f}"
    cr_w = int(draw.textlength(cr_label, font=font_small))
    cr_x = w - pad - 10 - cr_w
    cr_tc = to_rgb(scheme.foreground)
    cr_shadow = pick_text_color(scheme.background)
    draw_text_with_shadow(
        draw, (cr_x, y_text), cr_label, font=font_small, fill=cr_tc, shadow=cr_shadow
    )

    return img


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate scan-friendly mateswatch thumbnails (no terminal screenshotting)."
    )
    parser.add_argument("--schemes-dir", default="mate-terminal/schemes")
    parser.add_argument("--out-dir", default="generated/showcase/thumbs")
    parser.add_argument("--all", action="store_true", help="Render all schemes (slow)")
    parser.add_argument("--count", type=int, default=10, help="Sample size without --all")
    parser.add_argument("--seed", type=int, default=1)
    parser.add_argument("--shards", type=int, default=1)
    parser.add_argument("--shard-index", type=int, default=0)
    parser.add_argument("--size", default="560x315", help="Thumbnail size WxH")
    args = parser.parse_args()

    if args.shards < 1 or not (0 <= args.shard_index < args.shards):
        raise SystemExit("error: invalid --shards/--shard-index")

    try:
        size = parse_size(args.size)
    except ValueError as e:
        raise SystemExit(f"error: {e}")

    root = Path(args.schemes_dir)
    files = sorted(p for p in root.rglob("*.dconf") if p.is_file())
    if not files:
        print(f"error: no .dconf files found under {root}", file=sys.stderr)
        return 2

    rels = [(p, str(p.relative_to(root))) for p in files]
    files = [
        p
        for p, rel in rels
        if stable_bucket(rel, buckets=args.shards) == args.shard_index
    ]
    if not files:
        print("OK: no schemes assigned to this shard")
        return 0

    if not args.all:
        rng = random.Random(args.seed)
        files = rng.sample(files, k=min(args.count, len(files)))

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    failures: list[str] = []
    for path in files:
        scheme = parse_scheme(path)
        if scheme is None:
            failures.append(f"{path}: could not parse")
            continue
        try:
            img = render_thumb(scheme, size=size)
            out_path = out_dir / f"{scheme.profile_id}.jpg"
            img.save(out_path, format="JPEG", quality=85, optimize=True, progressive=True)
        except Exception as e:  # noqa: BLE001
            failures.append(f"{path}: {e}")

    if failures:
        print(f"FAIL: {len(failures)}/{len(files)} issues", file=sys.stderr)
        for f in failures[:50]:
            print(f"- {f}", file=sys.stderr)
        return 1

    print(f"OK: rendered {len(files)} thumbs (shard {args.shard_index}/{args.shards})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
