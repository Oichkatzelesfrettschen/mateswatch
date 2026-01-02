# Tilix → MATE Terminal (cleanroom conversion)

Tilix stores color schemes as JSON files (typically in `/usr/share/tilix/schemes/` and `~/.config/tilix/schemes/`).

MATE Terminal stores per-profile settings in dconf under:

- `/org/mate/terminal/profiles/<profile-id>/`

This repo provides a deterministic conversion that:

- Reads installed Tilix JSON schemes from your machine
- Generates MATE Terminal profile snippets (`*.dconf`)
- Optionally imports them into your user’s dconf under a safe prefix (`tilix-` / `tilix-user-`)

## Licensing note

On many distros, `/usr/share/tilix/schemes/*.json` comes from third-party theme packs (not Tilix itself) and may have unclear licensing.

That’s why this repo treats locally-installed Tilix schemes as input-only and keeps generated MATE profiles out of git. See `docs/theme-sources.md`.

## Generate (no imports)

```sh
./scripts/sync-tilix-to-mate-terminal.py
```

Outputs go to `generated/mate-terminal/tilix/` (gitignored), including `manifest.json`.

## Import + validate

```sh
./scripts/sync-tilix-to-mate-terminal.py --import
```

This imports all generated profiles into:
`/org/mate/terminal/profiles/tilix-*/` and `/org/mate/terminal/profiles/tilix-user-*/`

## Smoke test (launch briefly)

```sh
./scripts/sync-tilix-to-mate-terminal.py --import --smoke-count 3 --smoke-timeout 4
```

## Cleanup (remove imported profiles)

```sh
./scripts/reset-tilix-mate-terminal-profiles.sh
```

Dry-run:

```sh
./scripts/reset-tilix-mate-terminal-profiles.sh --dry-run
```
