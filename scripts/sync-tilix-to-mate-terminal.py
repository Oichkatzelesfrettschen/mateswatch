#!/usr/bin/env python3
import argparse
import hashlib
import json
import os
import random
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


HEX_RGB8 = re.compile(r"^#[0-9a-fA-F]{6}$")
HEX_RGB16 = re.compile(r"^#[0-9a-fA-F]{12}$")
SAFE_ID = re.compile(r"[^a-z0-9._+-]+")


@dataclass(frozen=True)
class TilixScheme:
    source_path: Path
    origin: str  # "system" or "user"
    filename: str
    name: str
    use_theme_colors: bool
    foreground: str
    background: str
    palette: list[str]


def run(cmd: list[str], *, stdin_text: str | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        check=False,
        text=True,
        input=stdin_text,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def which(cmd: str) -> str | None:
    for p in os.environ.get("PATH", "").split(os.pathsep):
        candidate = Path(p) / cmd
        if candidate.is_file() and os.access(candidate, os.X_OK):
            return str(candidate)
    return None


def require_hex_rgb(value: str, what: str) -> None:
    if not (HEX_RGB8.match(value) or HEX_RGB16.match(value)):
        raise ValueError(f"{what}: expected #RRGGBB or #RRRRGGGGBBBB, got {value!r}")


def color_to_rgb16(color: str) -> str:
    require_hex_rgb(color, "color")
    if HEX_RGB16.match(color):
        return color.upper()
    r = color[1:3]
    g = color[3:5]
    b = color[5:7]
    return f"#{r}{r}{g}{g}{b}{b}".upper()


def color_to_rgb8(color: str) -> str:
    require_hex_rgb(color, "color")
    if HEX_RGB8.match(color):
        return color.lower()
    # #RRRRGGGGBBBB -> take the high byte from each 16-bit channel
    r = color[1:5]
    g = color[5:9]
    b = color[9:13]
    return f"#{r[:2]}{g[:2]}{b[:2]}".lower()


def dconf_quote(value: str) -> str:
    return "'" + value.replace("\\", "\\\\").replace("'", "\\'") + "'"


def normalize_profile_id(prefix: str, filename: str) -> str:
    stem = filename[:-5] if filename.lower().endswith(".json") else filename
    stem = stem.lower()
    stem = SAFE_ID.sub("-", stem).strip("-")
    if not stem:
        stem = "unnamed"
    return f"{prefix}{stem}"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_tilix_scheme(origin: str, path: Path) -> TilixScheme:
    data = json.loads(path.read_text(encoding="utf-8"))
    name = str(data.get("name") or path.stem)
    use_theme_colors = bool(data.get("use-theme-colors", False))
    fg = data.get("foreground-color")
    bg = data.get("background-color")
    palette = data.get("palette")
    if palette is None:
        raise ValueError(f"{path}: missing required key palette")
    if (fg is None or bg is None) and not use_theme_colors:
        raise ValueError(
            f"{path}: missing foreground/background with use-theme-colors=false "
            "(need foreground-color and background-color)"
        )
    if not isinstance(palette, list) or len(palette) != 16:
        raise ValueError(f"{path}: palette must be an array of 16 colors")
    if fg is None:
        fg = "#ffffff"
    if bg is None:
        bg = "#000000"
    require_hex_rgb(fg, f"{path} foreground-color")
    require_hex_rgb(bg, f"{path} background-color")
    for i, c in enumerate(palette):
        require_hex_rgb(c, f"{path} palette[{i}]")
    return TilixScheme(
        source_path=path,
        origin=origin,
        filename=path.name,
        name=name,
        use_theme_colors=use_theme_colors,
        foreground=fg,
        background=bg,
        palette=list(palette),
    )


def iter_tilix_scheme_files() -> list[tuple[str, Path]]:
    items: list[tuple[str, Path]] = []
    user_dir = Path.home() / ".config" / "tilix" / "schemes"
    system_dir = Path("/usr/share/tilix/schemes")

    if user_dir.is_dir():
        items.extend([("user", p) for p in sorted(user_dir.glob("*.json"))])
    if system_dir.is_dir():
        items.extend([("system", p) for p in sorted(system_dir.glob("*.json"))])
    return items


def generate_mate_profile_dconf(profile_id: str, visible_name: str, scheme: TilixScheme) -> str:
    palette16 = ":".join(color_to_rgb16(c) for c in scheme.palette)
    use_theme_colors = "true" if scheme.use_theme_colors else "false"

    lines = [
        "[/]",
        f"visible-name={dconf_quote(visible_name)}",
        f"use-theme-colors={use_theme_colors}",
    ]

    if not scheme.use_theme_colors:
        fg16 = color_to_rgb16(scheme.foreground)
        bg16 = color_to_rgb16(scheme.background)
        cursor = color_to_rgb8(scheme.foreground)
        lines.extend(
            [
                f"foreground-color={dconf_quote(fg16)}",
                f"background-color={dconf_quote(bg16)}",
                "bold-color-same-as-fg=true",
                f"bold-color={dconf_quote(fg16)}",
                f"cursor-color={dconf_quote(cursor)}",
            ]
        )

    lines.extend(
        [
        f"palette={dconf_quote(palette16)}",
        "",
        ]
    )
    return "\n".join(lines)


def dconf_dump_profile(profile_id: str) -> str:
    proc = run(["dconf", "dump", f"/org/mate/terminal/profiles/{profile_id}/"])
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or proc.stdout.strip() or "dconf dump failed")
    return proc.stdout


def validate_dump(dump: str, expected: dict[str, str]) -> list[str]:
    errors: list[str] = []
    for key, want in expected.items():
        m = re.search(rf"^{re.escape(key)}=(.+)$", dump, flags=re.MULTILINE)
        if not m:
            errors.append(f"missing key {key}")
            continue
        got = m.group(1).strip()
        if got != want:
            errors.append(f"{key}: got {got} want {want}")
    return errors


def gsettings_get_profile_list() -> list[str]:
    proc = run(["gsettings", "get", "org.mate.terminal.global", "profile-list"])
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or proc.stdout.strip() or "gsettings get profile-list failed")
    return re.findall(r"'([^']+)'", proc.stdout.strip())


def gsettings_set_profile_list(profile_ids: list[str]) -> None:
    serialized = "[" + ", ".join(dconf_quote(x) for x in profile_ids) + "]"
    proc = run(["gsettings", "set", "org.mate.terminal.global", "profile-list", serialized])
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or proc.stdout.strip() or "gsettings set profile-list failed")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Cleanroom conversion: generate MATE Terminal profiles from installed Tilix scheme JSON files."
    )
    parser.add_argument("--output-dir", default="generated/mate-terminal/tilix", help="Where to write generated files")
    parser.add_argument("--system-prefix", default="tilix-", help="Profile ID prefix for system schemes")
    parser.add_argument("--user-prefix", default="tilix-user-", help="Profile ID prefix for user schemes")
    parser.add_argument("--limit", type=int, default=0, help="Limit number of schemes processed (0 = no limit)")
    parser.add_argument("--import", dest="do_import", action="store_true", help="Import generated profiles into dconf")
    parser.add_argument("--update-profile-list", action="store_true", help="Append generated profile IDs to profile-list")
    parser.add_argument("--smoke-count", type=int, default=0, help="Launch mate-terminal briefly for N profiles (0 = skip)")
    parser.add_argument("--smoke-timeout", type=int, default=5, help="Seconds before killing a smoke mate-terminal run")
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    scheme_files = iter_tilix_scheme_files()
    if args.limit and args.limit > 0:
        scheme_files = scheme_files[: args.limit]

    schemes: list[tuple[str, TilixScheme]] = []
    for origin, path in scheme_files:
        schemes.append((origin, load_tilix_scheme(origin, path)))

    generated: list[dict[str, Any]] = []
    profile_ids: list[str] = []
    id_to_visible: dict[str, str] = {}

    for origin, scheme in schemes:
        prefix = args.user_prefix if origin == "user" else args.system_prefix
        profile_id = normalize_profile_id(prefix, scheme.filename)
        visible_name = f"Tilix ({origin}): {scheme.name}"

        dconf_text = generate_mate_profile_dconf(profile_id, visible_name, scheme)
        out_path = output_dir / f"{profile_id}.dconf"
        out_path.write_text(dconf_text, encoding="utf-8")

        generated.append(
            {
                "origin": origin,
                "source_path": str(scheme.source_path),
                "source_sha256": sha256_file(scheme.source_path),
                "profile_id": profile_id,
                "visible_name": visible_name,
                "output_path": str(out_path),
            }
        )
        profile_ids.append(profile_id)
        id_to_visible[profile_id] = visible_name

    (output_dir / "manifest.json").write_text(
        json.dumps({"count": len(generated), "entries": generated}, indent=2) + "\n",
        encoding="utf-8",
    )

    if args.do_import:
        if which("dconf") is None or which("gsettings") is None:
            sys.stderr.write("error: dconf and gsettings are required for --import\n")
            return 2

        for entry in generated:
            profile_id = entry["profile_id"]
            out_path = Path(entry["output_path"])
            proc = run(
                ["dconf", "load", f"/org/mate/terminal/profiles/{profile_id}/"],
                stdin_text=out_path.read_text(encoding="utf-8"),
            )
            if proc.returncode != 0:
                sys.stderr.write(f"{profile_id}: dconf load failed: {proc.stderr.strip() or proc.stdout.strip()}\n")
                return 1

        if args.update_profile_list:
            current = gsettings_get_profile_list()
            merged = list(current)
            existing = set(current)
            for profile_id in profile_ids:
                if profile_id not in existing:
                    merged.append(profile_id)
                    existing.add(profile_id)
            gsettings_set_profile_list(merged)

        failures = 0
        for origin, scheme in schemes:
            prefix = args.user_prefix if origin == "user" else args.system_prefix
            profile_id = normalize_profile_id(prefix, scheme.filename)
            dump = dconf_dump_profile(profile_id)

            expected = {
                "use-theme-colors": "true" if scheme.use_theme_colors else "false",
                "palette": dconf_quote(":".join(color_to_rgb16(c) for c in scheme.palette)),
            }
            if not scheme.use_theme_colors:
                expected.update(
                    {
                        "foreground-color": dconf_quote(color_to_rgb16(scheme.foreground)),
                        "background-color": dconf_quote(color_to_rgb16(scheme.background)),
                        "bold-color-same-as-fg": "true",
                        "bold-color": dconf_quote(color_to_rgb16(scheme.foreground)),
                        "cursor-color": dconf_quote(color_to_rgb8(scheme.foreground)),
                    }
                )
            errs = validate_dump(dump, expected)
            if errs:
                failures += 1
                sys.stderr.write(f"{profile_id}:\n")
                for e in errs[:5]:
                    sys.stderr.write(f"  - {e}\n")

        if failures:
            sys.stderr.write(f"validation failures: {failures}\n")
            return 1

        if args.smoke_count and which("mate-terminal") is not None:
            smoke = profile_ids[:]
            random.shuffle(smoke)
            smoke = smoke[: args.smoke_count]

            # mate-terminal's --profile matches visible-name and it only knows profiles present in profile-list.
            # If we didn't persistently update the list, temporarily extend it for the smoke run.
            restore_profile_list = None
            if not args.update_profile_list:
                restore_profile_list = gsettings_get_profile_list()
                merged = list(restore_profile_list)
                existing = set(restore_profile_list)
                for pid in smoke:
                    if pid not in existing:
                        merged.append(pid)
                        existing.add(pid)
                gsettings_set_profile_list(merged)

            try:
                for profile_id in smoke:
                    visible = id_to_visible.get(profile_id, profile_id)
                    proc = run(
                        [
                            "timeout",
                            str(args.smoke_timeout),
                            "mate-terminal",
                            "--disable-factory",
                            f"--profile={visible}",
                            "--command",
                            "true",
                        ]
                    )
                    combined = (proc.stdout or "") + (proc.stderr or "")
                    if "No such profile" in combined:
                        sys.stderr.write(f"{profile_id}: mate-terminal did not find profile (visible-name: {visible})\n")
                        return 1
                    if proc.returncode not in (0, 124):  # 124=timeout(1)
                        sys.stderr.write(
                            f"{profile_id}: mate-terminal smoke failed ({proc.returncode}): {proc.stderr.strip() or proc.stdout.strip()}\n"
                        )
            finally:
                if restore_profile_list is not None:
                    gsettings_set_profile_list(restore_profile_list)

    print(f"Generated {len(generated)} profiles into {output_dir}")
    if args.do_import:
        print("Imported profiles into dconf under /org/mate/terminal/profiles/")
        if args.update_profile_list:
            print("Appended generated IDs to org.mate.terminal.global profile-list")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
