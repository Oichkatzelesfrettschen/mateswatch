# Atom (Tilix + MATE Terminal themes)

This repository vendors the **Atom** color scheme for:

- Tilix terminal (formerly Terminix)
- MATE Terminal (via dconf profile)

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

More details: `docs/mate-terminal-color-schemes.md`
