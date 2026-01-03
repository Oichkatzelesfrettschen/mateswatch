# Manual download + import (MATE Terminal profiles)

MATE Terminal themes in this repo are **dconf profile snippets**: one `*.dconf` per theme, stored under:

- `mate-terminal/schemes/**/<profile-id>.dconf`

You can download any single file from GitHub (or copy it off disk) and import it.

Note: **MATE Tweak** does not manage MATE Terminal profiles; these are imported via `dconf`/`gsettings` or via the `mateswatch` helper.

## Option A: use `mateswatch` (recommended)

After installing the `.deb`, import a theme id by name:

```sh
mateswatch list | head
mateswatch import gogh-atom --add-to-profile-list --set-default
```

## Option B: download one file and import manually

1) Pick a profile id (use the filename stem), e.g. `gogh-atom` from:

- `mate-terminal/schemes/gogh/gogh-atom.dconf`

2) Import it into dconf:

```sh
dconf load /org/mate/terminal/profiles/gogh-atom/ < gogh-atom.dconf
```

3) Add it to the profile dropdown list:

```sh
current="$(gsettings get org.mate.terminal.global profile-list)"
echo "$current"
```

Append `gogh-atom` to that list (don’t delete your existing ids).

## Option C: export “full” dconf dumps (portable files)

Some tools/scripts prefer a dconf dump that can be loaded at `/` (root), with a fully-qualified section.

Generate one:

```sh
./scripts/mateswatch-import.py export gogh-atom --format full --out gogh-atom.full.dconf
```

Import it:

```sh
dconf load / < gogh-atom.full.dconf
```

