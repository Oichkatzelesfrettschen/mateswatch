# MATE Terminal color schemes (profiles)

MATE Terminal stores its appearance settings as **profiles** in dconf (GSettings).

This repo includes an **Atom** profile derived from the Tilix Atom palette:
`mate-terminal/schemes/profile_Atom.dconf`.

## Where settings live

- Global MATE Terminal keys: `org.mate.terminal.global`
- Per-profile keys (dconf path): `/org/mate/terminal/profiles/<profile-id>/`

The global keys include:

- `default-profile` (the profile id used by default)
- `profile-list` (profile ids shown/available in the UI)

On this machine, profiles currently include:

```sh
dconf list /org/mate/terminal/profiles/
```

## How colors are represented

MATE Terminal typically uses **16-bit-per-channel** hex colors for the main scheme keys:

- `background-color`: `#RRRRGGGGBBBB`
- `foreground-color`: `#RRRRGGGGBBBB`
- `bold-color`: `#RRRRGGGGBBBB`
- `palette`: a single string of 16 colors separated by `:`, each `#RRRRGGGGBBBB`

Example (Dracula background `#282a36` → `#28282A2A3636`).

Some keys may still use 8-bit `#RRGGBB` (e.g. `cursor-color` on this machine), so when
authoring a portable profile, prefer what your local `dconf dump` shows.

## Import / export

Export a profile:

```sh
dconf dump /org/mate/terminal/profiles/<profile-id>/
```

Import a profile:

```sh
dconf load /org/mate/terminal/profiles/<profile-id>/ < profile.dconf
```

For convenience, this repo provides:

```sh
./scripts/mate-terminal-import-profile.sh Atom mate-terminal/schemes/profile_Atom.dconf
```

If the profile doesn’t show up in the UI, ensure it is listed in:

```sh
gsettings get org.mate.terminal.global profile-list
```

and add it if needed:

```sh
gsettings set org.mate.terminal.global profile-list "['default','Dracula','Atom']"
```

## Window/session config files (not themes)

MATE Terminal also supports saving and loading a *window/tab layout* file:

```sh
mate-terminal --save-config=/tmp/mate-terminal.ini
mate-terminal --load-config=/tmp/mate-terminal.ini
```

These files capture things like window geometry, working directory, and the `ProfileID`
used by a tab. They’re useful for session/workspace workflows, but they are not a
replacement for exporting/importing profile themes from dconf.

## Comparing profiles (extracting colors only)

For comparison, focus on the color-defining keys:

- `use-theme-colors`
- `background-color`
- `foreground-color`
- `palette`
- `bold-color` / `bold-color-same-as-fg`
- `cursor-color`

This repo includes a precomputed diff between your `default` profile colors and Atom:

- `mate-terminal/comparison/default_vs_atom_colors.diff`

## Best practices for MATE Terminal schemes

### 1) Decide your compatibility target

- **ANSI 16-color apps** (shell prompts, `ls`, many TUI tools): the 0–15 palette matters a lot.
- **256-color apps**: often map through the 16-color base; palette still matters.
- **Truecolor apps**: mostly care about background/foreground; palette is less critical.

Design the palette first, then tune foreground/background for readability.

### 2) Keep contrast high, but not harsh

- Avoid “pure black” backgrounds unless you really want the look; near-black reduces glare.
- Ensure foreground has comfortable contrast against the background for long sessions.
- Ensure selection/cursor remain visible across the palette (especially with transparency).

### 3) Make dark vs bright colors meaningfully different

Many terminal UIs rely on “bright” variants for emphasis. A good palette:

- Keeps hue identity between dark and bright variants (red stays red).
- Increases lightness/saturation for the bright half (8–15).
- Avoids making multiple colors indistinguishable (especially red/green, blue/cyan).

### 4) Don’t overuse “bold” as a color channel

MATE Terminal supports:

- `bold-color-same-as-fg=true`: bold is weight-only (recommended for portability).
- `bold-color-same-as-fg=false` + `bold-color=...`: bold can become a second foreground.

If you use a custom bold color, test prompts, manpages, and TUI apps; bold-as-color can
make emphasis unreadable or misleading.

### 5) Prefer solid backgrounds for shareable themes

`background-type='transparent'` and `background-darkness` depend on compositor and
wallpaper/background. They can look great locally, but are hard to reproduce and easy
to make unreadable.

If you want transparency:

- Start from a solid, readable scheme first.
- Apply transparency as a local preference (profile tweak), not as the “canonical” scheme.
- If using Marco (MATE’s window manager), compositing can affect transparency behavior.

### 6) Document the scheme in terms users recognize

When publishing a scheme, include:

- Background, foreground, and the 0–15 palette in `#RRGGBB` form
- Any “special” behavior: bold-color behavior, transparency expectations
- Import/export commands (dconf paths and gsettings profile-list notes)

## Other useful profile knobs (non-color)

These keys often matter as much as colors for “feel”:

- `font`, `use-system-font`
- `cursor-shape`, `cursor-blink-mode`
- `scrollback-lines`, `scrollback-unlimited`, `scrollbar-position`
- `silent-bell`
- `default-size-columns`, `default-size-rows`
- `title-mode`, `title`
- `use-urls`, `word-chars`

See what your profile is currently using via:

```sh
dconf dump /org/mate/terminal/profiles/<profile-id>/
```
