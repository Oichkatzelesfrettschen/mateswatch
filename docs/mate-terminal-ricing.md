# MATE Terminal ricing (what you can actually theme)

MATE Terminal is a GTK+ 3 app backed by VTE; most “ricing” is controlled by
GSettings/dconf profile keys, plus whatever your GTK theme/compositor does.

## Key idea: profiles are the unit of theming

Profiles live under:

- `/org/mate/terminal/profiles/<profile-id>/`

MATE Terminal only *recognizes* profiles listed in:

- `gsettings get org.mate.terminal.global profile-list`

## Quick commands

List known profiles:

```sh
gsettings get org.mate.terminal.global profile-list
```

Dump a profile:

```sh
dconf dump /org/mate/terminal/profiles/<profile-id>/
```

Set a single profile key (relocatable schema):

```sh
gsettings set org.mate.terminal.profile:/org/mate/terminal/profiles/<profile-id>/ background-type 'transparent'
```

## Theme knobs (per-profile)

These come directly from `org.mate.terminal.profile` (see upstream schema in MATE Terminal source).

**Colors**
- `use-theme-colors` (when true, GTK theme provides fg/bg)
- `foreground-color`, `background-color`
- `palette` (16-color palette used by ANSI apps)
- `bold-color`, `bold-color-same-as-fg`
- `cursor-color` (stored in dconf on this machine)

**Transparency / background images**
- `background-type`: `solid`, `transparent`, `image`
- `background-image`: path to an image file
- `scroll-background`: scroll image with text
- `background-darkness`: how much to darken the image (schema notes this behaves like a boolean in practice)

**Text + cursor**
- `font` / `use-system-font`
- `allow-bold`
- `cursor-shape`: `block`, `ibeam`, `underline`
- `cursor-blink-mode`: `system`, `on`, `off`

**UX and behavior**
- `scrollbar-position`: `left`, `right`, `hidden`
- `scrollback-lines` / `scrollback-unlimited`
- `scroll-on-keystroke`, `scroll-on-output`
- `silent-bell`
- `use-urls`, `word-chars`

**Shell + command**
- `login-shell`
- `use-custom-command` / `custom-command`

## Compositor-based ricing (shadows/blur)

For true transparency and effects like blur:

1. Set the profile to transparent:
   ```sh
   gsettings set org.mate.terminal.profile:/org/mate/terminal/profiles/<profile-id>/ background-type 'transparent'
   ```
2. Use a compositor (e.g. picom) rules to add blur/shadow for the `mate-terminal` window.

## CLI gotchas: `--profile` matches visible-name

`mate-terminal --profile=...` matches the profile’s `visible-name`, not the profile id.

Example: our Gogh imports have ids like `gogh-atom` but `visible-name` like `Gogh: Atom`.

Live test helper (temporarily appends ids to `profile-list` and launches):

- `scripts/test-mate-terminal-profiles-live.sh`

## Source pointers

Upstream `mate-terminal` repository:

- GSettings schema: `src/org.mate.terminal.gschema.xml.in`
- CLI profile selection: `src/terminal-app.c` (visible-name vs id)

