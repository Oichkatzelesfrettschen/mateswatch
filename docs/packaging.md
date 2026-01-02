# Packaging notes (Arch/CachyOS + Debian/LMDE)

This repo is a data-only theme (Tilix JSON + MATE Terminal dconf profile) plus small helper scripts.

## Arch / CachyOS / AUR (PKGBUILD)

On Arch-family distros (including CachyOS), the best-practice way to distribute this is **not a `.deb`**:

- Use a `PKGBUILD` and build with `makepkg` to produce `*.pkg.tar.zst`.
- Test builds in a clean chroot (devtools / `pkgctl build`) to avoid missing deps.
- Use `namcap` to lint both the `PKGBUILD` and the built package.
- Install files under `/usr/share/...` and user-facing helpers in `/usr/bin`.

This repo includes an example PKGBUILD at `packaging/arch/PKGBUILD`.

References:

- Arch Wiki: “Creating packages”
- Arch Wiki: “PKGBUILD”
- Arch Wiki: “Arch package guidelines”

## Debian / LMDE 7 (Debian 13 “trixie”) themes for MATE Terminal

### How MATE Terminal themes work

MATE Terminal stores “profiles” in dconf under:

- `/org/mate/terminal/profiles/<profile-id>/`

and a global list of available profiles in:

- `org.mate.terminal.global profile-list`

Because user dconf is user-owned state, a Debian package should generally **avoid mutating a user’s profile list automatically**. Instead:

- Ship the theme/profile file in `/usr/share/...`.
- Provide a helper command that users can run to import/enable it in their own dconf.

For more detail on the profile keys and color formats, see:

- `docs/mate-terminal-color-schemes.md`

### Runtime requirements (LMDE 7 / Debian 13)

To import and enable the theme in a running desktop session you typically need:

- `mate-terminal`
- `dconf-cli` (for `dconf`)
- `libglib2.0-bin` (for `gsettings`)

### `.deb` artifact for releases

This repo includes a small, reproducible `.deb` builder at:

- `packaging/deb/build-deb.sh`

It creates an `all`-architecture `.deb` in `dist/` containing:

- Tilix scheme: `/usr/share/tilix/schemes/atom.json`
- MATE Terminal profile: `/usr/share/mate-terminal/profiles/Atom.dconf`
- Helper command: `/usr/bin/mate-terminal-theme-atom-import`
- Documentation: `/usr/share/doc/mate-terminal-theme-atom/`

Install on Debian/LMDE:

```sh
sudo dpkg -i dist/mate-terminal-theme-atom_*.deb
mate-terminal-theme-atom-import --set-default
```

