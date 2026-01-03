#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from pathlib import Path


def run(
    cmd: list[str], *, stdin_text: str | None = None
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        check=False,
        text=True,
        input=stdin_text,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def dconf_quote(value: str) -> str:
    return "'" + value.replace("\\", "\\\\").replace("'", "\\'") + "'"


def which(cmd: str) -> bool:
    for p in os.environ.get("PATH", "").split(os.pathsep):
        candidate = Path(p) / cmd
        if candidate.is_file() and os.access(candidate, os.X_OK):
            return True
    return False


def candidate_scheme_roots() -> list[Path]:
    roots: list[Path] = []
    env = os.environ.get("MATESWATCH_SCHEMES_DIR")
    if env:
        roots.append(Path(env))
    # repo layout
    roots.append(Path(__file__).resolve().parents[1] / "mate-terminal" / "schemes")
    # potential installed layouts
    roots.append(Path("/usr/share/mateswatch/mate-terminal/schemes"))
    roots.append(Path("/usr/share/mate-terminal/profiles/mateswatch"))
    roots.append(Path("/usr/share/mate-terminal/profiles"))
    return roots


def find_profile_file(profile_id: str, roots: list[Path]) -> Path | None:
    target = f"{profile_id}.dconf"
    for root in roots:
        if not root.is_dir():
            continue
        p = root / target
        if p.is_file():
            return p
        for cand in root.rglob(target):
            if cand.is_file():
                return cand
    return None


def list_profiles(roots: list[Path]) -> list[str]:
    seen: set[str] = set()
    ids: list[str] = []
    for root in roots:
        if not root.is_dir():
            continue
        for f in root.rglob("*.dconf"):
            if f.name == "manifest.json":
                continue
            pid = f.stem
            if pid in seen:
                continue
            seen.add(pid)
            ids.append(pid)
    return sorted(ids)


def gsettings_get_profile_list() -> list[str]:
    proc = run(["gsettings", "get", "org.mate.terminal.global", "profile-list"])
    if proc.returncode != 0:
        raise RuntimeError(
            proc.stderr.strip()
            or proc.stdout.strip()
            or "gsettings get profile-list failed"
        )
    return re.findall(r"'([^']+)'", proc.stdout.strip())


def gsettings_set_profile_list(profile_ids: list[str]) -> None:
    serialized = "[" + ", ".join(dconf_quote(x) for x in profile_ids) + "]"
    proc = run(
        ["gsettings", "set", "org.mate.terminal.global", "profile-list", serialized]
    )
    if proc.returncode != 0:
        raise RuntimeError(
            proc.stderr.strip()
            or proc.stdout.strip()
            or "gsettings set profile-list failed"
        )


def import_profile(profile_id: str, scheme_file: Path) -> None:
    text = scheme_file.read_text(encoding="utf-8")
    proc = run(
        ["dconf", "load", f"/org/mate/terminal/profiles/{profile_id}/"], stdin_text=text
    )
    if proc.returncode != 0:
        raise RuntimeError(
            proc.stderr.strip() or proc.stdout.strip() or "dconf load failed"
        )


def snippet_to_full_dconf(profile_id: str, snippet_text: str) -> str:
    # Convert a mateswatch "snippet" (usually with section [/] and key/value pairs)
    # into a portable dconf dump that can be loaded at root (dconf load / < file).
    lines: list[str] = [f"[/org/mate/terminal/profiles/{profile_id}/]"]
    for raw in snippet_text.splitlines():
        line = raw.strip()
        if not line:
            continue
        if line.startswith("[") and line.endswith("]"):
            continue
        lines.append(line)
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Import mateswatch MATE Terminal profile snippets into your dconf (user session)."
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_list = sub.add_parser("list", help="List available profile IDs")
    p_list.add_argument("--contains", default="", help="Filter IDs by substring")

    p_path = sub.add_parser(
        "path", help="Show the on-disk .dconf file path for a profile ID"
    )
    p_path.add_argument("profile_id")

    p_import = sub.add_parser("import", help="Import a profile into dconf")
    p_import.add_argument("profile_id")
    p_import.add_argument(
        "--add-to-profile-list",
        action="store_true",
        help="Append profile id to profile-list",
    )
    p_import.add_argument(
        "--set-default", action="store_true", help="Set default-profile to this id"
    )

    p_export = sub.add_parser(
        "export",
        help="Export a profile as a standalone dconf dump (for manual download/import)",
    )
    p_export.add_argument("profile_id")
    p_export.add_argument(
        "--format",
        choices=("snippet", "full"),
        default="full",
        help="Export format: 'snippet' (repo file) or 'full' (dconf dump at /)",
    )
    p_export.add_argument(
        "--out",
        default="-",
        help="Output path (default stdout). Use '-' for stdout.",
    )

    p_export_all = sub.add_parser(
        "export-all",
        help="Export all profiles as standalone dconf dumps into a directory",
    )
    p_export_all.add_argument(
        "--format",
        choices=("snippet", "full"),
        default="full",
        help="Export format: 'snippet' (repo file) or 'full' (dconf dump at /)",
    )
    p_export_all.add_argument("outdir", help="Directory to write <id>.dconf files into")

    args = parser.parse_args()

    roots = candidate_scheme_roots()
    roots = [p for p in roots if p.exists()]

    if args.cmd == "list":
        ids = list_profiles(roots)
        if args.contains:
            want = args.contains.lower()
            ids = [x for x in ids if want in x.lower()]
        try:
            for pid in ids:
                print(pid)
        except BrokenPipeError:
            return 0
        return 0

    if args.cmd == "path":
        p = find_profile_file(args.profile_id, roots)
        if p is None:
            sys.stderr.write(f"not found: {args.profile_id}.dconf\n")
            return 2
        print(str(p))
        return 0

    if args.cmd == "export":
        scheme_path = find_profile_file(args.profile_id, roots)
        if scheme_path is None:
            sys.stderr.write(f"not found: {args.profile_id}.dconf\n")
            return 2

        text = scheme_path.read_text(encoding="utf-8", errors="replace")
        if args.format == "full":
            text = snippet_to_full_dconf(args.profile_id, text)

        if args.out == "-":
            sys.stdout.write(text)
            return 0

        Path(args.out).write_text(text, encoding="utf-8")
        return 0

    if args.cmd == "export-all":
        outdir = Path(args.outdir)
        outdir.mkdir(parents=True, exist_ok=True)
        ids = list_profiles(roots)
        for profile_id in ids:
            scheme_path = find_profile_file(profile_id, roots)
            if scheme_path is None:
                continue
            text = scheme_path.read_text(encoding="utf-8", errors="replace")
            if args.format == "full":
                text = snippet_to_full_dconf(profile_id, text)
            (outdir / f"{profile_id}.dconf").write_text(text, encoding="utf-8")

        (outdir / "README.txt").write_text(
            "mateswatch standalone exports\n\n"
            "These files are portable dconf dumps for MATE Terminal profiles.\n\n"
            "Import one profile (creates/updates that profile id):\n\n"
            "  dconf load / < <profile-id>.dconf\n\n"
            "To make it appear in MATE Terminal's profile dropdown, add the id to:\n\n"
            "  gsettings get org.mate.terminal.global profile-list\n"
            '  gsettings set org.mate.terminal.global profile-list "[...]"\n\n'
            "Or, if mateswatch is installed:\n\n"
            "  mateswatch import <profile-id> --add-to-profile-list --set-default\n",
            encoding="utf-8",
        )
        return 0

    if args.cmd == "import":
        if not which("dconf") or not which("gsettings"):
            sys.stderr.write("error: need dconf and gsettings on PATH\n")
            return 1

        p = find_profile_file(args.profile_id, roots)
        if p is None:
            sys.stderr.write(f"not found: {args.profile_id}.dconf\n")
            return 2

        import_profile(args.profile_id, p)

        if args.add_to_profile_list or args.set_default:
            current = gsettings_get_profile_list()
            if args.profile_id not in current:
                gsettings_set_profile_list(current + [args.profile_id])

        if args.set_default:
            proc = run(
                [
                    "gsettings",
                    "set",
                    "org.mate.terminal.global",
                    "default-profile",
                    dconf_quote(args.profile_id),
                ]
            )
            if proc.returncode != 0:
                sys.stderr.write(
                    proc.stderr.strip()
                    or proc.stdout.strip()
                    or "gsettings set default-profile failed"
                )
                return 1

        sys.stdout.write(f"Imported profile id '{args.profile_id}'.\n")
        return 0

    return 2


if __name__ == "__main__":
    raise SystemExit(main())
