#!/usr/bin/env python3
# Created: 2026-08-30
"""Verify a heading restoration didn't damage the text.

Compares each changed chapter against its pre-change copy and asserts:
  * the file is still well-formed XML
  * the set of verse numbers is unchanged
  * each verse's text is unchanged EXCEPT for the removal of a heading that is
    now a real <heading> element (nothing else may be added or lost)
  * every fetched heading appears exactly once, and no chapter has duplicates

'Before' comes from git for tracked versions, or from a tarball for xml_esv,
which .gitignore excludes.
"""

import json
import os
import re
import subprocess
import sys
import tarfile
import xml.etree.ElementTree as ET
from pathlib import Path

from apply_headings import normalise


def verses(xml):
    out = {}
    for m in re.finditer(r'<v n="(\d+)"[^>]*>(.*?)</v>', xml, re.S):
        body = re.sub(r'<[^>]+>', '', m.group(2))
        out[m.group(1)] = re.sub(r'\s+', ' ', body).strip()
    return out


def headings(xml):
    return [re.sub(r'\s+', ' ', h).strip()
            for h in re.findall(r'<heading>(.*?)</heading>', xml, re.S)]


GIT_REF = os.environ.get('GIT_REF', 'HEAD')


def git_before(path):
    r = subprocess.run(['git', 'show', f'{GIT_REF}:{path}'], capture_output=True, text=True)
    return r.stdout if r.returncode == 0 else None


def main():
    version = sys.argv[1]
    tarball = sys.argv[2] if len(sys.argv) > 2 else None
    data = json.loads(Path(f'raw/headings/{version}.json').read_text())

    old_from_tar = {}
    if tarball:
        with tarfile.open(tarball) as tf:
            for member in tf.getmembers():
                # tar on macOS emits ._ AppleDouble sidecars; they are not content.
                if (member.isfile() and member.name.endswith('.xml')
                        and not Path(member.name).name.startswith('._')):
                    old_from_tar[member.name] = tf.extractfile(member).read().decode('utf-8')

    problems = []
    checked = 0
    for key, want in sorted(data.items()):
        slug, chapter = key.rsplit('_', 1)
        path = Path(f'xml_{version}/{slug}_{chapter}.xml')
        if not path.exists():
            continue
        new = path.read_text(encoding='utf-8')
        old = old_from_tar.get(str(path)) if tarball else git_before(str(path))
        if old is None or old == new:
            continue
        checked += 1

        try:
            ET.fromstring(new)
        except ET.ParseError as e:
            problems.append(f'{path}: NOT WELL-FORMED: {e}')
            continue

        ov, nv = verses(old), verses(new)
        if set(ov) != set(nv):
            problems.append(f'{path}: verse set changed {set(ov) ^ set(nv)}')

        new_headings = {normalise(h) for h in headings(new)} - {normalise(h) for h in headings(old)}
        for n in sorted(set(ov) & set(nv)):
            if ov[n] == nv[n]:
                continue
            removed = ov[n]
            for h in headings(new):
                if removed.endswith(h):
                    removed = removed[: -len(h)].strip()
            if re.sub(r'\s+', ' ', removed).strip() != nv[n]:
                problems.append(
                    f'{path} v{n}: text changed beyond heading removal\n'
                    f'    old: ...{ov[n][-90:]!r}\n    new: ...{nv[n][-90:]!r}')

        hs = headings(new)
        dupes = {h for h in hs if [normalise(x) for x in hs].count(normalise(h)) > 1}
        if dupes:
            problems.append(f'{path}: duplicate headings {sorted(dupes)}')

        have = {normalise(h) for h in hs}
        for _verse, text in want:
            if normalise(text) not in have:
                problems.append(f'{path}: fetched heading missing after apply: {text!r}')

    print(f'{version}: validated {checked} changed chapters — '
          f'{len(problems)} problem(s)')
    for p in problems[:40]:
        print('  ✗', p)
    return 1 if problems else 0


if __name__ == '__main__':
    sys.exit(main())
