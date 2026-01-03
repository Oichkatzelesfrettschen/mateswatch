# Showcase screenshots (Hello, world in C)

This repo can generate a screenshot per scheme showing:

- a classic `hello.c`
- the compile command
- syntax-highlighted source (palette-mapped ANSI)
- `./hello` output

Local run (sample):

```sh
dbus-run-session -- ./scripts/render-mateswatch-showcase.py --count 20 --seed 1
```

To increase readability (bigger font + fewer columns/rows), tweak:

```sh
dbus-run-session -- ./scripts/render-mateswatch-showcase.py \
  --font "Monospace 18" --geometry 92x26 --xvfb-size 1280x800
```

Outputs:

- Screenshots: `generated/showcase/screens/*.png`
- Logs (failures): `generated/showcase/logs/*.log`

## GitHub Pages

Run the `pages-showcase` workflow to generate screenshots for **all** themes (sharded) and deploy a low-click gallery to GitHub Pages:

- The left pane is a filterable list with a 16-color palette strip per theme.
- Hover previews in the right pane (click to lock; arrow keys to navigate).
- Each theme links to its screenshot and its `.dconf` for manual import.
