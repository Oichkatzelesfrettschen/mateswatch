# Atom (Tilix + MATE Terminal themes)

This repository vendors the **Atom** color scheme for:

- Tilix terminal (formerly Terminix)
- MATE Terminal (via dconf profile)

It also includes “cleanroom” tooling to convert other theme sources into MATE Terminal profiles.

Local sources found on this machine:

- Tilix: `/usr/share/tilix/schemes/atom.json`
- MATE Terminal: imported into dconf at `/org/mate/terminal/profiles/Atom/`

## Colors

- Background: `#161719`
- Foreground: `#c5c8c6`
- ANSI palette (0–15):
  - 0: `#000000`
  - 1: `#fd5ff1`
  - 2: `#87c38a`
  - 3: `#ffd7b1`
  - 4: `#85befd`
  - 5: `#b9b6fc`
  - 6: `#85befd`
  - 7: `#e0e0e0`
  - 8: `#000000`
  - 9: `#fd5ff1`
  - 10: `#94fa36`
  - 11: `#f5ffa8`
  - 12: `#96cbfe`
  - 13: `#b9b6fc`
  - 14: `#85befd`
  - 15: `#e0e0e0`

## Install

### Tilix

User-only install (recommended):

```sh
mkdir -p ~/.config/tilix/schemes
cp tilix/schemes/atom.json ~/.config/tilix/schemes/
```

Then restart Tilix and select the scheme in:
`Preferences → Profiles → Colors → Color scheme → Atom`.

### MATE Terminal

Import the profile into dconf:

```sh
./scripts/mate-terminal-import-profile.sh Atom mate-terminal/schemes/profile_Atom.dconf
gsettings set org.mate.terminal.global profile-list "['default','Dracula','Atom']"
```

Then select the profile in:
`Edit → Profiles… → Atom`, or launch directly with:

```sh
mate-terminal --profile=Atom
```

Note: `mate-terminal --profile=...` matches the profile’s `visible-name`, and profiles must be present in
`org.mate.terminal.global profile-list`.

More details:

- `docs/mate-terminal-color-schemes.md`
- `docs/mate-terminal-ricing.md`
- `docs/tilix-to-mate-terminal.md`
- `docs/theme-sources.md`

## Gogh (MIT-licensed theme corpus)

This repo vendors converted MATE Terminal profiles generated from Gogh:

- `docs/gogh-to-mate-terminal.md`
- `mate-terminal/schemes/gogh/`

## Bulk convert Tilix → MATE Terminal (generated, gitignored)

Generate MATE Terminal `.dconf` snippets from your installed Tilix schemes:

```sh
./scripts/sync-tilix-to-mate-terminal.py --output-dir generated/mate-terminal/tilix
```

Optionally import them into your dconf (adds profiles; does not touch `profile-list` unless asked):

```sh
./scripts/sync-tilix-to-mate-terminal.py --import --smoke-count 10
```

Cleanup bulk profiles later:

```sh
./scripts/reset-tilix-mate-terminal-profiles.sh
```

## Packaging

- Debian/LMDE `.deb` builder: `packaging/deb/build-deb.sh` (writes to `dist/`)
- Arch/CachyOS example: `packaging/arch/PKGBUILD`
- Notes: `docs/packaging.md`
