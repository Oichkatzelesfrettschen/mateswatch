# mateswatch

Terminal color schemes for **MATE Terminal** (dconf profiles) with a “cleanroom” conversion toolchain and an opinionated, scroll-friendly naming system.

Current corpus (vendored in this repo):

- **2260** MATE Terminal profiles under `mate-terminal/schemes/` (see `docs/mateswatch-stats.md`)
- Sources include: Gogh, WezTerm built-ins, tinted-shell Base16/Base24, kitty-themes, alacritty-themes, plus a small Konsole set

## Naming (dropdown-friendly)

Every profile’s `visible-name` is formatted like:

`TYPE VibeName — Tag·Tag·Tag·Tag — Original`

Example:

`GOG Neon Lime — Dark·HighC·Vivid·Neutral — Atom`

This keeps profiles clustered by **type** while still conveying “color-vibe” at a glance.

## Install / import (MATE Terminal)

List available profile IDs:

```sh
./scripts/mateswatch-import.py list
```

Import one profile into your user dconf, add it to profile-list, and set default:

```sh
./scripts/mateswatch-import.py import gogh-atom --add-to-profile-list --set-default
```

## Docs

- MATE Terminal profile keys + best practices: `docs/mate-terminal-color-schemes.md`
- Ricing knobs beyond colors: `docs/mate-terminal-ricing.md`
- Source attribution: `docs/theme-sources.md`
- Gogh corpus: `docs/gogh-to-mate-terminal.md`
- Stats/index: `docs/mateswatch-stats.md`, `docs/mateswatch-index.json`

## Packaging

- Arch/CachyOS example: `packaging/arch/PKGBUILD`
- Debian/LMDE build script: `packaging/deb/build-deb.sh`
