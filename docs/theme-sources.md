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

## Kitty / Alacritty / Base16 / WezTerm

This repo also vendors converted MATE Terminal profiles generated from these upstream theme corpuses:

- kitty-themes (MIT): `https://github.com/dexpota/kitty-themes`
  - Attribution: `sources/kitty-themes/`
  - Converted profiles: `mate-terminal/schemes/kitty/`
- alacritty-themes (MIT): `https://github.com/rajasegar/alacritty-themes`
  - Attribution: `sources/alacritty-themes/`
  - Converted profiles: `mate-terminal/schemes/alacritty/`
- tinted-shell (MIT-style): `https://github.com/tinted-theming/tinted-shell`
  - Attribution: `sources/tinted-shell/`
  - Converted profiles: `mate-terminal/schemes/tinted/base16/` and `mate-terminal/schemes/tinted/base24/`
- WezTerm built-ins (MIT): `https://github.com/wez/wezterm`
  - Attribution: `sources/wezterm/`
  - Converted profiles: `mate-terminal/schemes/wezterm/`

## Konsole

Konsole `.colorscheme` files are converted into MATE Terminal profiles via:

- `scripts/import-konsole-colorschemes.py`

Vendored Konsole sources with clear MIT licensing include:

- Dracula Konsole: `sources/dracula/konsole/` → `mate-terminal/schemes/konsole/brands/`
- Catppuccin Konsole: `sources/catppuccin/konsole/` → `mate-terminal/schemes/konsole/brands/`
- Community Konsole bundles: `sources/konsole-community/` → `mate-terminal/schemes/konsole/community*/`

## Official Dracula / Catppuccin (“brands”)

Some themes have “official” upstream implementations per terminal. This repo vendors a minimal, licensed subset of those sources and converts them into MATE Terminal profiles:

- Dracula (MIT): `sources/dracula/{gnome-terminal,kitty,wezterm}/` → `mate-terminal/schemes/brands/dracula/` (type `DRC`)
- Catppuccin (MIT): `sources/catppuccin/{gnome-terminal,kitty,wezterm,palette}/` → `mate-terminal/schemes/brands/catppuccin/` (type `CTP`)

Generator:

```sh
./scripts/import-official-brands.py
```

## Dracula Pro (commercial)

Dracula Pro is a paid product and is not vendored here. See `docs/dracula-pro.md`.

## Converting locally-installed schemes

Convert Tilix JSON schemes into minimal MATE Terminal `.dconf` snippets (generated output is gitignored):

```sh
./scripts/sync-tilix-to-mate-terminal.py --output-dir generated/mate-terminal/tilix
```

Import a directory of `.dconf` profiles into your user dconf:

```sh
./scripts/import-mate-terminal-profiles-dir.py generated/mate-terminal/tilix
```
