# Packaging notes (Arch/CachyOS + Debian/LMDE)

This repo is a theme pack + tooling: it vendors multiple upstream theme corpuses as **MATE Terminal dconf profile snippets** plus a helper command to import selected profiles.

## Arch / CachyOS / AUR (PKGBUILD)

On Arch-family distros (including CachyOS), the best-practice way to distribute this is **not a `.deb`**:

- Use a `PKGBUILD` and build with `makepkg` to produce `*.pkg.tar.zst`.
- Test builds in a clean chroot (devtools / `pkgctl build`) to avoid missing deps.
- Use `namcap` to lint both the `PKGBUILD` and the built package.
- Install files under `/usr/share/...` and user-facing helpers in `/usr/bin`.

This repo includes an example PKGBUILD at `packaging/arch/PKGBUILD`.

### “.deb packages on the AUR” (when you must)

The AUR does not host binary packages. If you want to distribute a `.deb` as an upstream release artifact (for Debian/Mint users), Arch users should still consume it via a **normal Arch package**.

If you *must* create an AUR package that installs from an upstream binary deliverable, Arch guidelines generally expect a `-bin` style package that:

- Downloads a release artifact in `source=()` (do not commit the binary to the AUR git repo).
- Verifies checksums in `sha256sums=()`.
- Extracts the archive in `package()` (for `.deb`, that means extracting `data.tar.*`).

This is appropriate for closed-source apps or when sources are not practically buildable, but it is usually unnecessary for a data-only theme repo like this one.

References:

- Arch Wiki: “Creating packages” (`https://wiki.archlinux.org/title/Creating_packages`)
- Arch Wiki: “PKGBUILD” (`https://wiki.archlinux.org/title/PKGBUILD`)
- Arch Wiki: “Arch package guidelines” (`https://wiki.archlinux.org/title/Arch_package_guidelines`)
- Arch Wiki: “AUR submission guidelines” (`https://wiki.archlinux.org/title/AUR_submission_guidelines`)

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

### Debian archive note (licensing)

The Atom scheme source this repo vendored was found on this machine via `tilix-themes-git` from `https://github.com/storm119/Tilix-Themes`, which does not ship an explicit license file. That makes it unsuitable for Debian main as-is.

For a Debian/Mint-friendly theme corpus with a clear license, see the MIT-licensed Gogh conversions in this repo (`docs/gogh-to-mate-terminal.md`).

### `.deb` artifact for releases

This repo includes a small, reproducible `.deb` builder at:

- `packaging/deb/build-deb.sh`

It creates an `all`-architecture `.deb` in `dist/` containing:

- Tilix scheme (legacy): `/usr/share/tilix/schemes/atom.json`
- MATE Terminal profile snippets: `/usr/share/mateswatch/mate-terminal/schemes/`
- Helper command: `/usr/bin/mateswatch`
- Documentation: `/usr/share/doc/mateswatch/`

Install on Debian/LMDE:

```sh
sudo dpkg -i dist/mateswatch_*.deb
mateswatch list
mateswatch import gogh-atom --add-to-profile-list --set-default
```
