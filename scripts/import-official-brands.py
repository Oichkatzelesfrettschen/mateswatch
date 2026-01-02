#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from theme_common import format_visible_name, generate_mate_profile_dconf, require_hex_rgb


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def read_color(path: Path) -> str:
    return require_hex_rgb(read_text(path).strip(), str(path))


def parse_simple_kv_colors(text: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split()
        if len(parts) < 2:
            continue
        key = parts[0].strip()
        value = parts[1].strip()
        if key in {"foreground", "background"} or re.fullmatch(r"color(?:[0-9]|1[0-5])", key):
            out[key] = require_hex_rgb(value, key)
    return out


def parse_kitty_theme(path: Path) -> tuple[str, str, list[str]]:
    kv = parse_simple_kv_colors(read_text(path))
    fg = kv.get("foreground")
    bg = kv.get("background")
    if not fg or not bg:
        raise ValueError(f"{path}: missing foreground/background")
    palette: list[str] = []
    for i in range(16):
        k = f"color{i}"
        if k not in kv:
            raise ValueError(f"{path}: missing {k}")
        palette.append(kv[k])
    return bg, fg, palette


def load_toml(path: Path) -> dict:
    try:
        import tomllib  # py3.11+
    except ModuleNotFoundError:  # pragma: no cover
        import tomli as tomllib  # type: ignore
    return tomllib.loads(read_text(path))


def parse_wezterm_toml(path: Path) -> tuple[str, str, list[str]]:
    data = load_toml(path)
    colors = data.get("colors") or {}
    ansi = colors.get("ansi") or []
    brights = colors.get("brights") or []
    bg = colors.get("background")
    fg = colors.get("foreground")
    if not isinstance(ansi, list) or not isinstance(brights, list):
        raise ValueError(f"{path}: expected colors.ansi/brights arrays")
    if len(ansi) != 8 or len(brights) != 8:
        raise ValueError(f"{path}: expected 8 ansi + 8 brights, got {len(ansi)} + {len(brights)}")
    if not isinstance(bg, str) or not isinstance(fg, str):
        raise ValueError(f"{path}: missing colors.background/foreground")
    palette = [require_hex_rgb(c, f"{path}:ansi") for c in ansi] + [require_hex_rgb(c, f"{path}:brights") for c in brights]
    return require_hex_rgb(bg, f"{path}:background"), require_hex_rgb(fg, f"{path}:foreground"), palette


def write_profile(path: Path, *, type_code: str, original_name: str, bg: str, fg: str, palette: list[str]) -> None:
    visible = format_visible_name(type_code, original_name, bg, fg, palette)
    dconf = generate_mate_profile_dconf(visible_name=visible, use_theme_colors=False, foreground=fg, background=bg, palette=palette)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(dconf, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Import official Dracula/Catppuccin sources into MATE Terminal .dconf schemes.")
    parser.add_argument("--sources", default="sources", help="Root directory containing vendored upstream sources.")
    parser.add_argument("--out-dir", default="mate-terminal/schemes/brands", help="Output directory for generated *.dconf files.")
    parser.add_argument(
        "--only",
        action="append",
        default=[],
        help="Limit import to a source key (repeatable): dracula-gnome-terminal, dracula-kitty, dracula-wezterm, catppuccin-gnome-terminal, catppuccin-kitty, catppuccin-wezterm",
    )
    args = parser.parse_args()

    only = set(args.only or [])
    sources = Path(args.sources)
    out_root = Path(args.out_dir)

    def enabled(key: str) -> bool:
        return not only or key in only

    # Dracula (GNOME Terminal)
    if enabled("dracula-gnome-terminal"):
        base = sources / "dracula" / "gnome-terminal" / "colors" / "Dracula"
        bg = read_color(base / "bg_color")
        fg = read_color(base / "fg_color")
        pal = [require_hex_rgb(x, "palette") for x in read_text(base / "palette").splitlines() if x.strip()]
        if len(pal) != 16:
            raise ValueError(f"{base/'palette'}: expected 16 colors, got {len(pal)}")
        write_profile(
            out_root / "dracula" / "drc-dracula-gnome-terminal.dconf",
            type_code="DRC",
            original_name="Dracula (GNOME Terminal)",
            bg=bg,
            fg=fg,
            palette=pal,
        )

    # Dracula (kitty)
    if enabled("dracula-kitty"):
        bg, fg, pal = parse_kitty_theme(sources / "dracula" / "kitty" / "dracula.conf")
        write_profile(
            out_root / "dracula" / "drc-dracula-kitty.dconf",
            type_code="DRC",
            original_name="Dracula (kitty)",
            bg=bg,
            fg=fg,
            palette=pal,
        )

    # Dracula (WezTerm)
    if enabled("dracula-wezterm"):
        bg, fg, pal = parse_wezterm_toml(sources / "dracula" / "wezterm" / "dracula.toml")
        write_profile(
            out_root / "dracula" / "drc-dracula-wezterm.dconf",
            type_code="DRC",
            original_name="Dracula (WezTerm)",
            bg=bg,
            fg=fg,
            palette=pal,
        )

    # Catppuccin (GNOME Terminal) via pinned palette.json
    if enabled("catppuccin-gnome-terminal"):
        palette_json = json.loads(read_text(sources / "catppuccin" / "palette" / "palette.json"))
        palette_json.pop("version", None)
        for flavor in ("latte", "frappe", "macchiato", "mocha"):
            obj = palette_json[flavor]
            colors = obj["colors"]
            ansi = obj["ansiColors"]
            order = ["black", "red", "green", "yellow", "blue", "magenta", "cyan", "white"]
            pal = [ansi[k]["normal"]["hex"] for k in order] + [ansi[k]["bright"]["hex"] for k in order]
            bg = colors["base"]["hex"]
            fg = colors["text"]["hex"]
            write_profile(
                out_root / "catppuccin" / f"ctp-catppuccin-{flavor}-gnome-terminal.dconf",
                type_code="CTP",
                original_name=f"Catppuccin {flavor.capitalize()} (GNOME Terminal)",
                bg=require_hex_rgb(bg, "background"),
                fg=require_hex_rgb(fg, "foreground"),
                palette=[require_hex_rgb(c, "palette") for c in pal],
            )

    # Catppuccin (kitty)
    if enabled("catppuccin-kitty"):
        base = sources / "catppuccin" / "kitty" / "themes"
        for flavor in ("latte", "frappe", "macchiato", "mocha"):
            bg, fg, pal = parse_kitty_theme(base / f"{flavor}.conf")
            write_profile(
                out_root / "catppuccin" / f"ctp-catppuccin-{flavor}-kitty.dconf",
                type_code="CTP",
                original_name=f"Catppuccin {flavor.capitalize()} (kitty)",
                bg=bg,
                fg=fg,
                palette=pal,
            )

    # Catppuccin (WezTerm)
    if enabled("catppuccin-wezterm"):
        base = sources / "catppuccin" / "wezterm" / "dist"
        for flavor in ("latte", "frappe", "macchiato", "mocha"):
            bg, fg, pal = parse_wezterm_toml(base / f"catppuccin-{flavor}.toml")
            write_profile(
                out_root / "catppuccin" / f"ctp-catppuccin-{flavor}-wezterm.dconf",
                type_code="CTP",
                original_name=f"Catppuccin {flavor.capitalize()} (WezTerm)",
                bg=bg,
                fg=fg,
                palette=pal,
            )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
