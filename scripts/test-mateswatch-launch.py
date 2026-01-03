#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import os
import random
import re
import subprocess
import sys
import tempfile
from pathlib import Path

from theme_common import dconf_quote


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


def reset_profile(profile_id: str) -> None:
    run(["dconf", "reset", "-f", f"/org/mate/terminal/profiles/{profile_id}/"])


def stable_bucket(value: str, *, buckets: int) -> int:
    h = hashlib.sha1(value.encode("utf-8")).hexdigest()
    return int(h[:8], 16) % buckets


def sh_quote(s: str) -> str:
    return "'" + s.replace("\\", "\\\\").replace("'", "'\\''") + "'"


def xvfb_launch_smoke(*, profile_name: str, log_dir: Path) -> tuple[bool, str]:
    """
    Launch mate-terminal under xvfb with the given profile name.
    We consider it a success if:
      - the child writes a ready file (i.e. it actually executed in the terminal)
      - the terminal did not exit before ready
    """
    with tempfile.NamedTemporaryFile("w", delete=False, suffix=".sh") as f:
        f.write(
            r"""
set -euo pipefail
if [[ -n "${MATESWATCH_READY_FILE:-}" ]]; then
  printf 'ready\n' >"${MATESWATCH_READY_FILE}" 2>/dev/null || true
fi
sleep 0.2
"""
        )
        script_path = f.name
    os.chmod(script_path, 0o755)

    title = f"MSW-LAUNCH-{os.getpid()}"
    ready_file = f"/tmp/mateswatch-ready-{os.getpid()}-{os.path.basename(script_path)}"
    cmd_str = f"env MATESWATCH_READY_FILE={ready_file} bash {script_path}"
    logf = log_dir / f"{title}.log"

    try:
        bash_script = f"""
          set -euo pipefail
          rm -f {sh_quote(ready_file)} || true
          timeout 6 mate-terminal --disable-factory --hide-menubar --geometry=120x40 -t {sh_quote(title)} --profile {sh_quote(profile_name)} --command {sh_quote(cmd_str)} >{sh_quote(str(logf))} 2>&1 &
          pid=$!
          for _ in $(seq 1 40); do
            [[ -f {sh_quote(ready_file)} ]] && break
            if ! kill -0 $pid >/dev/null 2>&1; then
              echo "mate-terminal exited before ready" >&2
              break
            fi
            sleep 0.05
          done
          if [[ ! -f {sh_quote(ready_file)} ]]; then
            echo "ready file not created: {ready_file}" >&2
            echo "---- mate-terminal log ----" >&2
            tail -n 200 {sh_quote(str(logf))} >&2 || true
            exit 3
          fi
          rm -f {sh_quote(ready_file)} || true
          kill $pid >/dev/null 2>&1 || true
          wait $pid >/dev/null 2>&1 || true
        """
        proc = run(
            [
                "xvfb-run",
                "-a",
                "-s",
                "-screen 0 900x600x24",
                "bash",
                "-lc",
                bash_script,
            ]
        )
        if proc.returncode == 0:
            return True, ""
        return False, proc.stdout.strip()
    finally:
        try:
            os.unlink(script_path)
        except OSError:
            pass


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Headless launch/crash test: import each mateswatch scheme and launch mate-terminal under Xvfb."
    )
    parser.add_argument(
        "--schemes-dir",
        default="mate-terminal/schemes",
        help="Root directory containing *.dconf",
    )
    parser.add_argument("--all", action="store_true", help="Test all schemes (slow)")
    parser.add_argument(
        "--count", type=int, default=50, help="Sample size when not using --all"
    )
    parser.add_argument("--seed", type=int, default=1, help="Random seed for sampling")
    parser.add_argument("--shards", type=int, default=1, help="Total shard count")
    parser.add_argument(
        "--shard-index", type=int, default=0, help="Shard index (0..shards-1)"
    )
    args = parser.parse_args()

    if args.shards < 1 or not (0 <= args.shard_index < args.shards):
        raise SystemExit("error: invalid --shards/--shard-index")

    for cmd in ("xvfb-run", "mate-terminal", "bash", "timeout", "dconf", "gsettings"):
        require_cmd(cmd)

    root = Path(args.schemes_dir)
    files = sorted(p for p in root.rglob("*.dconf") if p.is_file())
    if not files:
        print(f"error: no .dconf files found under {root}", file=sys.stderr)
        return 2

    # Shard by stable hash of relative path.
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

    orig_list = gsettings_get_profile_list()
    log_dir = Path("generated/ci")
    log_dir.mkdir(parents=True, exist_ok=True)

    failures: list[str] = []
    tested = 0

    try:
        for i, scheme_path in enumerate(files, start=1):
            tested += 1
            scheme_text = scheme_path.read_text(encoding="utf-8", errors="replace")
            kv = read_kv(scheme_text)
            visible = unquote(kv.get("visible-name", scheme_path.stem))

            test_id = f"msw-ltest-{args.shard_index:02d}-{i:04d}"
            test_visible = f"MSW LAUNCH {visible}"
            test_text = with_visible_name(scheme_text, test_visible)

            proc = run(
                ["dconf", "load", f"/org/mate/terminal/profiles/{test_id}/"],
                stdin_text=test_text,
            )
            if proc.returncode != 0:
                failures.append(
                    f"{scheme_path}: dconf load failed: {proc.stdout.strip()}"
                )
                reset_profile(test_id)
                continue

            # Ensure mate-terminal can resolve the profile (it reads from profile-list).
            gsettings_set_profile_list(
                orig_list + ([test_id] if test_id not in orig_list else [])
            )

            ok, msg = xvfb_launch_smoke(profile_name=test_visible, log_dir=log_dir)
            if not ok:
                failures.append(f"{scheme_path}: mate-terminal launch failed: {msg}")
            else:
                # remove log for passing themes to keep CI artifacts small
                for lf in log_dir.glob("MSW-LAUNCH-*.log"):
                    lf.unlink(missing_ok=True)

            reset_profile(test_id)

    finally:
        try:
            gsettings_set_profile_list(orig_list)
        except Exception:
            pass

    if failures:
        print(f"FAIL: {len(failures)}/{tested} issues", file=sys.stderr)
        for f in failures[:50]:
            print(f"- {f}", file=sys.stderr)
        if len(failures) > 50:
            print(f"... and {len(failures) - 50} more", file=sys.stderr)
        print("(logs in generated/ci/ for failures)", file=sys.stderr)
        return 1

    print(
        f"OK: launch-verified {tested} scheme(s) (shard {args.shard_index}/{args.shards})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
