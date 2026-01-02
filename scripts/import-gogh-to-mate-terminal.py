#!/usr/bin/env python3
import argparse
import json
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

import yaml

from theme_common import color_to_rgb16, color_to_rgb8, dconf_quote, fingerprint, format_visible_name, slugify


@dataclass(frozen=True)
class GoghTheme:
    name: str
    author: str
    variant: str
    background: str
    foreground: str
    cursor: str
    palette: list[str]  # 16 items, #RRGGBB


def run(cmd: list[str], *, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        check=False,
        text=True,
        cwd=str(cwd) if cwd else None,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def load_theme(path: Path) -> GoghTheme:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path}: expected YAML mapping")

    name = str(data.get("name") or path.stem)
    author = str(data.get("author") or "").strip()
    variant = str(data.get("variant") or "").strip()
    background = str(data.get("background") or "").strip()
    foreground = str(data.get("foreground") or "").strip()
    cursor = str(data.get("cursor") or foreground or "").strip()

    # Validate formats by normalizing to rgb8.
    background = color_to_rgb8(background)
    foreground = color_to_rgb8(foreground)
    cursor = color_to_rgb8(cursor)

    palette = []
    for i in range(1, 17):
        key = f"color_{i:02d}"
        value = str(data.get(key) or "").strip()
        palette.append(color_to_rgb8(value))

    return GoghTheme(
        name=name,
        author=author,
        variant=variant,
        background=background,
        foreground=foreground,
        cursor=cursor,
        palette=palette,
    )


def generate_mate_profile_dconf(profile_id: str, visible_name: str, theme: GoghTheme) -> str:
    # Keep Gogh's explicit cursor color (some schemes use non-fg cursors).
    lines = [
        "[/]",
        f"visible-name={dconf_quote(visible_name)}",
        "use-theme-colors=false",
        f"foreground-color={dconf_quote(color_to_rgb16(theme.foreground))}",
        f"background-color={dconf_quote(color_to_rgb16(theme.background))}",
        "bold-color-same-as-fg=true",
        f"bold-color={dconf_quote(color_to_rgb16(theme.foreground))}",
        f"cursor-color={dconf_quote(color_to_rgb8(theme.cursor))}",
        f"palette={dconf_quote(':'.join(color_to_rgb16(c) for c in theme.palette))}",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Import Gogh YAML themes as MATE Terminal dconf profile snippets.")
    parser.add_argument("--gogh-dir", default="/tmp/gogh", help="Path to a cloned Gogh-Co/Gogh repository")
    parser.add_argument("--output-dir", default="mate-terminal/schemes/gogh", help="Output directory for generated *.dconf")
    parser.add_argument("--prefix", default="gogh-", help="Profile ID prefix")
    parser.add_argument("--limit", type=int, default=0, help="Limit number of themes (0 = all)")
    args = parser.parse_args()

    gogh_dir = Path(args.gogh_dir)
    themes_dir = gogh_dir / "themes"
    if not themes_dir.is_dir():
        sys.stderr.write(f"error: {themes_dir} not found (clone Gogh-Co/Gogh first)\n")
        return 2

    proc = run(["git", "rev-parse", "HEAD"], cwd=gogh_dir)
    gogh_rev = proc.stdout.strip() if proc.returncode == 0 else ""

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    theme_files = sorted(themes_dir.glob("*.yml"))
    if args.limit and args.limit > 0:
        theme_files = theme_files[: args.limit]

    manifest = {
        "source": {
            "repo": "https://github.com/Gogh-Co/Gogh",
            "rev": gogh_rev,
        },
        "count": 0,
        "themes": [],
    }

    for theme_file in theme_files:
        theme = load_theme(theme_file)
        stem = theme_file.stem
        profile_id = f"{args.prefix}{slugify(stem)}"
        label = theme.name
        if theme.variant:
            label = f"{label} ({theme.variant})"
        visible_name = format_visible_name("GOG", label, theme.background, theme.foreground, theme.palette)

        out_path = output_dir / f"{profile_id}.dconf"
        out_path.write_text(generate_mate_profile_dconf(profile_id, visible_name, theme), encoding="utf-8")

        fp = fingerprint(theme.background, theme.foreground, theme.palette)
        manifest["themes"].append(
            {
                "file": theme_file.name,
                "name": theme.name,
                "variant": theme.variant,
                "author": theme.author,
                "profile_id": profile_id,
                "visible_name": visible_name,
                "fingerprint": fp,
                "output": str(out_path),
            }
        )

    manifest["count"] = len(manifest["themes"])
    (output_dir / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    print(f"Generated {manifest['count']} MATE Terminal profiles in {output_dir}")
    if gogh_rev:
        print(f"Source: Gogh-Co/Gogh@{gogh_rev}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
