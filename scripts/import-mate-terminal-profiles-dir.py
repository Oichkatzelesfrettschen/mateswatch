#!/usr/bin/env python3
import argparse
import os
import random
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


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Import a directory of MATE Terminal *.dconf profile snippets into dconf."
    )
    parser.add_argument(
        "dir",
        help="Directory containing *.dconf files (profile id inferred from filename)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="Limit number of profiles imported (0 = all)",
    )
    parser.add_argument(
        "--add-to-profile-list",
        action="store_true",
        help="Append imported profile IDs to profile-list",
    )
    parser.add_argument(
        "--smoke-count",
        type=int,
        default=0,
        help="Launch mate-terminal briefly for N profiles (0 = skip)",
    )
    parser.add_argument(
        "--smoke-timeout",
        type=int,
        default=4,
        help="Seconds before killing a smoke mate-terminal run",
    )
    args = parser.parse_args()

    if os.environ.get("DISPLAY", "") == "" and args.smoke_count:
        sys.stderr.write("warning: DISPLAY is not set; smoke tests likely cannot run\n")

    root = Path(args.dir)
    if not root.is_dir():
        sys.stderr.write(f"error: {root} is not a directory\n")
        return 2

    files = sorted(p for p in root.glob("*.dconf") if p.name != "manifest.json")
    if args.limit and args.limit > 0:
        files = files[: args.limit]

    imported_ids: list[str] = []
    for file in files:
        profile_id = file.stem
        text = file.read_text(encoding="utf-8")
        proc = run(
            ["dconf", "load", f"/org/mate/terminal/profiles/{profile_id}/"],
            stdin_text=text,
        )
        if proc.returncode != 0:
            sys.stderr.write(
                f"{profile_id}: dconf load failed: {proc.stderr.strip() or proc.stdout.strip()}\n"
            )
            return 1
        imported_ids.append(profile_id)

    if args.add_to_profile_list:
        current = gsettings_get_profile_list()
        merged = list(current)
        existing = set(current)
        for profile_id in imported_ids:
            if profile_id not in existing:
                merged.append(profile_id)
                existing.add(profile_id)
        gsettings_set_profile_list(merged)

    if args.smoke_count:
        if shutil_which("mate-terminal") is None:
            sys.stderr.write("warning: mate-terminal not found; skipping smoke tests\n")
        else:
            sample = imported_ids[:]
            random.shuffle(sample)
            sample = sample[: args.smoke_count]
            restore_profile_list = None
            if not args.add_to_profile_list:
                restore_profile_list = gsettings_get_profile_list()
                merged = list(restore_profile_list)
                existing = set(restore_profile_list)
                for profile_id in sample:
                    if profile_id not in existing:
                        merged.append(profile_id)
                        existing.add(profile_id)
                gsettings_set_profile_list(merged)

            try:
                for profile_id in sample:
                    visible_proc = run(
                        [
                            "dconf",
                            "read",
                            f"/org/mate/terminal/profiles/{profile_id}/visible-name",
                        ]
                    )
                    visible = profile_id
                    if visible_proc.returncode == 0:
                        v = visible_proc.stdout.strip()
                        if v.startswith("'") and v.endswith("'"):
                            visible = v[1:-1]

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
                        sys.stderr.write(
                            f"{profile_id}: mate-terminal did not find profile (visible-name: {visible})\n"
                        )
                        return 1
                    if proc.returncode not in (0, 124):
                        sys.stderr.write(
                            f"{profile_id}: mate-terminal smoke failed ({proc.returncode}): {proc.stderr.strip() or proc.stdout.strip()}\n"
                        )
            finally:
                if restore_profile_list is not None:
                    gsettings_set_profile_list(restore_profile_list)

    print(f"Imported {len(imported_ids)} profiles from {root}")
    if args.add_to_profile_list:
        print("Updated org.mate.terminal.global profile-list")
    return 0


def shutil_which(cmd: str) -> str | None:
    for p in os.environ.get("PATH", "").split(os.pathsep):
        candidate = Path(p) / cmd
        if candidate.is_file() and os.access(candidate, os.X_OK):
            return str(candidate)
    return None


if __name__ == "__main__":
    raise SystemExit(main())
