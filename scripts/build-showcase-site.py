#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


HTML = """\
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>mateswatch showcase</title>
    <style>
      :root {
        --bg: #0f1114;
        --panel: #141820;
        --panel-2: #191f29;
        --panel-3: #10141a;
        --text: #e9e6df;
        --muted: #a9a59c;
        --accent: #4bd1a5;
        --accent-2: #f3b35b;
        --border: rgba(255,255,255,0.12);
        --shadow: rgba(0,0,0,0.35);
        --scale: 1.0;
        --thumb-w: 160px;
      }
      * { box-sizing: border-box; }
      body {
        margin: 0;
        font-family: "IBM Plex Sans", "Source Sans 3", "Noto Sans", "Segoe UI", sans-serif;
        color: var(--text);
        background: var(--bg);
        overflow: hidden;
      }
      header {
        position: sticky;
        top: 0;
        z-index: 10;
        border-bottom: 1px solid var(--border);
        backdrop-filter: blur(8px);
        background: rgba(10, 12, 15, 0.96);
      }
      .wrap {
        max-width: 1500px;
        margin: 0 auto;
        padding: 12px 16px;
      }
      h1 {
        font-size: 18px;
        margin: 0 0 6px 0;
        letter-spacing: 0.4px;
      }
      .meta {
        color: var(--muted);
        font-size: 12px;
        line-height: 1.35;
      }
      .controls {
        display: grid;
        grid-template-columns: 1fr 150px 200px 160px 150px 170px;
        gap: 8px;
        margin-top: 10px;
      }
      input, select {
        width: 100%;
        padding: 10px 12px;
        border-radius: 10px;
        border: 1px solid var(--border);
        background: rgba(255,255,255,0.05);
        color: var(--text);
        outline: none;
        font-size: 13px;
      }
      .layout {
        height: calc(100vh - 134px);
        display: grid;
        grid-template-columns: 320px minmax(360px, 560px) minmax(0, 1fr);
        gap: 14px;
        padding: 14px;
        max-width: 1500px;
        margin: 0 auto;
      }
      .panel {
        border: 1px solid var(--border);
        background: var(--panel);
        border-radius: 14px;
        padding: 12px;
        box-shadow: 0 12px 24px var(--shadow);
      }
      .panel + .panel { margin-top: 12px; }
      .panelTitle {
        font-size: 11px;
        color: var(--muted);
        letter-spacing: 0.16em;
        text-transform: uppercase;
        margin-bottom: 8px;
      }
      .overviewGrid {
        display: grid;
        grid-template-columns: 70px repeat(3, 1fr);
        gap: 6px;
        font-size: 12px;
      }
      .overviewCell {
        border: 1px solid rgba(255,255,255,0.08);
        background: rgba(255,255,255,0.03);
        border-radius: 8px;
        padding: 8px;
        text-align: center;
        color: var(--muted);
      }
      .overviewCell.head {
        background: transparent;
        border: none;
        color: var(--muted);
        font-weight: 600;
      }
      .overviewCell.btn {
        cursor: pointer;
        color: var(--text);
        transition: border 120ms ease, background 120ms ease;
      }
      .overviewCell.btn.active {
        border-color: rgba(75,209,165,0.6);
        background: rgba(75,209,165,0.12);
      }
      .overviewCell .count {
        font-size: 14px;
        font-weight: 600;
      }
      .overviewCell .label {
        font-size: 11px;
        color: var(--muted);
      }
      .filterGroup { margin-bottom: 10px; }
      .filterTitle {
        font-size: 12px;
        color: var(--muted);
        margin-bottom: 6px;
      }
      .filterRow {
        display: flex;
        gap: 6px;
        flex-wrap: wrap;
      }
      .filterBtn {
        border: 1px solid var(--border);
        background: rgba(255,255,255,0.04);
        color: var(--text);
        padding: 6px 10px;
        border-radius: 999px;
        font-size: 12px;
        cursor: pointer;
      }
      .filterBtn.active {
        border-color: rgba(75,209,165,0.6);
        background: rgba(75,209,165,0.15);
      }
      .filterBtn .count {
        color: var(--muted);
        margin-left: 6px;
      }
      .compareList {
        display: grid;
        gap: 8px;
      }
      .compareItem {
        border: 1px solid rgba(255,255,255,0.08);
        background: rgba(255,255,255,0.03);
        border-radius: 10px;
        padding: 8px;
        display: grid;
        grid-template-columns: 56px 1fr auto;
        gap: 8px;
        align-items: center;
      }
      .compareItem img {
        width: 56px;
        height: 40px;
        object-fit: cover;
        border-radius: 6px;
        border: 1px solid rgba(255,255,255,0.12);
        background: #000;
      }
      .compareItem .name {
        font-size: 12px;
        line-height: 1.2;
      }
      .compareItem button {
        border: 1px solid var(--border);
        background: rgba(255,255,255,0.04);
        color: var(--text);
        padding: 4px 8px;
        border-radius: 8px;
        font-size: 11px;
        cursor: pointer;
      }
      .list {
        border: 1px solid var(--border);
        background: var(--panel);
        border-radius: 14px;
        overflow: hidden;
        display: grid;
        grid-template-rows: auto 1fr;
        box-shadow: 0 12px 24px var(--shadow);
      }
      .listHead {
        padding: 10px 12px;
        border-bottom: 1px solid var(--border);
        display: flex;
        justify-content: space-between;
        align-items: baseline;
        gap: 10px;
      }
      .status { color: var(--muted); font-size: 12px; }
      .rows {
        overflow: auto;
        scroll-behavior: smooth;
      }
      .groupHead {
        position: sticky;
        top: 0;
        z-index: 2;
        background: var(--panel-2);
        border-bottom: 1px solid var(--border);
        padding: 8px 12px;
        font-size: 11px;
        letter-spacing: 0.16em;
        text-transform: uppercase;
        color: var(--muted);
      }
      .row {
        padding: calc(10px * var(--scale)) calc(12px * var(--scale));
        border-bottom: 1px solid rgba(255,255,255,0.06);
        display: grid;
        grid-template-columns: var(--thumb-w) 1fr auto;
        gap: 12px;
        align-items: center;
        cursor: pointer;
      }
      .row:hover { background: rgba(255,255,255,0.04); }
      .row.sel { background: rgba(75,209,165,0.1); }
      .thumb {
        width: 100%;
        aspect-ratio: 4 / 3;
        border-radius: 10px;
        border: 1px solid rgba(255,255,255,0.12);
        background: #000;
        object-fit: cover;
      }
      .thumb.broken { filter: grayscale(1); opacity: 0.35; }
      .title {
        font-size: calc(14px * var(--scale));
        line-height: 1.2;
        margin: 0 0 6px 0;
      }
      .sub {
        font-size: calc(12px * var(--scale));
        color: var(--muted);
        display: flex;
        gap: 10px;
        flex-wrap: wrap;
      }
      .pal {
        height: calc(10px * var(--scale));
        border-radius: 999px;
        border: 1px solid rgba(255,255,255,0.12);
        background: #000;
        overflow: hidden;
        margin-top: 6px;
      }
      .pinBtn {
        border: 1px solid var(--border);
        background: rgba(255,255,255,0.04);
        color: var(--text);
        padding: 6px 10px;
        border-radius: 10px;
        font-size: 12px;
        cursor: pointer;
      }
      .pinBtn.active {
        border-color: rgba(75,209,165,0.6);
        background: rgba(75,209,165,0.15);
      }
      .preview {
        border: 1px solid var(--border);
        background: var(--panel-2);
        border-radius: 14px;
        overflow: hidden;
        display: grid;
        grid-template-rows: auto 1fr auto;
        box-shadow: 0 12px 24px var(--shadow);
      }
      .previewHead {
        padding: 10px 12px;
        border-bottom: 1px solid var(--border);
        display: flex;
        justify-content: space-between;
        align-items: baseline;
        gap: 10px;
      }
      .previewHead .actions {
        display: flex;
        gap: 10px;
        flex-wrap: wrap;
        justify-content: flex-end;
      }
      a { color: var(--accent); text-decoration: none; font-size: 12px; }
      a:hover { text-decoration: underline; }
      button { font-family: inherit; }
      .shotWrap { overflow: auto; background: var(--panel-3); }
      .shot {
        display: block;
        width: 100%;
        height: auto;
        background: #000;
      }
      .hint {
        color: var(--muted);
        font-size: 12px;
        padding: 10px 12px;
        border-top: 1px solid var(--border);
      }
      .previewPal {
        display: grid;
        grid-template-columns: repeat(16, 1fr);
        gap: 2px;
        padding: 8px 12px 12px 12px;
        background: rgba(255,255,255,0.02);
        border-top: 1px solid var(--border);
      }
      .previewPal span {
        height: 12px;
        border-radius: 2px;
        border: 1px solid rgba(0,0,0,0.3);
      }
      .hintSmall { font-size: 11px; color: var(--muted); }
      @media (max-width: 1300px) {
        .layout { grid-template-columns: 300px minmax(320px, 1fr); }
        .preview { display: none; }
      }
      @media (max-width: 1000px) {
        body { overflow: auto; }
        .layout { height: auto; grid-template-columns: 1fr; }
      }
      @media (prefers-reduced-motion: reduce) {
        * { scroll-behavior: auto; }
      }
      body[data-view="gallery"] {
        overflow: auto;
      }
      body[data-view="gallery"] .layout {
        height: auto;
        grid-template-columns: 320px 1fr;
      }
      body[data-view="gallery"] .preview {
        display: none;
      }
      body[data-view="gallery"] .rows {
        overflow: visible;
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
        gap: 12px;
        padding: 12px;
      }
      body[data-view="gallery"] .row {
        grid-template-columns: 1fr;
        border: 1px solid rgba(255,255,255,0.06);
        border-radius: 14px;
        background: rgba(255,255,255,0.03);
      }
      body[data-view="gallery"] .thumb {
        aspect-ratio: 16 / 9;
      }
      body[data-view="gallery"] .groupHead { position: static; }
      @media (max-width: 900px) {
        .controls { grid-template-columns: 1fr; }
      }
    </style>
  </head>
  <body data-view="focus">
    <header>
      <div class="wrap">
        <h1>mateswatch showcase</h1>
        <div class="meta">@@META@@</div>
        <div class="controls">
          <input id="q" placeholder="Search: id, name, tags, vibe..." />
          <select id="type"></select>
          <select id="sort"></select>
          <select id="group"></select>
          <select id="density"></select>
          <select id="view"></select>
        </div>
      </div>
    </header>

    <main class="layout">
      <aside class="sidebar">
        <section class="panel">
          <div class="panelTitle">Overview map</div>
          <div class="overviewGrid" id="overview"></div>
          <div class="hintSmall" style="margin-top:8px;">
            grid = lightness (rows) x temperature (columns)
          </div>
        </section>

        <section class="panel">
          <div class="panelTitle">Filters</div>
          <div class="filterGroup">
            <div class="filterTitle">Lightness</div>
            <div class="filterRow" id="filterLight"></div>
          </div>
          <div class="filterGroup">
            <div class="filterTitle">Temperature</div>
            <div class="filterRow" id="filterTemp"></div>
          </div>
          <div class="filterGroup">
            <div class="filterTitle">Vividness</div>
            <div class="filterRow" id="filterVivid"></div>
          </div>
          <div class="filterGroup">
            <div class="filterTitle">Contrast</div>
            <div class="filterRow" id="filterContrast"></div>
          </div>
          <div class="filterGroup">
            <button id="clearFilters" class="filterBtn">Clear filters</button>
          </div>
        </section>

        <section class="panel">
          <div class="panelTitle">Compare tray</div>
          <div class="compareList" id="compare"></div>
          <div class="hintSmall" style="margin-top:6px;">Pin up to 6 themes for side-by-side review.</div>
          <div style="margin-top:8px;">
            <button id="clearCompare" class="filterBtn">Clear tray</button>
          </div>
        </section>
      </aside>

      <section class="list">
        <div class="listHead">
          <div class="status" id="count"></div>
          <div class="status" id="lock"></div>
        </div>
        <div class="rows" id="rows"></div>
      </section>

      <section class="preview">
        <div class="previewHead">
          <div class="status" id="previewTitle"></div>
          <div class="actions">
            <a id="openImg" href="#" target="_blank" rel="noreferrer">Open image</a>
            <a id="openScheme" href="#" target="_blank" rel="noreferrer">Open .dconf</a>
            <button id="copyId" type="button">Copy id</button>
          </div>
        </div>
        <div class="shotWrap">
          <img class="shot" id="previewImg" alt="preview" />
        </div>
        <div class="hint" id="previewHint"></div>
        <div class="previewPal" id="previewPal"></div>
      </section>
    </main>

    @@INLINE_INDEX@@
    @@INLINE_SCORES@@

    <script>
      const INDEX_URL = './data/mateswatch-index.json';
      const SCORES_URL = './data/mateswatch-scheme-scores.json';
      const SCREENS_DIR = '@@SCREENS_DIR@@';
      const THUMBS_DIR = './thumbs';
      const SCHEMES_ROOT = './schemes/';

      const q = document.getElementById('q');
      const typeSel = document.getElementById('type');
      const sortSel = document.getElementById('sort');
      const groupSel = document.getElementById('group');
      const densitySel = document.getElementById('density');
      const viewSel = document.getElementById('view');
      const rowsEl = document.getElementById('rows');
      const countEl = document.getElementById('count');
      const lockEl = document.getElementById('lock');
      const previewImg = document.getElementById('previewImg');
      const previewTitle = document.getElementById('previewTitle');
      const previewHint = document.getElementById('previewHint');
      const previewPal = document.getElementById('previewPal');
      const openImg = document.getElementById('openImg');
      const openScheme = document.getElementById('openScheme');
      const copyId = document.getElementById('copyId');
      const overviewEl = document.getElementById('overview');
      const filterLightEl = document.getElementById('filterLight');
      const filterTempEl = document.getElementById('filterTemp');
      const filterVividEl = document.getElementById('filterVivid');
      const filterContrastEl = document.getElementById('filterContrast');
      const clearFiltersBtn = document.getElementById('clearFilters');
      const compareEl = document.getElementById('compare');
      const clearCompareBtn = document.getElementById('clearCompare');

      const LIGHTNESS = ['Dark', 'Mid', 'Light'];
      const TEMPS = ['Cool', 'Neutral', 'Warm'];
      const VIVIDNESS = ['Vivid', 'Muted', 'Pastel', 'Neutral'];
      const CONTRAST = ['High', 'Med', 'Low'];

      let allEntries = [];
      let scores = new Map();
      let filtered = [];
      let locked = false;
      let selectedIndex = 0;
      let observer = null;
      let listObserver = null;
      let renderedCount = 0;
      const PAGE_SIZE = 160;
      const pinned = [];
      const pinLimit = 6;

      const filters = {
        lightness: '',
        temperature: '',
        vividness: '',
        contrast: ''
      };

      function norm(s) { return (s || '').toLowerCase(); }

      function readInlineJson(id) {
        const el = document.getElementById(id);
        if (!el) return null;
        try { return JSON.parse(el.textContent); } catch (_) { return null; }
      }

      function pickTag(tags, options, fallback) {
        for (const opt of options) {
          if (tags.includes(opt)) return opt;
        }
        return fallback;
      }

      function deriveProps(e) {
        const tags = e.vibe_tags || [];
        e.lightness = pickTag(tags, ['Light', 'Dark'], 'Mid');
        e.temperature = pickTag(tags, ['Warm', 'Cool'], 'Neutral');
        e.vividness = pickTag(tags, ['Vivid', 'Muted', 'Pastel'], 'Neutral');
        e.contrast = pickTag(tags, ['HighC', 'MedC', 'LowC'], 'Med');
      }

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
          (e.vibe_tags || []).join(' ')
        ].join(' ').toLowerCase();
      }

      function applyDensity() {
        const v = densitySel.value || '1.0';
        document.documentElement.style.setProperty('--scale', v);
        const tw = v >= 1.2 ? '190px' : v <= 0.9 ? '140px' : '160px';
        document.documentElement.style.setProperty('--thumb-w', tw);
      }

      function applyView() {
        const view = viewSel.value || 'focus';
        document.body.dataset.view = view;
        if (view === 'gallery') {
          groupSel.value = 'none';
          groupSel.disabled = true;
        } else {
          groupSel.disabled = false;
        }
      }

      function makeOption(value, label) {
        const o = document.createElement('option');
        o.value = value;
        o.textContent = label;
        return o;
      }

      function renderPalette(container, colors) {
        container.textContent = '';
        if (!colors || !colors.length) return;
        for (const c of colors) {
          const s = document.createElement('span');
          s.style.background = c;
          container.appendChild(s);
        }
      }

      function ensureObserver() {
        if (observer) return;
        if (!('IntersectionObserver' in window)) return;
        observer = new IntersectionObserver(entries => {
          for (const entry of entries) {
            if (!entry.isIntersecting) continue;
            const img = entry.target;
            if (img.dataset.src && !img.src) img.src = img.dataset.src;
            observer.unobserve(img);
          }
        }, { root: null, rootMargin: '240px' });
      }

      function attachLazy(img) {
        if (!img.dataset.src) return;
        if (!('IntersectionObserver' in window)) {
          img.src = img.dataset.src;
          return;
        }
        ensureObserver();
        observer.observe(img);
      }

      function setPreview(e) {
        if (!e) return;
        const pid = e.profile_id;
        const s = scores.get(pid);
        const cr = (s && typeof s.contrast_ratio === 'number') ? s.contrast_ratio.toFixed(2) : '';
        previewTitle.textContent = `${e.visible_name} - ${pid}`;
        previewHint.textContent = `type=${e.type} | vibe=${e.vibe_name} | tags=${(e.vibe_tags||[]).join(', ')} | bg=${e.background||''} | fg=${e.foreground||''}${cr ? ' | CR=' + cr : ''}`;
        previewImg.src = `${SCREENS_DIR}/${pid}.png`;
        openImg.href = `${SCREENS_DIR}/${pid}.png`;
        const rel = (e.path || '').replace('mate-terminal/schemes/', '');
        openScheme.href = `${SCHEMES_ROOT}${rel}`;
        renderPalette(previewPal, e.palette || []);
        copyId.onclick = async () => {
          try { await navigator.clipboard.writeText(pid); } catch (_) {}
        };
      }

      function updateSelection() {
        const els = rowsEl.querySelectorAll('.row');
        els.forEach((el, idx) => el.classList.toggle('sel', idx === selectedIndex));
      }

      function updateCount() {
        countEl.textContent = `${Math.min(renderedCount, filtered.length).toLocaleString()} / ${filtered.length.toLocaleString()} (of ${allEntries.length.toLocaleString()})`;
      }

      function disconnectListObserver() {
        if (listObserver) listObserver.disconnect();
        listObserver = null;
      }

      function attachSentinel(onHit, root) {
        disconnectListObserver();
        if (!('IntersectionObserver' in window)) return;
        const sentinel = document.getElementById('sentinel');
        if (!sentinel) return;
        listObserver = new IntersectionObserver((entries) => {
          for (const ent of entries) {
            if (!ent.isIntersecting) continue;
            onHit();
            break;
          }
        }, { root, rootMargin: '900px 0px' });
        listObserver.observe(sentinel);
      }

      function appendFocusPage(setupObserver) {
        const end = Math.min(filtered.length, renderedCount + PAGE_SIZE);
        const frag = document.createDocumentFragment();
        for (let i = renderedCount; i < end; i++) {
          frag.appendChild(renderRow(filtered[i], i));
        }
        let sentinel = document.getElementById('sentinel');
        if (!sentinel) {
          sentinel = document.createElement('div');
          sentinel.id = 'sentinel';
          sentinel.style.height = '1px';
        } else {
          sentinel.remove();
        }
        rowsEl.appendChild(frag);
        rowsEl.appendChild(sentinel);
        renderedCount = end;
        updateCount();
        updateSelection();
        if (setupObserver) {
          attachSentinel(() => {
            if (renderedCount < filtered.length) appendFocusPage(false);
            updateCount();
          }, rowsEl);
        }
      }

      function appendGalleryPage(setupObserver) {
        const end = Math.min(filtered.length, renderedCount + PAGE_SIZE);
        const frag = document.createDocumentFragment();
        for (let i = renderedCount; i < end; i++) {
          frag.appendChild(renderCard(filtered[i]));
        }
        let sentinel = document.getElementById('sentinel');
        if (!sentinel) {
          sentinel = document.createElement('div');
          sentinel.id = 'sentinel';
          sentinel.style.height = '1px';
        } else {
          sentinel.remove();
        }
        rowsEl.appendChild(frag);
        rowsEl.appendChild(sentinel);
        renderedCount = end;
        updateCount();
        if (setupObserver) {
          attachSentinel(() => {
            if (renderedCount < filtered.length) appendGalleryPage(false);
            updateCount();
          }, null);
        }
      }

      function ensureRendered(index) {
        const view = viewSel.value || 'focus';
        const groupKey = groupSel.value || 'none';
        if (view !== 'focus' || groupKey !== 'none') return;
        while (index >= renderedCount && renderedCount < filtered.length) {
          appendFocusPage(false);
        }
      }

      function renderRow(e, i) {
        const row = document.createElement('div');
        row.className = 'row' + (i === selectedIndex ? ' sel' : '');
        row.tabIndex = 0;
        row.dataset.i = String(i);

        const thumb = document.createElement('img');
        thumb.className = 'thumb';
        thumb.alt = `${e.visible_name} (${e.profile_id})`;
        thumb.loading = 'lazy';
        thumb.dataset.src = `${THUMBS_DIR}/${e.profile_id}.jpg`;
        thumb.onerror = () => { thumb.classList.add('broken'); };
        attachLazy(thumb);

        const info = document.createElement('div');
        const title = document.createElement('div');
        title.className = 'title';
        title.textContent = e.visible_name;

        const sub = document.createElement('div');
        sub.className = 'sub';
        const s = scores.get(e.profile_id);
        const cr = (s && typeof s.contrast_ratio === 'number') ? `CR=${s.contrast_ratio.toFixed(2)}` : '';
        const pid = document.createElement('code');
        pid.textContent = e.profile_id;
        const type = document.createElement('span');
        type.textContent = e.type;
        const vibe = document.createElement('span');
        vibe.textContent = e.vibe_name;
        sub.appendChild(pid);
        sub.appendChild(type);
        sub.appendChild(vibe);
        if (cr) {
          const crEl = document.createElement('span');
          crEl.textContent = cr;
          sub.appendChild(crEl);
        }

        const pal = document.createElement('div');
        pal.className = 'pal';
        pal.style.backgroundImage = palGradient(e.palette || []);

        info.appendChild(title);
        info.appendChild(sub);
        info.appendChild(pal);

        const pinBtn = document.createElement('button');
        pinBtn.className = 'pinBtn' + (pinned.includes(e.profile_id) ? ' active' : '');
        pinBtn.textContent = pinned.includes(e.profile_id) ? 'Pinned' : 'Pin';
        pinBtn.addEventListener('click', ev => {
          ev.stopPropagation();
          togglePin(e.profile_id);
        });

        row.appendChild(thumb);
        row.appendChild(info);
        row.appendChild(pinBtn);

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
        return row;
      }

      function renderCard(e) {
        const card = document.createElement('div');
        card.className = 'row';
        const thumb = document.createElement('img');
        thumb.className = 'thumb';
        thumb.alt = `${e.visible_name} (${e.profile_id})`;
        thumb.loading = 'lazy';
        thumb.dataset.src = `${THUMBS_DIR}/${e.profile_id}.jpg`;
        thumb.onerror = () => { thumb.classList.add('broken'); };
        attachLazy(thumb);

        const info = document.createElement('div');
        const title = document.createElement('div');
        title.className = 'title';
        title.textContent = e.visible_name;

        const sub = document.createElement('div');
        sub.className = 'sub';
        sub.textContent = `${e.type} | ${e.vibe_name}`;

        const pal = document.createElement('div');
        pal.className = 'pal';
        pal.style.backgroundImage = palGradient(e.palette || []);

        const pinBtn = document.createElement('button');
        pinBtn.className = 'pinBtn' + (pinned.includes(e.profile_id) ? ' active' : '');
        pinBtn.textContent = pinned.includes(e.profile_id) ? 'Pinned' : 'Pin';
        pinBtn.addEventListener('click', ev => {
          ev.stopPropagation();
          togglePin(e.profile_id);
        });

        info.appendChild(title);
        info.appendChild(sub);
        info.appendChild(pal);

        card.appendChild(thumb);
        card.appendChild(info);
        card.appendChild(pinBtn);
        card.addEventListener('click', () => {
          setPreview(e);
        });
        return card;
      }

      function groupOrderFor(key, types) {
        if (key === 'type') return types;
        if (key === 'lightness') return LIGHTNESS;
        if (key === 'temperature') return TEMPS;
        if (key === 'vividness') return VIVIDNESS;
        if (key === 'contrast') return CONTRAST;
        return [];
      }

      function renderList(types) {
        rowsEl.textContent = '';
        renderedCount = 0;
        disconnectListObserver();
        const view = viewSel.value || 'focus';
        if (view === 'gallery') {
          appendGalleryPage(true);
          lockEl.textContent = '';
          return;
        }

        const groupKey = groupSel.value || 'none';
        if (groupKey === 'none') {
          appendFocusPage(true);
        } else {
          const groups = new Map();
          for (const e of filtered) {
            const key = e[groupKey] || 'Other';
            if (!groups.has(key)) groups.set(key, []);
            groups.get(key).push(e);
          }
          const order = groupOrderFor(groupKey, types);
          const keys = order.length ? order.filter(k => groups.has(k)) : Array.from(groups.keys());
          let index = 0;
          for (const k of keys) {
            const head = document.createElement('div');
            head.className = 'groupHead';
            head.textContent = `${k} (${groups.get(k).length})`;
            rowsEl.appendChild(head);
            for (const e of groups.get(k)) {
              rowsEl.appendChild(renderRow(e, index));
              index += 1;
            }
          }
        }
        updateCount();
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

      function updateFilterButtons(base) {
        const countBy = key => {
          const map = new Map();
          for (const e of base) {
            const v = e[key] || 'Other';
            map.set(v, (map.get(v) || 0) + 1);
          }
          return map;
        };
        const lightCounts = countBy('lightness');
        const tempCounts = countBy('temperature');
        const vividCounts = countBy('vividness');
        const contrastCounts = countBy('contrast');

        renderFilterRow(filterLightEl, 'lightness', LIGHTNESS, lightCounts);
        renderFilterRow(filterTempEl, 'temperature', TEMPS, tempCounts);
        renderFilterRow(filterVividEl, 'vividness', VIVIDNESS, vividCounts);
        renderFilterRow(filterContrastEl, 'contrast', CONTRAST, contrastCounts);
      }

      function renderFilterRow(container, key, values, counts) {
        container.textContent = '';
        for (const v of values) {
          const btn = document.createElement('button');
          btn.className = 'filterBtn' + (filters[key] === v ? ' active' : '');
          const count = counts.get(v) || 0;
          btn.textContent = v;
          const span = document.createElement('span');
          span.className = 'count';
          span.textContent = String(count);
          btn.appendChild(span);
          btn.addEventListener('click', () => {
            filters[key] = (filters[key] === v ? '' : v);
            applyFilters();
          });
          container.appendChild(btn);
        }
      }

      function renderOverview(base) {
        const counts = {};
        for (const l of LIGHTNESS) {
          counts[l] = {};
          for (const t of TEMPS) counts[l][t] = 0;
        }
        for (const e of base) {
          counts[e.lightness][e.temperature] += 1;
        }
        overviewEl.textContent = '';
        const head = document.createElement('div');
        head.className = 'overviewCell head';
        head.textContent = '';
        overviewEl.appendChild(head);
        for (const t of TEMPS) {
          const col = document.createElement('div');
          col.className = 'overviewCell head';
          col.textContent = t;
          overviewEl.appendChild(col);
        }
        for (const l of LIGHTNESS) {
          const rowHead = document.createElement('div');
          rowHead.className = 'overviewCell head';
          rowHead.textContent = l;
          overviewEl.appendChild(rowHead);
          for (const t of TEMPS) {
            const btn = document.createElement('div');
            const active = filters.lightness === l && filters.temperature === t;
            btn.className = 'overviewCell btn' + (active ? ' active' : '');
            const count = counts[l][t] || 0;
            btn.innerHTML = `<div class=\"count\">${count}</div><div class=\"label\">${l}/${t}</div>`;
            btn.addEventListener('click', () => {
              if (filters.lightness === l && filters.temperature === t) {
                filters.lightness = '';
                filters.temperature = '';
              } else {
                filters.lightness = l;
                filters.temperature = t;
              }
              applyFilters();
            });
            overviewEl.appendChild(btn);
          }
        }
      }

      function togglePin(pid) {
        const idx = pinned.indexOf(pid);
        if (idx >= 0) {
          pinned.splice(idx, 1);
        } else if (pinned.length < pinLimit) {
          pinned.push(pid);
        }
        renderCompare();
        renderList(typesCache);
      }

      function renderCompare() {
        compareEl.textContent = '';
        if (!pinned.length) {
          const empty = document.createElement('div');
          empty.className = 'hintSmall';
          empty.textContent = 'No pinned themes yet.';
          compareEl.appendChild(empty);
          return;
        }
        for (const pid of pinned) {
          const e = entryById.get(pid);
          if (!e) continue;
          const item = document.createElement('div');
          item.className = 'compareItem';
          const img = document.createElement('img');
          img.src = `${SCREENS_DIR}/${pid}.png`;
          img.alt = pid;
          img.onerror = () => { img.classList.add('broken'); };
          const name = document.createElement('div');
          name.className = 'name';
          name.textContent = e.visible_name;
          const btn = document.createElement('button');
          btn.textContent = 'Remove';
          btn.addEventListener('click', () => togglePin(pid));
          item.appendChild(img);
          item.appendChild(name);
          item.appendChild(btn);
          compareEl.appendChild(item);
        }
      }

      function applyFilters() {
        const needle = norm(q.value.trim());
        const t = typeSel.value || '';
        const base = allEntries.filter(e => {
          if (t && e.type !== t) return false;
          if (needle && !entrySearch(e).includes(needle)) return false;
          return true;
        });
        updateFilterButtons(base);
        renderOverview(base);

        filtered = base.filter(e => {
          if (filters.lightness && e.lightness !== filters.lightness) return false;
          if (filters.temperature && e.temperature !== filters.temperature) return false;
          if (filters.vividness && e.vividness !== filters.vividness) return false;
          if (filters.contrast && e.contrast !== filters.contrast) return false;
          return true;
        });
        applySort();
        selectedIndex = Math.min(selectedIndex, Math.max(0, filtered.length - 1));
        renderList(typesCache);
      }

      function handleKeys(ev) {
        if (!filtered.length || viewSel.value === 'gallery') return;
        if (ev.key === 'ArrowDown') {
          selectedIndex = Math.min(filtered.length - 1, selectedIndex + 1);
          locked = true;
          lockEl.textContent = 'locked (click a row to unlock)';
          ensureRendered(selectedIndex);
          updateSelection();
          setPreview(filtered[selectedIndex]);
          rowsEl.querySelectorAll('.row')[selectedIndex]?.scrollIntoView({block:'nearest'});
          ev.preventDefault();
        } else if (ev.key === 'ArrowUp') {
          selectedIndex = Math.max(0, selectedIndex - 1);
          locked = true;
          lockEl.textContent = 'locked (click a row to unlock)';
          ensureRendered(selectedIndex);
          updateSelection();
          setPreview(filtered[selectedIndex]);
          rowsEl.querySelectorAll('.row')[selectedIndex]?.scrollIntoView({block:'nearest'});
          ev.preventDefault();
        } else if (ev.key === 'Escape') {
          locked = false;
          lockEl.textContent = 'hover previews';
        }
      }

      let typesCache = [];
      const entryById = new Map();

      async function load() {
        const inlineIndex = readInlineJson('data-index');
        const inlineScores = readInlineJson('data-scores');
        const idx = inlineIndex || await (await fetch(INDEX_URL)).json();
        allEntries = idx.entries || [];
        for (const e of allEntries) {
          deriveProps(e);
          entryById.set(e.profile_id, e);
        }
        if (inlineScores) {
          for (const r of (inlineScores.rows || [])) scores.set(r.profile_id, r);
        } else {
          try {
            const s = await (await fetch(SCORES_URL)).json();
            for (const r of (s.rows || [])) scores.set(r.profile_id, r);
          } catch (_) {}
        }

        typesCache = Array.from(new Set(allEntries.map(e => e.type))).sort();
        typeSel.appendChild(makeOption('', `All types (${typesCache.length})`));
        for (const t of typesCache) typeSel.appendChild(makeOption(t, t));

        sortSel.appendChild(makeOption('name', 'Sort: name'));
        sortSel.appendChild(makeOption('type', 'Sort: type'));
        sortSel.appendChild(makeOption('contrast', 'Sort: contrast (high to low)'));
        sortSel.appendChild(makeOption('spread', 'Sort: palette spread (high to low)'));
        sortSel.appendChild(makeOption('bg_sat_low', 'Sort: bg saturation (low to high)'));

        groupSel.appendChild(makeOption('none', 'Group: none'));
        groupSel.appendChild(makeOption('type', 'Group: type'));
        groupSel.appendChild(makeOption('lightness', 'Group: lightness'));
        groupSel.appendChild(makeOption('temperature', 'Group: temperature'));
        groupSel.appendChild(makeOption('vividness', 'Group: vividness'));
        groupSel.appendChild(makeOption('contrast', 'Group: contrast'));
        groupSel.value = 'lightness';

        densitySel.appendChild(makeOption('0.9', 'Density: tight'));
        densitySel.appendChild(makeOption('1.0', 'Density: normal'));
        densitySel.appendChild(makeOption('1.2', 'Density: comfy'));
        densitySel.appendChild(makeOption('1.35', 'Density: huge'));
        densitySel.value = '1.0';
        applyDensity();

        viewSel.appendChild(makeOption('focus', 'View: focus + preview'));
        viewSel.appendChild(makeOption('gallery', 'View: gallery'));
        viewSel.value = 'focus';
        applyView();

        q.addEventListener('input', applyFilters);
        typeSel.addEventListener('change', applyFilters);
        sortSel.addEventListener('change', applyFilters);
        groupSel.addEventListener('change', applyFilters);
        densitySel.addEventListener('change', () => { applyDensity(); renderList(typesCache); });
        viewSel.addEventListener('change', () => { applyView(); renderList(typesCache); });
        window.addEventListener('keydown', handleKeys);
        clearFiltersBtn.addEventListener('click', () => {
          filters.lightness = '';
          filters.temperature = '';
          filters.vividness = '';
          filters.contrast = '';
          applyFilters();
        });
        clearCompareBtn.addEventListener('click', () => {
          pinned.splice(0, pinned.length);
          renderCompare();
          renderList(typesCache);
        });

        previewImg.onerror = () => {
          previewHint.textContent = `missing screenshot: ${previewImg.src}`;
        };

        renderCompare();
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


def safe_json(text: str) -> str:
    return text.replace("</", "<\\/")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build a static HTML showcase page (overview + list + preview)."
    )
    parser.add_argument("--index-json", default="docs/mateswatch-index.json")
    parser.add_argument("--scores-json", default="docs/mateswatch-scheme-scores.json")
    parser.add_argument("--out-dir", default="site")
    parser.add_argument("--screens-dir", default="screens")
    args = parser.parse_args()

    idx_path = Path(args.index_json)
    idx_text = idx_path.read_text(encoding="utf-8")
    idx = json.loads(idx_text)
    total = idx.get("count", 0)

    scores_path = Path(args.scores_json)
    scores_text = scores_path.read_text(encoding="utf-8") if scores_path.exists() else ""

    out_dir = Path(args.out_dir)
    data_dir = out_dir / "data"
    data_dir.mkdir(parents=True, exist_ok=True)

    (data_dir / "mateswatch-index.json").write_text(
        json.dumps(idx, separators=(",", ":")) + "\n", encoding="utf-8"
    )
    if scores_text:
        (data_dir / "mateswatch-scheme-scores.json").write_text(
            scores_text, encoding="utf-8"
        )

    inline_index = safe_json(json.dumps(idx, separators=(",", ":")))
    inline_scores = ""
    if scores_text:
        try:
            inline_scores = safe_json(
                json.dumps(json.loads(scores_text), separators=(",", ":"))
            )
        except json.JSONDecodeError:
            inline_scores = ""

    meta = f"{total} themes | overview map + filters | pin to compare | arrows to navigate"

    inline_index_tag = (
        f"<script type=\"application/json\" id=\"data-index\">{inline_index}</script>"
    )
    inline_scores_tag = (
        f"<script type=\"application/json\" id=\"data-scores\">{inline_scores}</script>"
        if inline_scores
        else ""
    )

    html = (
        HTML.replace("@@META@@", meta)
        .replace("@@SCREENS_DIR@@", args.screens_dir)
        .replace("@@INLINE_INDEX@@", inline_index_tag)
        .replace("@@INLINE_SCORES@@", inline_scores_tag)
    )

    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "index.html").write_text(html, encoding="utf-8")

    screens_path = Path(args.screens_dir)
    if not screens_path.is_absolute():
        screens_path = out_dir / screens_path
    if not screens_path.exists():
        print(
            f"warning: screenshots not found at {screens_path} (page will show missing images)",
            file=sys.stderr,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
