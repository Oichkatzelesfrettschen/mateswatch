#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass


HEX_RGB8 = re.compile(r"^#?[0-9a-fA-F]{6}$")
HEX_RGB16 = re.compile(r"^#?[0-9a-fA-F]{12}$")
SAFE_ID = re.compile(r"[^a-z0-9._+-]+")


def dconf_quote(value: str) -> str:
    return "'" + value.replace("\\", "\\\\").replace("'", "\\'") + "'"


def normalize_hex(color: str) -> str:
    c = color.strip()
    if c.startswith("0x") or c.startswith("0X"):
        c = c[2:]
    if not c.startswith("#"):
        c = "#" + c
    return c


def require_hex_rgb(color: str, what: str) -> str:
    c = normalize_hex(color)
    if HEX_RGB8.match(c) or HEX_RGB16.match(c):
        return c
    raise ValueError(f"{what}: expected #RRGGBB or #RRRRGGGGBBBB, got {color!r}")


def color_to_rgb16(color: str) -> str:
    c = require_hex_rgb(color, "color")
    if HEX_RGB16.match(c):
        return c.upper()
    r = c[1:3]
    g = c[3:5]
    b = c[5:7]
    return f"#{r}{r}{g}{g}{b}{b}".upper()


def color_to_rgb8(color: str) -> str:
    c = require_hex_rgb(color, "color")
    if HEX_RGB8.match(c):
        return c.lower()
    r = c[1:5]
    g = c[5:9]
    b = c[9:13]
    return f"#{r[:2]}{g[:2]}{b[:2]}".lower()


def parse_rgb8(color: str) -> tuple[int, int, int]:
    c = color_to_rgb8(color)
    return int(c[1:3], 16), int(c[3:5], 16), int(c[5:7], 16)


def srgb_to_luminance01(r: int, g: int, b: int) -> float:
    def f(x: float) -> float:
        x = x / 255.0
        return x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4

    rl, gl, bl = f(r), f(g), f(b)
    return 0.2126 * rl + 0.7152 * gl + 0.0722 * bl


def relative_contrast(bg_l: float, fg_l: float) -> float:
    lo = min(bg_l, fg_l)
    hi = max(bg_l, fg_l)
    return (hi + 0.05) / (lo + 0.05)


def rgb_to_hsv(r: int, g: int, b: int) -> tuple[float, float, float]:
    rf, gf, bf = r / 255.0, g / 255.0, b / 255.0
    mx = max(rf, gf, bf)
    mn = min(rf, gf, bf)
    d = mx - mn
    if d == 0:
        h = 0.0
    elif mx == rf:
        h = (60 * ((gf - bf) / d) + 360) % 360
    elif mx == gf:
        h = (60 * ((bf - rf) / d) + 120) % 360
    else:
        h = (60 * ((rf - gf) / d) + 240) % 360
    s = 0.0 if mx == 0 else d / mx
    v = mx
    return h, s, v


@dataclass(frozen=True)
class Vibe:
    name: str
    tags: list[str]
    background_kind: str  # "dark" or "light"


def vibe_for_scheme(background: str, foreground: str, palette: list[str]) -> Vibe:
    br, bg, bb = parse_rgb8(background)
    fr, fg, fb = parse_rgb8(foreground)
    bg_l = srgb_to_luminance01(br, bg, bb)
    fg_l = srgb_to_luminance01(fr, fg, fb)
    contrast = relative_contrast(bg_l, fg_l)

    bg_kind = "dark" if bg_l < 0.35 else "light"

    # Use a "representative accent" from the bright blue/cyan slot if present, else pick the highest-sat palette color.
    candidates = []
    for idx in (12, 14, 4, 6, 9, 13, 10, 11):
        if 0 <= idx < len(palette):
            candidates.append(palette[idx])
    if not candidates:
        candidates = palette[:]

    best = candidates[0]
    best_s = -1.0
    for c in candidates:
        r, g, b = parse_rgb8(c)
        h, s, v = rgb_to_hsv(r, g, b)
        if s > best_s:
            best_s = s
            best = c

    ar, ag, ab = parse_rgb8(best)
    hue, sat, val = rgb_to_hsv(ar, ag, ab)

    tags: list[str] = []
    tags.append("Dark" if bg_kind == "dark" else "Light")
    tags.append("HighC" if contrast >= 7.0 else ("MedC" if contrast >= 4.5 else "LowC"))
    tags.append("Vivid" if sat >= 0.65 else ("Pastel" if sat >= 0.40 and bg_kind == "light" else "Muted"))

    warm = "Warm" if (hue < 70 or hue >= 290) else ("Cool" if 160 <= hue <= 260 else "Neutral")
    tags.append(warm)

    hue_name = (
        "Crimson"
        if hue < 20 or hue >= 340
        else "Amber"
        if hue < 55
        else "Lime"
        if hue < 95
        else "Jade"
        if hue < 145
        else "Cyan"
        if hue < 195
        else "Azure"
        if hue < 225
        else "Indigo"
        if hue < 265
        else "Orchid"
        if hue < 305
        else "Rose"
    )

    if bg_kind == "dark":
        adj = "Nocturne" if val < 0.8 else "Neon"
    else:
        adj = "Dawn" if val < 0.8 else "Daylight"

    return Vibe(name=f"{adj} {hue_name}", tags=tags, background_kind=bg_kind)


def slugify(text: str) -> str:
    s = text.strip().lower()
    s = SAFE_ID.sub("-", s).strip("-")
    return s or "unnamed"


def format_visible_name(type_code: str, original_name: str, background: str, foreground: str, palette: list[str]) -> str:
    vibe = vibe_for_scheme(background, foreground, palette)
    tags = "·".join(vibe.tags)
    # Format requested: NEWNAME - DESC - OLDNAME, while keeping type clusterable.
    # Put TYPE in NEWNAME and keep the "old" title last for recognition.
    return f"{type_code} {vibe.name} — {tags} — {original_name}"


def fingerprint(background: str, foreground: str, palette: list[str]) -> str:
    norm = [color_to_rgb16(background), color_to_rgb16(foreground)] + [color_to_rgb16(c) for c in palette]
    h = hashlib.sha1()
    h.update("\n".join(norm).encode("utf-8"))
    return h.hexdigest()


def generate_mate_profile_dconf(*, visible_name: str, use_theme_colors: bool, foreground: str, background: str, palette: list[str]) -> str:
    palette16 = ":".join(color_to_rgb16(c) for c in palette)
    lines = [
        "[/]",
        f"visible-name={dconf_quote(visible_name)}",
        f"use-theme-colors={'true' if use_theme_colors else 'false'}",
    ]
    if not use_theme_colors:
        fg16 = color_to_rgb16(foreground)
        bg16 = color_to_rgb16(background)
        cursor = color_to_rgb8(foreground)
        lines.extend(
            [
                f"foreground-color={dconf_quote(fg16)}",
                f"background-color={dconf_quote(bg16)}",
                "bold-color-same-as-fg=true",
                f"bold-color={dconf_quote(fg16)}",
                f"cursor-color={dconf_quote(cursor)}",
            ]
        )
    lines.extend([f"palette={dconf_quote(palette16)}", ""])
    return "\n".join(lines)
