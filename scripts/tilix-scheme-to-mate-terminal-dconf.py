#!/usr/bin/env python3
import argparse
import json
import re
import sys


HEX_RGB = re.compile(r"^#[0-9a-fA-F]{6}$")


def dconf_quote(value: str) -> str:
    # dconf uses single-quoted strings; escape embedded single quotes.
    return "'" + value.replace("\\", "\\\\").replace("'", "\\'") + "'"


def rgb8_to_rgb16(color: str) -> str:
    if not HEX_RGB.match(color):
        raise ValueError(f"expected #RRGGBB, got {color!r}")
    r = color[1:3]
    g = color[3:5]
    b = color[5:7]
    return f"#{r}{r}{g}{g}{b}{b}".upper()


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Convert a Tilix scheme JSON to a MATE Terminal dconf profile snippet."
    )
    parser.add_argument("tilix_json", help="Path to Tilix scheme JSON (e.g. tilix/schemes/atom.json)")
    parser.add_argument("--profile-id", default="Atom", help="Target profile id (dconf folder name)")
    parser.add_argument("--visible-name", default="Atom", help="Profile visible name shown in UI")
    parser.add_argument(
        "--cursor-color",
        default=None,
        help="Cursor color as #RRGGBB (defaults to Tilix foreground-color)",
    )
    args = parser.parse_args()

    with open(args.tilix_json, "r", encoding="utf-8") as file:
        tilix = json.load(file)

    fg = tilix.get("foreground-color")
    bg = tilix.get("background-color")
    palette = tilix.get("palette")
    if fg is None or bg is None or palette is None:
        raise SystemExit("tilix scheme must include foreground-color, background-color, and palette")
    if not isinstance(palette, list) or len(palette) != 16:
        raise SystemExit("tilix scheme palette must be an array of 16 colors")

    fg16 = rgb8_to_rgb16(fg)
    bg16 = rgb8_to_rgb16(bg)
    pal16 = ":".join(rgb8_to_rgb16(c) for c in palette)
    cursor = args.cursor_color or fg
    if not HEX_RGB.match(cursor):
        raise SystemExit("--cursor-color must be #RRGGBB")

    lines = [
        "[/]",
        f"visible-name={dconf_quote(args.visible_name)}",
        "use-theme-colors=false",
        f"foreground-color={dconf_quote(fg16)}",
        f"background-color={dconf_quote(bg16)}",
        "bold-color-same-as-fg=true",
        f"bold-color={dconf_quote(fg16)}",
        f"cursor-color={dconf_quote(cursor.lower())}",
        f"palette={dconf_quote(pal16)}",
        "",
    ]

    sys.stdout.write("\n".join(lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

