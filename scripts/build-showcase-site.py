#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path


HTML = """\
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>mateswatch showcase</title>
    <style>
      :root {{
        --bg: #0f111a;
        --panel: #171a26;
        --text: #e6e6e6;
        --muted: #a7a7a7;
        --border: rgba(255,255,255,0.12);
        --link: #7aa2f7;
      }}
      * {{ box-sizing: border-box; }}
      body {{
        margin: 0;
        font-family: ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Ubuntu, Cantarell, Noto Sans, Arial;
        background: var(--bg);
        color: var(--text);
      }}
      header {{
        position: sticky;
        top: 0;
        z-index: 10;
        background: rgba(15, 17, 26, 0.92);
        backdrop-filter: blur(10px);
        border-bottom: 1px solid var(--border);
      }}
      .wrap {{ max-width: 1200px; margin: 0 auto; padding: 14px 16px; }}
      h1 {{ font-size: 18px; margin: 0 0 10px 0; letter-spacing: 0.3px; }}
      .meta {{ color: var(--muted); font-size: 13px; }}
      .controls {{
        display: grid;
        grid-template-columns: 1fr 220px;
        gap: 10px;
        margin-top: 10px;
      }}
      input, select {{
        width: 100%;
        padding: 10px 12px;
        border-radius: 10px;
        border: 1px solid var(--border);
        background: rgba(255,255,255,0.05);
        color: var(--text);
        outline: none;
      }}
      main .wrap {{ padding-top: 18px; padding-bottom: 30px; }}
      .grid {{
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
        gap: 14px;
      }}
      .card {{
        border: 1px solid var(--border);
        background: var(--panel);
        border-radius: 14px;
        overflow: hidden;
      }}
      .shot {{
        display: block;
        width: 100%;
        height: auto;
        background: #000;
      }}
      .info {{ padding: 10px 12px 12px 12px; }}
      .name {{
        font-size: 13px;
        line-height: 1.25;
        margin: 0 0 6px 0;
        word-break: break-word;
      }}
      .small {{
        font-size: 12px;
        color: var(--muted);
        display: flex;
        gap: 8px;
        flex-wrap: wrap;
      }}
      a {{ color: var(--link); text-decoration: none; }}
      a:hover {{ text-decoration: underline; }}
      .hidden {{ display: none; }}
    </style>
  </head>
  <body>
    <header>
      <div class="wrap">
        <h1>mateswatch — theme showcase</h1>
        <div class="meta">{meta}</div>
        <div class="controls">
          <input id="q" placeholder="Filter by id, type, vibe, tags..." />
          <select id="type">
            <option value="">All types</option>
            {type_options}
          </select>
        </div>
      </div>
    </header>
    <main>
      <div class="wrap">
        <div class="grid" id="grid">
          {cards}
        </div>
      </div>
    </main>
    <script>
      const q = document.getElementById('q');
      const type = document.getElementById('type');
      const cards = Array.from(document.querySelectorAll('[data-search]'));
      function apply() {{
        const needle = q.value.trim().toLowerCase();
        const t = type.value;
        for (const el of cards) {{
          const s = el.getAttribute('data-search');
          const et = el.getAttribute('data-type');
          const okNeedle = !needle || (s && s.includes(needle));
          const okType = !t || et === t;
          el.classList.toggle('hidden', !(okNeedle && okType));
        }}
      }}
      q.addEventListener('input', apply);
      type.addEventListener('change', apply);
    </script>
  </body>
</html>
"""


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a static HTML showcase page.")
    parser.add_argument("--index-json", default="docs/mateswatch-index.json")
    parser.add_argument("--out-dir", default="site")
    parser.add_argument("--screens-dir", default="screens")
    args = parser.parse_args()

    idx = json.loads(Path(args.index_json).read_text(encoding="utf-8"))
    entries = idx["entries"]
    total = idx["count"]
    types = list(idx["types"].keys())
    types.sort()

    type_options = "\n".join(
        f'<option value="{t}">{t} ({idx["types"][t]})</option>' for t in types
    )

    cards = []
    for e in entries:
        pid = e["profile_id"]
        t = e["type"]
        visible = e["visible_name"]
        vibe = e["vibe_name"]
        tags = e["vibe_tags"]
        path = e["path"]
        search = " ".join(
            [
                str(pid),
                str(t),
                str(visible),
                str(vibe),
                " ".join(tags),
                str(path),
            ]
        ).lower()
        img = f"{args.screens_dir}/{pid}.png"
        cards.append(
            f"""
            <div class="card" data-type="{t}" data-search="{search}">
              <a href="{img}">
                <img class="shot" loading="lazy" src="{img}" alt="{pid}" />
              </a>
              <div class="info">
                <p class="name">{visible}</p>
                <div class="small">
                  <span><code>{pid}</code></span>
                  <span>{t}</span>
                  <span>{vibe}</span>
                </div>
              </div>
            </div>
            """.strip()
        )

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "index.html").write_text(
        HTML.format(
            meta=f"{total} themes · screenshots generated by GitHub Actions",
            type_options=type_options,
            cards="\n".join(cards),
        ),
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
