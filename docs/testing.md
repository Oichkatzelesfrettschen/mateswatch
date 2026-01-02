# Testing / linting mateswatch

## What we can test automatically

We can’t programmatically prove a theme “looks good”, but we *can* verify:

- Every `*.dconf` scheme file is syntactically valid for MATE Terminal
- Theme import into dconf works
- `mate-terminal` can launch a profile without errors (“No such profile”) in quick succession

## Lint + format tools

Recommended tools (already present on this machine):

- Python: `ruff`, `black`
- Shell: `shellcheck`, `shfmt`

Run:

```sh
./scripts/lint.sh
```

## Scheme validation

Validates every scheme file’s key set + 16-color palette formatting:

```sh
./scripts/test-schemes.sh
```

## Render fidelity (pixel-verified)

This is the closest we can get to “does it look right” automatically:

- Runs `mate-terminal` under `xvfb-run`
- Renders a fixed ANSI 16-color background block grid
- Screenshots the terminal window with ImageMagick `import` (uses `xdotool` when available)
- Samples pixels and verifies they match the scheme’s palette entries

Fast sample:

```sh
./scripts/test-mateswatch-render.py --count 20
```

Full corpus (slow):

```sh
./scripts/test-mateswatch-render.py --all --keep
```

## Live “does it launch” test (desktop required)

This imports schemes into **temporary** test profiles and launches `mate-terminal` quickly to ensure no errors.

Sample (fast):

```sh
./scripts/test-mateswatch-live.py --count 50
```

Full corpus (slow, thousands of windows):

```sh
./scripts/test-mateswatch-live.py --all
```
