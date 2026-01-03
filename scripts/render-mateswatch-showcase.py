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


def apply_overrides(dconf_text: str, overrides: dict[str, str]) -> str:
    out = []
    seen: set[str] = set()
    for line in dconf_text.splitlines():
        if "=" in line and not line.startswith("["):
            key, _ = line.split("=", 1)
            key = key.strip()
            if key in overrides:
                out.append(f"{key}={overrides[key]}")
                seen.add(key)
                continue
        out.append(line)
    insert_at = 1 if out and out[0].startswith("[") else 0
    for key, value in overrides.items():
        if key not in seen:
            out.insert(insert_at, f"{key}={value}")
            insert_at += 1
    return "\n".join(out) + "\n"


def update_profile_dconf(
    dconf_text: str,
    *,
    visible_name: str,
    font: str | None,
    columns: int | None,
    rows: int | None,
) -> str:
    overrides = {"visible-name": dconf_quote(visible_name)}
    if font:
        overrides["use-system-font"] = "false"
        overrides["font"] = dconf_quote(font)

    # Reduce "wasted" space in screenshots and make quick-scanning easier.
    overrides.update(
        {
            "scrollbar-position": dconf_quote("hidden"),
            "default-show-menubar": "false",
            "cursor-blink-mode": dconf_quote("off"),
            "silent-bell": "true",
            "scrollback-unlimited": "false",
            "scrollback-lines": "500",
        }
    )
    if columns is not None and rows is not None:
        overrides["use-custom-default-size"] = "true"
        overrides["default-size-columns"] = str(columns)
        overrides["default-size-rows"] = str(rows)
    return apply_overrides(dconf_text, overrides)


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
        "#include <stdbool.h>\n"
        "#include <stdint.h>\n"
        "#include <stdio.h>\n"
        "\n"
        "#define APP_NAME \"mateswatch\"\n"
        "#define ARR_LEN(x) ((int)(sizeof(x) / sizeof((x)[0])))\n"
        "\n"
        "typedef struct {\n"
        "    const char *label;\n"
        "    uint32_t rgb;\n"
        "    bool bold;\n"
        "} Swatch;\n"
        "\n"
        "static const Swatch kSwatches[] = {\n"
        "    {\"accent\", 0x7aa2f7u, true},\n"
        "    {\"warm\", 0xf7768eu, false},\n"
        "    {\"cool\", 0x7dcfffu, true},\n"
        "};\n"
        "\n"
        "static uint32_t clamp_u32(uint32_t v, uint32_t max) {\n"
        "    return v > max ? max : v;\n"
        "}\n"
        "\n"
        "int main(void) {\n"
        "    puts(\"Hello, world!\");\n"
        "    printf(\"%s swatches: %d\\n\", APP_NAME, ARR_LEN(kSwatches));\n"
        "    for (int i = 0; i < ARR_LEN(kSwatches); ++i) {\n"
        "        const Swatch s = kSwatches[i];\n"
        "        printf(\"[%d] %s = 0x%06x%s\\n\", i, s.label, s.rgb, s.bold ? \"!\" : \"\");\n"
        "    }\n"
        "    const uint32_t mix = clamp_u32(kSwatches[0].rgb + kSwatches[1].rgb, 0xffffffu);\n"
        "    printf(\"mix: 0x%06x\\n\", mix);\n"
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
printf '\\033[1mANSI 0-15 (background blocks)\\033[0m\\n'
for row in 0 8; do
  for i in $(seq $row $((row+7))); do
    printf \"\\033[48;5;%sm %2d \\033[0m \" \"$i\" \"$i\"
  done
  printf '\\n'
done
printf '\\n\\033[1mANSI 0-15 (foreground glyphs)\\033[0m\\n'
for row in 0 8; do
  for i in $(seq $row $((row+7))); do
    printf \"\\033[38;5;%sm##\\033[0m%02d \" \"$i\" \"$i\"
  done
  printf '\\n'
done
printf '\\n\\033[1mText samples\\033[0m\\n'
printf '\\033[31merror\\033[0m \\033[33mwarn\\033[0m \\033[32mok\\033[0m \\033[34minfo\\033[0m \\033[35mtrace\\033[0m\\n'
printf '\\033[1mbold\\033[0m \\033[2mdim\\033[0m \\033[4munderline\\033[0m \\033[7mreverse\\033[0m\\n'
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
    font: str | None,
    geometry: str,
    xvfb_size: str,
) -> tuple[bool, str]:
    scheme_text = scheme_path.read_text(encoding="utf-8", errors="replace")
    scheme = parse_scheme(scheme_path)

    # xdotool's `search --name` treats the value as a regex. Keep the title to a
    # simple, regex-safe alphabet to avoid accidental regex metacharacters from
    # theme IDs (e.g. "+" in "vs-code-dark+").
    title_suffix = hashlib.sha1(scheme.profile_id.encode("utf-8")).hexdigest()[:12]
    title = f"MSW-SHOW-{os.getpid()}-{title_suffix}"
    ready_file = f"/tmp/mateswatch-ready-{os.getpid()}-{scheme.profile_id}"

    test_profile_id = f"msw-show-{scheme.profile_id}"
    test_visible = f"MSW SHOW {scheme.visible_name}"

    m = re.match(r"^(\\d+)x(\\d+)$", geometry.strip())
    cols = int(m.group(1)) if m else None
    rows = int(m.group(2)) if m else None
    test_text = update_profile_dconf(
        scheme_text,
        visible_name=test_visible,
        font=font,
        columns=cols,
        rows=rows,
    )

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
          timeout 20 mate-terminal --disable-factory --hide-menubar --geometry={sh_quote(geometry)} -t {sh_quote(title)} --profile {sh_quote(test_visible)} --command "$cmd_str" >{sh_quote(str(logf))} 2>&1 &
          pid=$!
          for _ in $(seq 1 200); do
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
          wid="$(xdotool search --sync --limit 1 --name {sh_quote(title)} 2>/dev/null | head -n 1 || true)"
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
                f"-screen 0 {xvfb_size}x24",
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
    parser.add_argument(
        "--font",
        default="Monospace 18",
        help="Font string for the temporary profile (use empty string to keep default).",
    )
    parser.add_argument(
        "--geometry",
        default="92x26",
        help="Terminal geometry in columnsxrows (e.g. 100x30).",
    )
    parser.add_argument(
        "--xvfb-size",
        default="1280x800",
        help="Xvfb screen size in WxH (e.g. 1400x900).",
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
                font=args.font or None,
                geometry=args.geometry,
                xvfb_size=args.xvfb_size,
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
