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
from dataclasses import dataclass
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


@dataclass(frozen=True)
class ParsedScheme:
    profile_id: str
    visible_name: str


def parse_scheme(path: Path) -> ParsedScheme:
    kv = read_kv(path.read_text(encoding="utf-8", errors="replace"))
    return ParsedScheme(
        profile_id=path.stem, visible_name=unquote(kv.get("visible-name", path.stem))
    )


def build_hello_assets(workdir: Path) -> tuple[Path, Path]:
    c_path = workdir / "hello.c"
    exe_path = workdir / "hello"
    c_path.write_text(
        "#include <stdio.h>\n"
        "\n"
        "int main(void) {\n"
        '    printf("Hello, world!\\n");\n'
        "    return 0;\n"
        "}\n",
        encoding="utf-8",
    )
    cc = (
        "gcc"
        if run(["bash", "-lc", "command -v gcc >/dev/null 2>&1"]).returncode == 0
        else "cc"
    )
    proc = run([cc, "-O2", "-Wall", "-Wextra", "-o", str(exe_path), str(c_path)])
    if proc.returncode != 0:
        raise RuntimeError(f"compile failed: {proc.stdout.strip()}")
    return c_path, exe_path


def make_terminal_script(*, hello_c: Path, hello_bin: Path) -> str:
    # Use 16-color Pygments formatter so ANSI colors map onto the theme palette.
    return f"""\
set -euo pipefail
export TERM=xterm-256color
printf '\\033[?25l\\033[H\\033[2J'
printf '\\033[1m$ gcc hello.c -o hello\\033[0m\\n\\n'
python3 - <<'PY'
from pygments import highlight
from pygments.lexers import CLexer
from pygments.formatters import TerminalFormatter
code = open({sh_quote(str(hello_c))}, 'r', encoding='utf-8').read()
print(highlight(code, CLexer(), TerminalFormatter(style='default')), end='')
PY
printf '\\n\\033[1m$ ./hello\\033[0m\\n'
{sh_quote(str(hello_bin))} || true
printf '\\n'
if [[ -n "${{MATESWATCH_READY_FILE:-}}" ]]; then
  printf 'ready\\n' >"${{MATESWATCH_READY_FILE}}" 2>/dev/null || true
fi
sleep 2.0
"""


def render_one(
    *,
    scheme_path: Path,
    out_path: Path,
    orig_profile_list: list[str],
    workdir: Path,
    keep_logs: bool,
) -> tuple[bool, str]:
    scheme_text = scheme_path.read_text(encoding="utf-8", errors="replace")
    scheme = parse_scheme(scheme_path)
    title = f"MSW-SHOW-{os.getpid()}-{scheme.profile_id}"
    ready_file = f"/tmp/mateswatch-ready-{os.getpid()}-{scheme.profile_id}"

    test_profile_id = f"msw-show-{scheme.profile_id}"
    test_visible = f"MSW SHOW {scheme.visible_name}"
    test_text = with_visible_name(scheme_text, test_visible)

    proc = run(
        ["dconf", "load", f"/org/mate/terminal/profiles/{test_profile_id}/"],
        stdin_text=test_text,
    )
    if proc.returncode != 0:
        reset_profile(test_profile_id)
        return False, f"dconf load failed: {proc.stdout.strip()}"

    # mate-terminal resolves profiles through profile-list.
    gsettings_set_profile_list(
        orig_profile_list
        + ([test_profile_id] if test_profile_id not in orig_profile_list else [])
    )

    hello_c, hello_bin = build_hello_assets(workdir)
    term_script = make_terminal_script(hello_c=hello_c, hello_bin=hello_bin)
    term_script_path = workdir / "run-in-terminal.sh"
    term_script_path.write_text(term_script, encoding="utf-8")
    term_script_path.chmod(0o755)

    log_dir = Path("generated/showcase/logs")
    log_dir.mkdir(parents=True, exist_ok=True)
    logf = log_dir / f"{scheme.profile_id}.log"

    try:
        bash = f"""
          set -euo pipefail
          rm -f {sh_quote(ready_file)} || true
          cmd_str="env MATESWATCH_READY_FILE={sh_quote(ready_file)} bash {sh_quote(str(term_script_path))}"
          timeout 10 mate-terminal --disable-factory --hide-menubar --geometry=120x40 -t {sh_quote(title)} --profile {sh_quote(test_visible)} --command "$cmd_str" >{sh_quote(str(logf))} 2>&1 &
          pid=$!
          for _ in $(seq 1 80); do
            [[ -f {sh_quote(ready_file)} ]] && break
            sleep 0.05
          done
          if [[ ! -f {sh_quote(ready_file)} ]]; then
            echo "ready file not created: {ready_file}" >&2
            tail -n 200 {sh_quote(str(logf))} >&2 || true
            kill $pid >/dev/null 2>&1 || true
            wait $pid >/dev/null 2>&1 || true
            exit 3
          fi
          sleep 0.15
          wid="$(xdotool search --name {sh_quote(title)} 2>/dev/null | head -n 1 || true)"
          if [[ -z "$wid" ]]; then
            echo "could not locate window id" >&2
            tail -n 200 {sh_quote(str(logf))} >&2 || true
            exit 4
          fi
          import -window "$wid" {sh_quote(str(out_path))} >/dev/null 2>&1
          kill $pid >/dev/null 2>&1 || true
          wait $pid >/dev/null 2>&1 || true
          rm -f {sh_quote(ready_file)} || true
        """
        proc2 = run(
            [
                "xvfb-run",
                "-a",
                "-s",
                "-screen 0 1000x700x24",
                "bash",
                "-lc",
                bash,
            ]
        )
        if proc2.returncode != 0:
            return False, proc2.stdout.strip()
        if not keep_logs:
            logf.unlink(missing_ok=True)
        return True, ""
    finally:
        reset_profile(test_profile_id)
        gsettings_set_profile_list(orig_profile_list)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate mate-terminal screenshots per mateswatch theme showing C hello-world with syntax highlighting (headless via Xvfb)."
    )
    parser.add_argument(
        "--schemes-dir",
        default="mate-terminal/schemes",
        help="Root directory containing *.dconf",
    )
    parser.add_argument(
        "--out-dir",
        default="generated/showcase/screens",
        help="Directory to write screenshots into",
    )
    parser.add_argument("--all", action="store_true", help="Render all schemes (slow)")
    parser.add_argument(
        "--count", type=int, default=10, help="Sample size without --all"
    )
    parser.add_argument("--seed", type=int, default=1, help="Random seed for sampling")
    parser.add_argument("--shards", type=int, default=1, help="Total shard count")
    parser.add_argument("--shard-index", type=int, default=0, help="Shard index")
    parser.add_argument(
        "--keep-logs", action="store_true", help="Keep logs for passing themes"
    )
    args = parser.parse_args()

    if args.shards < 1 or not (0 <= args.shard_index < args.shards):
        raise SystemExit("error: invalid --shards/--shard-index")

    for cmd in (
        "xvfb-run",
        "mate-terminal",
        "xdotool",
        "import",
        "bash",
        "timeout",
        "dconf",
        "gsettings",
        "python3",
    ):
        require_cmd(cmd)

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

    orig_profile_list = gsettings_get_profile_list()
    failures: list[str] = []

    with tempfile.TemporaryDirectory(prefix="mateswatch-showcase-") as td:
        workdir = Path(td)
        for scheme_path in files:
            out_path = out_dir / f"{scheme_path.stem}.png"
            ok, msg = render_one(
                scheme_path=scheme_path,
                out_path=out_path,
                orig_profile_list=orig_profile_list,
                workdir=workdir,
                keep_logs=args.keep_logs,
            )
            if not ok:
                failures.append(f"{scheme_path}: {msg}")

    if failures:
        print(f"FAIL: {len(failures)}/{len(files)} issues", file=sys.stderr)
        for f in failures[:50]:
            print(f"- {f}", file=sys.stderr)
        return 1

    print(
        f"OK: rendered {len(files)} screenshots (shard {args.shard_index}/{args.shards})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
