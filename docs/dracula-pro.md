# Dracula Pro (licensing + what mateswatch can/can’t ship)

Dracula **(classic)** is an open theme family with many official implementations (MIT license). This repo vendors and converts those official, MIT-licensed sources (see `docs/theme-sources.md`).

Dracula **Pro** is a *commercial* product (paid download). As such:

- It is **not** open-licensed.
- Even if you personally purchased it, redistribution is typically restricted by the vendor’s terms.

## What this means for mateswatch

- mateswatch will **not vendor** Dracula Pro assets or ship them in releases.
- If you have Dracula Pro files locally, mateswatch can support a “cleanroom/local-only” workflow:
  - convert the colors into MATE Terminal profiles under `generated/` (gitignored)
  - import into your user dconf with `mateswatch import ...`

If you want this, point me at the Dracula Pro format(s) you have on disk (e.g. a Terminal JSON, a WezTerm TOML, a kitty conf), and I’ll add a local-only importer that keeps those files out of git and out of release artifacts.

