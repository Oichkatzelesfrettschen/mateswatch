#!/usr/bin/env bash
set -euo pipefail

pkgname="mateswatch"
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

mkdir -p "${root}/usr/share/mateswatch/mate-terminal"
mkdir -p "${root}/usr/bin"
mkdir -p "${root}/usr/share/doc/${pkgname}"
mkdir -p "${controldir}"
mkdir -p "${outdir}"

cp -a "${repo_root}/mate-terminal/schemes" \
  "${root}/usr/share/mateswatch/mate-terminal/"
install -m 0755 "${repo_root}/scripts/mateswatch-import.py" \
  "${root}/usr/bin/mateswatch"

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
install -m 0644 "${repo_root}/docs/dracula-pro.md" \
  "${root}/usr/share/doc/${pkgname}/dracula-pro.md"
install -m 0644 "${repo_root}/docs/mateswatch-stats.md" \
  "${root}/usr/share/doc/${pkgname}/mateswatch-stats.md"

mkdir -p "${root}/usr/share/doc/${pkgname}/sources"
cp -a "${repo_root}/sources/"* "${root}/usr/share/doc/${pkgname}/sources/"
install -m 0644 "${repo_root}/docs/packaging.md" \
  "${root}/usr/share/doc/${pkgname}/packaging.md"

cat > "${root}/usr/share/doc/${pkgname}/README.Debian" <<'EOF'
This package ships mateswatch: a large set of MATE Terminal profile snippets and a helper command.

To list and import themes for your user:

  mateswatch list
  mateswatch import gogh-atom --add-to-profile-list --set-default

EOF

cat > "${root}/usr/share/doc/${pkgname}/copyright" <<'EOF'
Format: https://www.debian.org/doc/packaging-manuals/copyright-format/1.0/
Upstream-Name: mateswatch (terminal theme pack)
Source: https://github.com/Oichkatzelesfrettschen/mateswatch

Files: usr/share/mateswatch/mate-terminal/schemes/**
Copyright: Various
License: MIT
 Comment:
  This package includes converted scheme snippets derived from MIT-licensed
  upstream theme collections. See /usr/share/doc/mateswatch/sources/.

Files: usr/share/doc/mateswatch/sources/**
Copyright: Various
License: Various
 Comment:
  This directory contains vendored upstream license texts and attribution
  notes per source corpus.

Files: usr/bin/mateswatch
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

License: MIT
 Permission is hereby granted, free of charge, to any person obtaining a copy
 of this software and associated documentation files (the "Software"), to deal
 in the Software without restriction, including without limitation the rights
 to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 copies of the Software, and to permit persons to whom the Software is
 furnished to do so, subject to the following conditions:
 .
 The above copyright notice and this permission notice shall be included in all
 copies or substantial portions of the Software.
 .
 THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 SOFTWARE.

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
Depends: mate-terminal, dconf-cli, libglib2.0-bin, python3
Description: mateswatch terminal theme pack for MATE Terminal
 Ships a large set of MATE Terminal profile snippets plus a helper command
 to import/enable individual profiles for the current user.
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
