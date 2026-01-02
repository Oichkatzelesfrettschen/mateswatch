#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import random
import re
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

from PIL import Image

from theme_common import color_to_rgb8, dconf_quote


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


def parse_palette(palette_value: str) -> list[str]:
    raw = unquote(palette_value)
    parts = raw.split(":")
    if len(parts) != 16:
        raise ValueError(f"palette: expected 16 colors, got {len(parts)}")
    return [color_to_rgb8(p) for p in parts]


def parse_scheme(path: Path) -> tuple[str, str, list[str], str]:
    kv = read_kv(path.read_text(encoding="utf-8", errors="replace"))
    visible = unquote(kv.get("visible-name", path.stem))
    bg = color_to_rgb8(unquote(kv["background-color"]))
    fg = color_to_rgb8(unquote(kv["foreground-color"]))
    palette = parse_palette(kv["palette"])
    return visible, bg, fg, palette


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


def rgb_hex_to_tuple(rgb: str) -> tuple[int, int, int]:
    c = rgb.lstrip("#")
    return int(c[0:2], 16), int(c[2:4], 16), int(c[4:6], 16)


def mean_rgb(pixels: list[tuple[int, int, int]]) -> tuple[int, int, int]:
    r = sum(p[0] for p in pixels) / len(pixels)
    g = sum(p[1] for p in pixels) / len(pixels)
    b = sum(p[2] for p in pixels) / len(pixels)
    return int(round(r)), int(round(g)), int(round(b))


def sample_box(
    img: Image.Image, *, x: int, y: int, w: int = 6, h: int = 6
) -> tuple[int, int, int]:
    px = img.load()
    xs = range(max(0, x - w // 2), min(img.width, x + w // 2 + 1))
    ys = range(max(0, y - h // 2), min(img.height, y + h // 2 + 1))
    samples: list[tuple[int, int, int]] = []
    for yy in ys:
        for xx in xs:
            r, g, b = px[xx, yy][:3]
            samples.append((r, g, b))
    return mean_rgb(samples)


def dominant_color(img: Image.Image) -> tuple[int, int, int]:
    # Downsample to speed up and reduce noise.
    small = img.convert("RGB").resize((img.width // 4, img.height // 4))
    colors = small.getcolors(maxcolors=256 * 256 * 256)
    if not colors:
        raise RuntimeError("unable to compute dominant color")
    count, rgb = max(colors, key=lambda t: t[0])
    _ = count
    return rgb


@dataclass(frozen=True)
class BlockLayout:
    x0: int
    y0: int
    row_h: int
    left_w: int
    right_x0: int


def detect_layout(
    img: Image.Image,
    bg_rgb: tuple[int, int, int],
    *,
    bg_tol: int = 6,
) -> BlockLayout:
    px = img.convert("RGB").load()

    min_run = 30  # pixels
    # Skip menu bar/title decorations (when present under Xvfb).
    y_start = 40
    y_end = min(img.height, 320)

    best: tuple[int, int, int, tuple[int, int, int], int] | None = None
    # best = (y0, left_x0, left_w, left_color, right_x0)

    for y in range(y_start, y_end):
        runs: list[tuple[int, int, tuple[int, int, int]]] = []  # (x0, w, color)
        x = 0
        while x < img.width:
            c = px[x, y]
            x0 = x
            while x < img.width and px[x, y] == c:
                x += 1
            w = x - x0
            if chan_diff(c, bg_rgb) > bg_tol and w >= min_run:
                runs.append((x0, w, c))

        # We render 3 non-bg runs per row: marker, left block, right block.
        if len(runs) < 3:
            continue

        runs.sort(key=lambda t: t[0])
        # First run is the left-side marker; second is the left palette block.
        left_x0, left_w, left_c = runs[1]
        right = next((r for r in runs[2:] if r[0] > left_x0 + left_w), None)
        if right is None:
            continue

        best = (y, left_x0, left_w, left_c, right[0])
        break

    if best is None:
        raise RuntimeError(
            "could not locate block grid (marker + two long color runs) in screenshot"
        )

    y0, x0, left_w, left_c, right_x0 = best

    # Determine row height using the left-side per-row marker stripe; this avoids
    # ambiguity when multiple palette rows share identical colors.
    mx = max(0, x0 - min_run)  # marker should be left of the left block
    # Find a pixel in the marker stripe for this y by scanning left a bit.
    found_mx = None
    for xx in range(max(0, x0 - 120), x0):
        if chan_diff(px[xx, y0], bg_rgb) > bg_tol:
            found_mx = xx
            break
    if found_mx is not None:
        mx = found_mx
    mc = px[mx, y0]

    # Expand to marker segment bounds.
    top = y0
    while top > 0 and px[mx, top - 1] == mc:
        top -= 1
    bottom = y0
    while bottom < img.height and px[mx, bottom] == mc:
        bottom += 1
    row_h = max(8, bottom - top)

    # Walk upwards through the marker segments to find the first row (row 0).
    y_cursor = top - 1
    while y_cursor > 0 and chan_diff(px[mx, y_cursor], bg_rgb) > bg_tol:
        c = px[mx, y_cursor]
        seg_top = y_cursor
        while seg_top > 0 and px[mx, seg_top - 1] == c:
            seg_top -= 1
        top = seg_top
        y_cursor = top - 1

    y0 = top

    return BlockLayout(x0=x0, y0=y0, row_h=row_h, left_w=left_w, right_x0=right_x0)


def chan_diff(a: tuple[int, int, int], b: tuple[int, int, int]) -> int:
    return max(abs(a[0] - b[0]), abs(a[1] - b[1]), abs(a[2] - b[2]))


def make_pattern_script() -> str:
    # Prints an 8x2 block grid:
    # - left block uses xterm-256 background 0..7 (maps to ANSI palette 0..7)
    # - right block uses xterm-256 background 8..15 (maps to ANSI palette 8..15)
    # Keep it on-screen (avoid scrolling it off) and sleep for capture.
    # Uses only spaces so foreground doesn’t affect pixels.
    return r"""
set -euo pipefail
printf '\033[?25l'
printf '\033[H\033[2J'
for i in $(seq 0 7); do
  # Per-row marker (xterm-256 colors) to make row boundaries detectable even when
  # multiple ANSI palette entries share identical RGB values.
  printf "\033[48;5;%dm%6s\033[0m" "$((196+i))" ""
  printf "%1s" ""
  printf "\033[48;5;%dm%28s\033[0m" "$i" ""
  printf "%1s" ""
  printf "\033[48;5;%dm%28s\033[0m" "$((8+i))" ""
  printf "\n"
done
if [[ -n "${MATESWATCH_READY_FILE:-}" ]]; then
  printf 'ready\n' >"${MATESWATCH_READY_FILE}" 2>/dev/null || true
fi
sleep 3.0
"""


def xvfb_render(*, visible_name: str, out_png: Path) -> tuple[int, str]:
    script = make_pattern_script()
    with tempfile.NamedTemporaryFile("w", delete=False, suffix=".sh") as f:
        f.write(script)
        script_path = f.name
    os.chmod(script_path, 0o755)
    try:
        # mate-terminal's --command accepts a *single* argument; pass a shell-ish string.
        # Avoid extra quoting inside the command string; the outer shell quoting is sufficient.
        # Signal file to coordinate screenshot timing (avoid racing GTK startup).
        ready_file = (
            f"/tmp/mateswatch-ready-{os.getpid()}-{os.path.basename(script_path)}"
        )
        cmd_str = f"env MATESWATCH_READY_FILE={ready_file} bash {script_path}"
        cmd = [
            "xvfb-run",
            "-a",
            "-s",
            "-screen 0 900x600x24",
            "bash",
            "-lc",
            # Launch terminal fullscreen, render blocks, screenshot root, then exit.
            # The command sleeps long enough for the first frame to paint.
            f"""
              set -euo pipefail
              rm -f {sh_quote(ready_file)} || true
              title="MSW-RENDER-{os.getpid()}"
              timeout 8 mate-terminal --disable-factory --hide-menubar --geometry=120x40 -t "$title" --profile={sh_quote(visible_name)} --command {sh_quote(cmd_str)} >/dev/null 2>&1 &
              pid=$!
              # Wait for the child command to reach "ready", then screenshot.
              for _ in $(seq 1 60); do
                [[ -f {sh_quote(ready_file)} ]] && break
                sleep 0.1
              done
              if [[ ! -f {sh_quote(ready_file)} ]]; then
                echo "ready file not created: {ready_file}" >&2
                kill $pid >/dev/null 2>&1 || true
                wait $pid >/dev/null 2>&1 || true
                exit 3
              fi
              # small extra delay for paint
              sleep 0.2
              if command -v xdotool >/dev/null 2>&1; then
                wid="$(xdotool search --name "$title" 2>/dev/null | head -n 1 || true)"
              else
                wid=""
              fi
              if [[ -n "$wid" ]]; then
                import -window "$wid" {sh_quote(str(out_png))} >/dev/null 2>&1
              else
                import -window root {sh_quote(str(out_png))} >/dev/null 2>&1
              fi
              wait $pid >/dev/null 2>&1 || true
              rm -f {sh_quote(ready_file)} || true
            """,
        ]
        proc = run(cmd)
        return proc.returncode, proc.stdout
    finally:
        try:
            os.unlink(script_path)
        except OSError:
            pass


def sh_quote(s: str) -> str:
    return "'" + s.replace("\\", "\\\\").replace("'", "'\\''") + "'"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Screenshot-based render fidelity test for mateswatch schemes."
    )
    parser.add_argument(
        "--schemes-dir",
        default="mate-terminal/schemes",
        help="Root directory containing *.dconf",
    )
    parser.add_argument("--all", action="store_true", help="Test all schemes (slow)")
    parser.add_argument(
        "--count", type=int, default=20, help="Sample size when not using --all"
    )
    parser.add_argument("--seed", type=int, default=1, help="Random seed for sampling")
    parser.add_argument(
        "--max-chan-diff",
        type=int,
        default=6,
        help="Max per-channel RGB diff tolerance",
    )
    parser.add_argument(
        "--keep", action="store_true", help="Keep screenshots for passing themes too"
    )
    args = parser.parse_args()

    for cmd in (
        "xvfb-run",
        "mate-terminal",
        "import",
        "bash",
        "timeout",
        "dconf",
        "gsettings",
    ):
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
    out_dir = Path("generated/visual")
    out_dir.mkdir(parents=True, exist_ok=True)

    failures: list[str] = []
    tested = 0

    try:
        for i, scheme_path in enumerate(files, start=1):
            tested += 1
            scheme_text = scheme_path.read_text(encoding="utf-8", errors="replace")
            visible, bg, _fg, palette = parse_scheme(scheme_path)

            test_id = f"msw-rtest-{i:04d}"
            test_visible = f"MSW RENDER {visible}"
            test_text = with_visible_name(scheme_text, test_visible)

            proc = run(
                ["dconf", "load", f"/org/mate/terminal/profiles/{test_id}/"],
                stdin_text=test_text,
            )
            if proc.returncode != 0:
                failures.append(
                    f"{scheme_path}: dconf load failed: {proc.stdout.strip()}"
                )
                continue

            # Ensure profile is discoverable.
            gsettings_set_profile_list(
                orig_list + ([test_id] if test_id not in orig_list else [])
            )

            png_path = out_dir / f"{test_id}.png"
            rc, out = xvfb_render(visible_name=test_visible, out_png=png_path)
            if rc != 0 or not png_path.is_file():
                failures.append(
                    f"{scheme_path}: xvfb render failed rc={rc}: {out.strip()}"
                )
                reset_profile(test_id)
                continue

            img = Image.open(png_path).convert("RGB")
            bg_rgb = rgb_hex_to_tuple(bg)

            # Detect dominant background; if mismatch, use dominant for layout.
            dom = dominant_color(img)
            use_bg = bg_rgb if chan_diff(dom, bg_rgb) <= args.max_chan_diff else dom

            try:
                layout = detect_layout(img, use_bg)
            except Exception as e:
                failures.append(f"{scheme_path}: layout detect failed: {e}")
                if not args.keep:
                    png_path.unlink(missing_ok=True)
                reset_profile(test_id)
                continue

            # Sample centers.
            for row in range(8):
                y = layout.y0 + row * layout.row_h + layout.row_h // 2
                lx = layout.x0 + layout.left_w // 2
                rx = layout.right_x0 + layout.left_w // 2
                got_l = sample_box(img, x=lx, y=y)
                got_r = sample_box(img, x=rx, y=y)
                exp_l = rgb_hex_to_tuple(palette[row])
                exp_r = rgb_hex_to_tuple(palette[8 + row])

                if chan_diff(got_l, exp_l) > args.max_chan_diff:
                    failures.append(
                        f"{scheme_path}: row {row} left mismatch got={got_l} exp={exp_l} (maxdiff={chan_diff(got_l, exp_l)})"
                    )
                    break
                if chan_diff(got_r, exp_r) > args.max_chan_diff:
                    failures.append(
                        f"{scheme_path}: row {row} right mismatch got={got_r} exp={exp_r} (maxdiff={chan_diff(got_r, exp_r)})"
                    )
                    break

            if failures and failures[-1].startswith(str(scheme_path)):
                # Keep screenshot for this failing theme.
                pass
            else:
                if not args.keep:
                    png_path.unlink(missing_ok=True)

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
        print(f"(screenshots in {out_dir}/ for failures)", file=sys.stderr)
        return 1

    print(f"OK: render-verified {tested} scheme(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
