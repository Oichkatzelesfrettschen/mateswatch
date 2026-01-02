#!/usr/bin/env bash
set -euo pipefail

pkgname="mate-terminal-theme-atom"
version="$(cat VERSION)"
debrel="1"
debver="${version}-${debrel}"
arch="all"

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
outdir="${repo_root}/dist"

workdir="$(mktemp -d)"
trap 'rm -rf "${workdir}"' EXIT

root="${workdir}/root"
controldir="${workdir}/control"

mkdir -p "${root}/usr/share/tilix/schemes"
mkdir -p "${root}/usr/share/mate-terminal/profiles"
mkdir -p "${root}/usr/bin"
mkdir -p "${root}/usr/share/doc/${pkgname}"
mkdir -p "${controldir}"
mkdir -p "${outdir}"

install -m 0644 "${repo_root}/tilix/schemes/atom.json" \
  "${root}/usr/share/tilix/schemes/atom.json"
install -m 0644 "${repo_root}/mate-terminal/schemes/profile_Atom.dconf" \
  "${root}/usr/share/mate-terminal/profiles/Atom.dconf"
install -m 0755 "${repo_root}/packaging/deb/mate-terminal-theme-atom-import" \
  "${root}/usr/bin/mate-terminal-theme-atom-import"

install -m 0644 "${repo_root}/README.md" \
  "${root}/usr/share/doc/${pkgname}/README.md"
install -m 0644 "${repo_root}/docs/mate-terminal-color-schemes.md" \
  "${root}/usr/share/doc/${pkgname}/mate-terminal-color-schemes.md"
install -m 0644 "${repo_root}/docs/mate-terminal-ricing.md" \
  "${root}/usr/share/doc/${pkgname}/mate-terminal-ricing.md"
install -m 0644 "${repo_root}/docs/tilix-to-mate-terminal.md" \
  "${root}/usr/share/doc/${pkgname}/tilix-to-mate-terminal.md"
install -m 0644 "${repo_root}/docs/gogh-to-mate-terminal.md" \
  "${root}/usr/share/doc/${pkgname}/gogh-to-mate-terminal.md"
install -m 0644 "${repo_root}/docs/theme-sources.md" \
  "${root}/usr/share/doc/${pkgname}/theme-sources.md"
install -m 0644 "${repo_root}/docs/packaging.md" \
  "${root}/usr/share/doc/${pkgname}/packaging.md"

cat > "${root}/usr/share/doc/${pkgname}/README.Debian" <<'EOF'
This package ships the Atom theme as a profile file and a helper command.

To import/enable it for your user:

  mate-terminal-theme-atom-import --set-default

EOF

cat > "${root}/usr/share/doc/${pkgname}/copyright" <<'EOF'
Format: https://www.debian.org/doc/packaging-manuals/copyright-format/1.0/
Upstream-Name: Atom (Tilix/MATE Terminal color scheme)
Source: https://github.com/storm119/Tilix-Themes

Files: usr/share/tilix/schemes/atom.json usr/share/mate-terminal/profiles/Atom.dconf
Copyright: Unknown
License: UNKNOWN
 Comment:
  The upstream repository referenced above does not ship a license file at the
  time this repo vendored the Atom theme, so the license is not known here.

Files: usr/bin/mate-terminal-theme-atom-import
Copyright: 2026 eirikr
License: 0BSD
 Permission to use, copy, modify, and/or distribute this software for any
 purpose with or without fee is hereby granted.
 .
 THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES WITH
 REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF MERCHANTABILITY
 AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY SPECIAL, DIRECT,
 INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES WHATSOEVER RESULTING FROM
 LOSS OF USE, DATA OR PROFITS, WHETHER IN AN ACTION OF CONTRACT, NEGLIGENCE OR
 OTHER TORTIOUS ACTION, ARISING OUT OF OR IN CONNECTION WITH THE USE OR
 PERFORMANCE OF THIS SOFTWARE.

EOF

installed_kb="$(du -ks "${root}" | awk '{print $1}')"

cat > "${controldir}/control" <<EOF
Package: ${pkgname}
Version: ${debver}
Section: misc
Priority: optional
Architecture: ${arch}
Installed-Size: ${installed_kb}
Maintainer: eirikr <eirikr@localhost>
Depends: mate-terminal, dconf-cli, libglib2.0-bin
Recommends: tilix
Description: Atom color scheme for MATE Terminal (and Tilix)
 Ships the Atom palette as a MATE Terminal profile file and a helper command
 to import/enable it for the current user.
EOF

# md5sums is optional, but helps some tooling.
(cd "${root}" && find usr -type f -print0 | sort -z | xargs -0 md5sum) > "${controldir}/md5sums"

epoch="${SOURCE_DATE_EPOCH:-0}"

tar_args=(
  --sort=name
  --mtime="@${epoch}"
  --owner=0
  --group=0
  --numeric-owner
)

(cd "${controldir}" && tar "${tar_args[@]}" -cf "${workdir}/control.tar" .)
gzip -n -c "${workdir}/control.tar" > "${workdir}/control.tar.gz"

(cd "${root}" && tar "${tar_args[@]}" --exclude='./DEBIAN' -cf "${workdir}/data.tar" .)
gzip -n -c "${workdir}/data.tar" > "${workdir}/data.tar.gz"

printf '2.0\n' > "${workdir}/debian-binary"

debfile="${outdir}/${pkgname}_${debver}_${arch}.deb"
rm -f "${debfile}"
ar r "${debfile}" "${workdir}/debian-binary" "${workdir}/control.tar.gz" "${workdir}/data.tar.gz" >/dev/null

echo "Wrote ${debfile}"
