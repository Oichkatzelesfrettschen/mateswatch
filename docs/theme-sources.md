# Theme sources (local + upstream)

This repo aims to keep a “cleanroom” boundary:

- Only vendor theme files when their license is clear.
- Otherwise, convert locally-installed schemes into MATE Terminal profiles and keep the generated output out of git.

## Tilix schemes on this machine

Tilix scheme JSON files live in:

- System: `/usr/share/tilix/schemes/*.json`
- User: `~/.config/tilix/schemes/*.json`

On this machine, `/usr/share/tilix/schemes` is provided by the Arch/AUR package:

- `tilix-themes-git` → `https://github.com/storm119/Tilix-Themes` (license unknown)

This repo vendors `tilix/schemes/atom.json` byte-identical to the system `atom.json` for reproducibility.

## Gogh

Gogh is a large theme collection with a clear MIT license:

- Upstream: `https://github.com/Gogh-Co/Gogh`
- Vendored license + attribution: `sources/gogh/`
- Converted MATE Terminal profiles: `mate-terminal/schemes/gogh/`

## Converting locally-installed schemes

Convert Tilix JSON schemes into minimal MATE Terminal `.dconf` snippets (generated output is gitignored):

```sh
./scripts/sync-tilix-to-mate-terminal.py --output-dir generated/mate-terminal/tilix
```

Import a directory of `.dconf` profiles into your user dconf:

```sh
./scripts/import-mate-terminal-profiles-dir.py generated/mate-terminal/tilix
```
