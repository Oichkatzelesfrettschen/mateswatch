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

Outputs:

- Screenshots: `generated/showcase/screens/*.png`
- Logs (failures): `generated/showcase/logs/*.log`

## GitHub Pages

Run the `pages-showcase` workflow to generate screenshots for **all** themes (sharded) and deploy a searchable gallery to GitHub Pages.
