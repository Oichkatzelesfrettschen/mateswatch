#!/usr/bin/env python3
from __future__ import annotations

import argparse
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
        stderr=subprocess.STDOUT,
    )


def require_cmd(name: str) -> None:
    if run(["bash", "-lc", f"command -v {name} >/dev/null 2>&1"]).returncode != 0:
        raise SystemExit(f"error: required command not found on PATH: {name}")


def dconf_quote(value: str) -> str:
    return "'" + value.replace("\\", "\\\\").replace("'", "\\'") + "'"


def unquote(s: str) -> str:
    if len(s) >= 2 and s[0] == "'" and s[-1] == "'":
        return s[1:-1]
    return s


def read_visible_name(dconf_text: str) -> str | None:
    for line in dconf_text.splitlines():
        if line.startswith("visible-name="):
            return unquote(line.split("=", 1)[1].strip())
    return None


def with_visible_name(dconf_text: str, visible_name: str) -> str:
    out = []
    replaced = False
    for line in dconf_text.splitlines():
        if line.startswith("visible-name="):
            out.append(f"visible-name={dconf_quote(visible_name)}")
            replaced = True
        else:
            out.append(line)
    if not replaced:
        out.insert(1, f"visible-name={dconf_quote(visible_name)}")
    return "\n".join(out) + "\n"


def gsettings_get_profile_list() -> list[str]:
    proc = run(["gsettings", "get", "org.mate.terminal.global", "profile-list"])
    if proc.returncode != 0:
        raise RuntimeError(proc.stdout.strip() or "gsettings get profile-list failed")
    return re.findall(r"'([^']+)'", proc.stdout.strip())


def gsettings_set_profile_list(profile_ids: list[str]) -> None:
    serialized = "[" + ", ".join(dconf_quote(x) for x in profile_ids) + "]"
    proc = run(
        ["gsettings", "set", "org.mate.terminal.global", "profile-list", serialized]
    )
    if proc.returncode != 0:
        raise RuntimeError(proc.stdout.strip() or "gsettings set profile-list failed")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Live-launch test for mateswatch schemes (desktop required)."
    )
    parser.add_argument(
        "--schemes-dir",
        default="mate-terminal/schemes",
        help="Root directory containing *.dconf",
    )
    parser.add_argument("--all", action="store_true", help="Test all schemes (slow)")
    parser.add_argument(
        "--count", type=int, default=30, help="Sample size when not using --all"
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=0,
        help="Random seed for sampling (0 = deterministic)",
    )
    args = parser.parse_args()

    for cmd in ("dconf", "gsettings", "mate-terminal", "timeout"):
        require_cmd(cmd)

    root = Path(args.schemes_dir)
    files = sorted(p for p in root.rglob("*.dconf") if p.is_file())
    if not files:
        print(f"error: no .dconf files found under {root}", file=sys.stderr)
        return 2

    if not args.all:
        rng = random.Random(args.seed)
        files = rng.sample(files, k=min(args.count, len(files)))

    orig_list = gsettings_get_profile_list()

    failures: list[str] = []
    try:
        for i, path in enumerate(files, start=1):
            dconf_text = path.read_text(encoding="utf-8", errors="replace")
            orig_visible = read_visible_name(dconf_text) or path.stem
            test_visible = f"MSW TEST {orig_visible}"
            test_id = f"msw-test-{i:04d}"

            test_text = with_visible_name(dconf_text, test_visible)

            # Import into a temporary profile id.
            proc = run(
                ["dconf", "load", f"/org/mate/terminal/profiles/{test_id}/"],
                stdin_text=test_text,
            )
            if proc.returncode != 0:
                failures.append(f"{path}: dconf load failed: {proc.stdout.strip()}")
                continue

            # Keep profile-list small: original + this one id only.
            gsettings_set_profile_list(
                orig_list + ([test_id] if test_id not in orig_list else [])
            )

            out = run(
                [
                    "timeout",
                    "4",
                    "mate-terminal",
                    "--disable-factory",
                    f"--profile={test_visible}",
                    "--command",
                    "true",
                ]
            )
            if "No such profile" in out.stdout:
                failures.append(
                    f"{path}: mate-terminal says 'No such profile' for visible-name {test_visible!r}"
                )
            elif out.returncode not in (0, 124):  # 124 is timeout
                failures.append(
                    f"{path}: mate-terminal non-zero exit {out.returncode}: {out.stdout.strip()}"
                )

            # Cleanup temp profile data.
            run(["dconf", "reset", "-f", f"/org/mate/terminal/profiles/{test_id}/"])

    finally:
        try:
            gsettings_set_profile_list(orig_list)
        except Exception:
            pass

    if failures:
        print("FAIL:", file=sys.stderr)
        for f in failures[:50]:
            print(f"- {f}", file=sys.stderr)
        if len(failures) > 50:
            print(f"... and {len(failures) - 50} more", file=sys.stderr)
        return 1

    print(f"OK: tested {len(files)} scheme(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
