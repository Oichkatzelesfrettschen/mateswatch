# Gogh → MATE Terminal

This repository vendors *converted* MATE Terminal profiles generated from the Gogh theme collection.

- Upstream: `https://github.com/Gogh-Co/Gogh`
- License: MIT (see `sources/gogh/LICENSE`)
- Conversion tool: `scripts/import-gogh-to-mate-terminal.py`

## Regenerate the profiles

Clone Gogh (example):

```sh
git clone --depth 1 https://github.com/Gogh-Co/Gogh /tmp/gogh
```

Generate profiles into this repo:

```sh
./scripts/import-gogh-to-mate-terminal.py --gogh-dir /tmp/gogh --output-dir mate-terminal/schemes/gogh
```

## Import into your user profiles

Import all `.dconf` files in the directory into your dconf database:

```sh
./scripts/import-mate-terminal-profiles-dir.py mate-terminal/schemes/gogh
```

Note: MATE Terminal only recognizes profiles that are present in
`org.mate.terminal.global profile-list`. The integration test script temporarily
adds a profile id to that list before launching MATE Terminal.

For a single-profile workflow (recommended), use:

```sh
./scripts/mateswatch-import.py import gogh-atom --add-to-profile-list --set-default
```

## Live test (requires desktop session)

```sh
./scripts/test-mate-terminal-profiles-live.sh gogh-atom gogh-gruvbox-dark gogh-tokyo-night
```

## Cleanup

```sh
./scripts/reset-tilix-mate-terminal-profiles.sh
```
