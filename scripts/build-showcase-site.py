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
        --panel: #141826;
        --panel2: #101324;
        --text: #e6e6e6;
        --muted: #a7a7a7;
        --border: rgba(255,255,255,0.12);
        --link: #7aa2f7;
        --scale: 1.0;
      }}
      * {{ box-sizing: border-box; }}
      body {{
        margin: 0;
        font-family: ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Ubuntu, Cantarell, Noto Sans, Arial;
        background: var(--bg);
        color: var(--text);
        overflow: hidden;
      }}
      header {{
        position: sticky;
        top: 0;
        z-index: 10;
        background: rgba(15, 17, 26, 0.92);
        backdrop-filter: blur(10px);
        border-bottom: 1px solid var(--border);
      }}
      .wrap {{ max-width: 1400px; margin: 0 auto; padding: 12px 14px; }}
      h1 {{ font-size: 16px; margin: 0 0 6px 0; letter-spacing: 0.3px; }}
      .meta {{ color: var(--muted); font-size: 12px; line-height: 1.3; }}
      .controls {{
        display: grid;
        grid-template-columns: 1fr 140px 200px 180px;
        gap: 8px;
        margin-top: 10px;
      }}
      input, select {{
        width: 100%;
        padding: 10px 10px;
        border-radius: 10px;
        border: 1px solid var(--border);
        background: rgba(255,255,255,0.05);
        color: var(--text);
        outline: none;
        font-size: 13px;
      }}
      .chips {{
        margin-top: 10px;
        display: flex;
        gap: 8px;
        flex-wrap: wrap;
      }}
      .chip {{
        border: 1px solid var(--border);
        background: rgba(255,255,255,0.04);
        color: var(--muted);
        padding: 6px 10px;
        border-radius: 999px;
        font-size: 12px;
        cursor: pointer;
        user-select: none;
      }}
      .chip.on {{
        background: rgba(122,162,247,0.18);
        color: var(--text);
        border-color: rgba(122,162,247,0.45);
      }}
      .layout {{
        height: calc(100vh - 118px);
        display: grid;
        grid-template-columns: minmax(420px, 560px) 1fr;
        gap: 12px;
        padding: 12px;
        max-width: 1400px;
        margin: 0 auto;
      }}
      .list {{
        border: 1px solid var(--border);
        background: var(--panel);
        border-radius: 14px;
        overflow: hidden;
        display: grid;
        grid-template-rows: auto 1fr;
      }}
      .listHead {{
        padding: 10px 12px;
        border-bottom: 1px solid var(--border);
        display: flex;
        justify-content: space-between;
        align-items: baseline;
        gap: 10px;
      }}
      .listHead .count {{ color: var(--muted); font-size: 12px; }}
      .rows {{ overflow: auto; }}
      .row {{
        padding: calc(10px * var(--scale)) calc(12px * var(--scale));
        border-bottom: 1px solid rgba(255,255,255,0.06);
        display: grid;
        grid-template-columns: 1fr;
        gap: 6px;
        cursor: pointer;
      }}
      .row:hover {{ background: rgba(255,255,255,0.04); }}
      .row.sel {{ background: rgba(122,162,247,0.12); }}
      .title {{
        font-size: calc(13px * var(--scale));
        line-height: 1.2;
        word-break: break-word;
      }}
      .sub {{
        font-size: calc(12px * var(--scale));
        color: var(--muted);
        display: flex;
        gap: 10px;
        flex-wrap: wrap;
        align-items: center;
      }}
      code {{
        font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
        font-size: 0.95em;
      }}
      .pal {{
        height: calc(10px * var(--scale));
        border-radius: 999px;
        border: 1px solid rgba(255,255,255,0.12);
        background: #000;
        overflow: hidden;
      }}
      .preview {{
        border: 1px solid var(--border);
        background: var(--panel2);
        border-radius: 14px;
        overflow: hidden;
        display: grid;
        grid-template-rows: auto 1fr;
      }}
      .previewHead {{
        padding: 10px 12px;
        border-bottom: 1px solid var(--border);
        display: flex;
        justify-content: space-between;
        align-items: baseline;
        gap: 10px;
      }}
      .previewHead .actions {{
        display: flex;
        gap: 10px;
        flex-wrap: wrap;
        justify-content: flex-end;
      }}
      a {{ color: var(--link); text-decoration: none; font-size: 12px; }}
      a:hover {{ text-decoration: underline; }}
      button {{
        border: 1px solid var(--border);
        background: rgba(255,255,255,0.04);
        color: var(--text);
        padding: 6px 10px;
        border-radius: 10px;
        font-size: 12px;
        cursor: pointer;
      }}
      button:hover {{ background: rgba(255,255,255,0.07); }}
      .shotWrap {{ overflow: auto; }}
      .shot {{
        display: block;
        width: 100%;
        height: auto;
        image-rendering: auto;
        background: #000;
      }}
      .hint {{ color: var(--muted); font-size: 12px; padding: 10px 12px; }}
      @media (max-width: 1100px) {{
        body {{ overflow: auto; }}
        .layout {{ height: auto; grid-template-columns: 1fr; }}
      }}
    </style>
  </head>
  <body>
    <header>
      <div class="wrap">
        <h1>mateswatch — theme showcase</h1>
        <div class="meta">@@META@@</div>
        <div class="controls">
          <input id="q" placeholder="Search: id, name, tags, vibe..." />
          <select id="type"></select>
          <select id="sort"></select>
          <select id="density"></select>
        </div>
        <div class="chips" id="chips"></div>
      </div>
    </header>

    <main class="layout">
      <section class="list">
        <div class="listHead">
          <div class="count" id="count"></div>
          <div class="count" id="lock"></div>
        </div>
        <div class="rows" id="rows"></div>
      </section>

      <section class="preview">
        <div class="previewHead">
          <div class="count" id="previewTitle"></div>
          <div class="actions">
            <a id="openImg" href="#" target="_blank" rel="noreferrer">Open image</a>
            <a id="openScheme" href="#" target="_blank" rel="noreferrer">Open .dconf</a>
            <button id="copyId" type="button">Copy id</button>
          </div>
        </div>
        <div class="shotWrap">
          <img class="shot" id="previewImg" alt="preview" />
          <div class="hint" id="previewHint"></div>
        </div>
      </section>
    </main>

    <script>
      const INDEX_URL = './data/mateswatch-index.json';
      const SCORES_URL = './data/mateswatch-scheme-scores.json';
      const SCREENS_DIR = '@@SCREENS_DIR@@';
      const SCHEMES_ROOT = './schemes/';

      const q = document.getElementById('q');
      const typeSel = document.getElementById('type');
      const sortSel = document.getElementById('sort');
      const densitySel = document.getElementById('density');
      const chips = document.getElementById('chips');
      const rowsEl = document.getElementById('rows');
      const countEl = document.getElementById('count');
      const lockEl = document.getElementById('lock');
      const previewImg = document.getElementById('previewImg');
      const previewTitle = document.getElementById('previewTitle');
      const previewHint = document.getElementById('previewHint');
      const openImg = document.getElementById('openImg');
      const openScheme = document.getElementById('openScheme');
      const copyId = document.getElementById('copyId');

      let allEntries = [];
      let scores = new Map();
      let filtered = [];
      let locked = false;
      let selectedIndex = 0;

      function norm(s) { return (s || '').toLowerCase(); }

      function palGradient(colors) {
        if (!colors || !colors.length) return 'linear-gradient(90deg,#000,#000)';
        const n = colors.length;
        const step = 100 / n;
        const segs = colors.map((c, i) => `${c} ${(i*step).toFixed(4)}%, ${c} ${((i+1)*step).toFixed(4)}%`);
        return `linear-gradient(90deg, ${segs.join(', ')})`;
      }

      function entrySearch(e) {
        return [
          e.profile_id, e.type, e.visible_name, e.vibe_name,
          (e.vibe_tags || []).join(' '),
        ].join(' ').toLowerCase();
      }

      function applyDensity() {
        const v = densitySel.value || '1.0';
        document.documentElement.style.setProperty('--scale', v);
      }

      function makeOption(value, label) {
        const o = document.createElement('option');
        o.value = value;
        o.textContent = label;
        return o;
      }

      function setPreview(e) {
        if (!e) return;
        const pid = e.profile_id;
        previewTitle.textContent = `${e.visible_name}  —  ${pid}`;
        previewHint.textContent = `type=${e.type} · vibe=${e.vibe_name} · tags=${(e.vibe_tags||[]).join('·')}`;
        previewImg.src = `${SCREENS_DIR}/${pid}.png`;
        openImg.href = `${SCREENS_DIR}/${pid}.png`;
        const rel = (e.path || '').replace('mate-terminal/schemes/', '');
        openScheme.href = `${SCHEMES_ROOT}${rel}`;
        copyId.onclick = async () => {
          try { await navigator.clipboard.writeText(pid); } catch (_) {}
        };
      }

      function updateSelection() {
        const els = rowsEl.querySelectorAll('.row');
        els.forEach((el, idx) => el.classList.toggle('sel', idx === selectedIndex));
      }

      function renderList() {
        rowsEl.textContent = '';
        const frag = document.createDocumentFragment();
        for (let i = 0; i < filtered.length; i++) {
          const e = filtered[i];
          const row = document.createElement('div');
          row.className = 'row' + (i === selectedIndex ? ' sel' : '');
          row.tabIndex = 0;
          row.dataset.i = String(i);

          const title = document.createElement('div');
          title.className = 'title';
          title.textContent = e.visible_name;

          const pal = document.createElement('div');
          pal.className = 'pal';
          pal.style.backgroundImage = palGradient(e.palette || []);

          const sub = document.createElement('div');
          sub.className = 'sub';
          const s = scores.get(e.profile_id);
          const cr = (s && typeof s.contrast_ratio === 'number') ? `CR=${s.contrast_ratio.toFixed(2)}` : '';
          sub.innerHTML = `<code>${e.profile_id}</code> <span>${e.type}</span> <span>${e.vibe_name}</span> <span>${cr}</span>`;

          row.appendChild(title);
          row.appendChild(pal);
          row.appendChild(sub);

          row.addEventListener('mouseenter', () => {
            if (locked) return;
            selectedIndex = i;
            updateSelection();
            setPreview(e);
          });
          row.addEventListener('click', () => {
            selectedIndex = i;
            locked = !locked;
            lockEl.textContent = locked ? 'locked (click a row to unlock)' : 'hover previews';
            updateSelection();
            setPreview(e);
          });
          frag.appendChild(row);
        }
        rowsEl.appendChild(frag);
        countEl.textContent = `${filtered.length.toLocaleString()} / ${allEntries.length.toLocaleString()}`;
        lockEl.textContent = locked ? 'locked (click a row to unlock)' : 'hover previews';
        if (filtered[selectedIndex]) setPreview(filtered[selectedIndex]);
      }

      function applySort() {
        const mode = sortSel.value || 'name';
        const byName = (a,b) => a.visible_name.localeCompare(b.visible_name);
        if (mode === 'name') filtered.sort(byName);
        else if (mode === 'type') filtered.sort((a,b) => (a.type + a.visible_name).localeCompare(b.type + b.visible_name));
        else if (mode === 'contrast') {
          filtered.sort((a,b) => (scores.get(b.profile_id)?.contrast_ratio||0) - (scores.get(a.profile_id)?.contrast_ratio||0) || byName(a,b));
        } else if (mode === 'spread') {
          filtered.sort((a,b) => (scores.get(b.profile_id)?.palette_core_spread||0) - (scores.get(a.profile_id)?.palette_core_spread||0) || byName(a,b));
        } else if (mode === 'bg_sat_low') {
          filtered.sort((a,b) => (scores.get(a.profile_id)?.background_saturation||0) - (scores.get(b.profile_id)?.background_saturation||0) || byName(a,b));
        }
      }

      function addChip(tag) {
        const el = document.createElement('div');
        el.className = 'chip';
        el.textContent = tag;
        el.dataset.tag = tag;
        el.addEventListener('click', () => {
          el.classList.toggle('on');
          applyFilters();
        });
        chips.appendChild(el);
      }

      function applyFilters() {
        const needle = norm(q.value.trim());
        const t = typeSel.value || '';
        const chipsOn = Array.from(chips.querySelectorAll('.chip.on')).map(x => x.dataset.tag);
        filtered = allEntries.filter(e => {
          if (t && e.type !== t) return false;
          if (needle && !entrySearch(e).includes(needle)) return false;
          if (chipsOn.length) {
            const tags = new Set(e.vibe_tags || []);
            for (const c of chipsOn) if (!tags.has(c)) return false;
          }
          return true;
        });
        applySort();
        selectedIndex = Math.min(selectedIndex, Math.max(0, filtered.length - 1));
        renderList();
      }

      function handleKeys(ev) {
        if (!filtered.length) return;
        if (ev.key === 'ArrowDown') {
          selectedIndex = Math.min(filtered.length - 1, selectedIndex + 1);
          locked = true;
          lockEl.textContent = 'locked (click a row to unlock)';
          updateSelection();
          setPreview(filtered[selectedIndex]);
          rowsEl.querySelectorAll('.row')[selectedIndex]?.scrollIntoView({block:'nearest'});
          ev.preventDefault();
        } else if (ev.key === 'ArrowUp') {
          selectedIndex = Math.max(0, selectedIndex - 1);
          locked = true;
          lockEl.textContent = 'locked (click a row to unlock)';
          updateSelection();
          setPreview(filtered[selectedIndex]);
          rowsEl.querySelectorAll('.row')[selectedIndex]?.scrollIntoView({block:'nearest'});
          ev.preventDefault();
        } else if (ev.key === 'Escape') {
          locked = false;
          lockEl.textContent = 'hover previews';
        }
      }

      async function load() {
        const idx = await (await fetch(INDEX_URL)).json();
        allEntries = idx.entries || [];
        try {
          const s = await (await fetch(SCORES_URL)).json();
          for (const r of (s.rows || [])) scores.set(r.profile_id, r);
        } catch (_) {}

        const types = Array.from(new Set(allEntries.map(e => e.type))).sort();
        typeSel.appendChild(makeOption('', `All types (${types.length})`));
        for (const t of types) typeSel.appendChild(makeOption(t, t));

        sortSel.appendChild(makeOption('name', 'Sort: name'));
        sortSel.appendChild(makeOption('type', 'Sort: type'));
        sortSel.appendChild(makeOption('contrast', 'Sort: contrast (high→low)'));
        sortSel.appendChild(makeOption('spread', 'Sort: palette spread (high→low)'));
        sortSel.appendChild(makeOption('bg_sat_low', 'Sort: bg saturation (low→high)'));

        densitySel.appendChild(makeOption('0.85', 'Density: high'));
        densitySel.appendChild(makeOption('1.0', 'Density: normal'));
        densitySel.appendChild(makeOption('1.2', 'Density: comfy'));
        densitySel.appendChild(makeOption('1.4', 'Density: huge'));
        densitySel.value = '1.0';
        applyDensity();

        const tags = new Set();
        for (const e of allEntries) for (const t of (e.vibe_tags || [])) tags.add(t);
        const preferred = ['Dark','Light','HighC','MedC','LowC','Vivid','Pastel','Muted','Warm','Neutral','Cool'];
        for (const t of preferred) if (tags.has(t)) addChip(t);

        q.addEventListener('input', applyFilters);
        typeSel.addEventListener('change', applyFilters);
        sortSel.addEventListener('change', applyFilters);
        densitySel.addEventListener('change', () => { applyDensity(); renderList(); });
        window.addEventListener('keydown', handleKeys);

        applyFilters();
      }

      load().catch(err => {
        countEl.textContent = 'failed to load index';
        previewHint.textContent = String(err);
      });
    </script>
  </body>
</html>
"""


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build a static HTML showcase page (list + palette strip + hover preview)."
    )
    parser.add_argument("--index-json", default="docs/mateswatch-index.json")
    parser.add_argument("--scores-json", default="docs/mateswatch-scheme-scores.json")
    parser.add_argument("--out-dir", default="site")
    parser.add_argument("--screens-dir", default="screens")
    args = parser.parse_args()

    idx = json.loads(Path(args.index_json).read_text(encoding="utf-8"))
    total = idx.get("count", 0)

    out_dir = Path(args.out_dir)
    data_dir = out_dir / "data"
    data_dir.mkdir(parents=True, exist_ok=True)

    (data_dir / "mateswatch-index.json").write_text(
        json.dumps(idx, separators=(",", ":")) + "\n", encoding="utf-8"
    )
    scores_path = Path(args.scores_json)
    if scores_path.exists():
        (data_dir / "mateswatch-scheme-scores.json").write_text(
            scores_path.read_text(encoding="utf-8"), encoding="utf-8"
        )

    out_dir.mkdir(parents=True, exist_ok=True)
    meta = f"{total} themes · hover to preview · click to lock · arrows to navigate"
    (out_dir / "index.html").write_text(
        HTML.replace("@@META@@", meta).replace("@@SCREENS_DIR@@", args.screens_dir),
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
