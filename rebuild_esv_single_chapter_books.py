#!/usr/bin/env python3
# Created: 2026-08-30
"""Rebuild the five ESV single-chapter books, which the import left empty.

The bug
-------
The ESV importer fetched every chapter as ``https://www.esv.org/<Book>+<n>/``.
For a single-chapter book esv.org reads "Jude 1" as *Jude verse 1*, not chapter
1, so the request returned one verse instead of the book. All five ended up with
a single ``<v n="1">`` — and not even the right text: ``jude_1.xml`` held
Revelation 1:1. Against 13/14/25/21/25 verses in every other version, these
books render blank in the reader.

The fix is to request the bare book name, which returns the whole book. The page
bleeds into neighbouring books, so verses are filtered by book number.

Verse rendering reuses rebuild_esv_poetry.py, which already handles esv.org's
poetry line-spans, words-of-Christ and small-caps. Section headings come from the
same page, so these books get theirs in the same pass — apply_headings.py could
not place them while the verses were missing.

Two deliberate omissions:
  * No <crossref> elements. xml_esv/cross_refs/<book>/ is empty for exactly
    these five books (the same import failure), so there are no cids to point
    at. rebuild_esv_poetry's renderer drops crossrefs absent from the map.
  * No <footnotes> block. The one in each file belongs to the bogus verse, and
    nothing in the app parses footnotes, so carrying wrong data forward is worse
    than dropping it.

    python3 rebuild_esv_single_chapter_books.py            # dry run
    python3 rebuild_esv_single_chapter_books.py --apply
"""

import re
import sys
import time
from collections import OrderedDict
from pathlib import Path

import requests
from bs4 import BeautifulSoup

from rebuild_esv_poetry import _load_cmap, _render, _walk

# slug, display name for esv.org, book number
BOOKS = [
    ('obadiah', 'Obadiah', 31),
    ('philemon', 'Philemon', 57),
    ('2_john', '2 John', 63),
    ('3_john', '3 John', 64),
    ('jude', 'Jude', 65),
]

SKIP_HEADINGS = {'Footnotes', 'Cross references', 'Cross References'}


def fetch(book_name):
    url = f"https://www.esv.org/{book_name.replace(' ', '+')}/"
    for attempt in range(3):
        try:
            r = requests.get(url, timeout=25, headers={'User-Agent': 'Mozilla/5.0'})
            r.raise_for_status()
            return BeautifulSoup(r.content, 'html.parser')
        except requests.RequestException:
            if attempt == 2:
                raise
            time.sleep(2.0)


def in_book(ref, booknum):
    """data-ref is BBCCCVVV; keep this book's chapter 1 only."""
    return (len(ref) == 8 and ref.isdigit()
            and int(ref[:2]) == booknum and int(ref[2:5]) == 1)


def parse(soup, slug, booknum):
    """(verses, headings) — {n: inner xml} and [(verse, heading text)]."""
    spans_by_v = OrderedDict()
    for vs in soup.find_all('span', class_='verse'):
        ref = vs.get('data-ref')
        if ref and in_book(ref, booknum):
            spans_by_v.setdefault(int(ref[-3:]), (ref, []))[1].append(vs)

    cmap_all = _load_cmap(slug, 1)
    verses = {}
    for vn, (ref, spans) in spans_by_v.items():
        parts, pending = [], []
        for vs in spans:
            _walk(vs.children, cmap_all.get(ref, {}), parts, pending)
        if pending:
            parts.append(('t', ' '.join(pending)))
        text = _render(parts)
        if text.strip():
            verses[vn] = text

    headings, pending = [], []
    for el in soup.find_all(['h3', 'h4', 'span', 'div', 'a', 'b']):
        ref = el.get('data-ref')
        if ref:
            if pending:
                if in_book(ref, booknum):
                    headings.extend((int(ref[-3:]), h) for h in pending)
                pending = []
        elif el.name in ('h3', 'h4'):
            text = re.sub(r'\s+', ' ', el.get_text(' ', strip=True)).strip()
            if text and text not in SKIP_HEADINGS:
                pending.append(text)
    return verses, headings


def build(existing, booknum, verses, headings):
    """Rewrite the chapter body, keeping the file's own header and <book> tag."""
    head, sep, _rest = existing.partition('\n\t\t<marker')
    if not sep:
        raise ValueError('unexpected file shape')

    by_verse = {}
    for verse, text in headings:
        by_verse.setdefault(verse, []).append(text)

    def marker(v):
        return (f'\t\t\t<marker class="begin-verse" mid="v{booknum:02d}001{v:03d}">\n'
                f'\t\t\t</marker>\n')

    out = [head, '\n',
           f'\t\t<marker class="begin-verse" mid="v{booknum:02d}001001">\n',
           '\t\t</marker>\n',
           '\t\t<chapter num="1">\n']
    for text in by_verse.get(1, []):
        out.append(f'\t\t\t<heading>{text}</heading>\n')
    out.append('\t\t\t<begin-paragraph>\n\t\t\t</begin-paragraph>\n')

    ordered = sorted(verses)
    for i, v in enumerate(ordered):
        if i:
            out.append(marker(v))
            for text in by_verse.get(v, []):
                out.append(f'\t\t\t<heading>{text}</heading>\n')
        out.append(f'\t\t\t<v n="{v}">{verses[v]}</v>\n')
    out.append(marker(ordered[-1] + 1))
    out.append('\t\t\t<end-paragraph>\n\t\t\t</end-paragraph>\n')
    out.append('\t\t</chapter>\n\t</book>\n</bible>')
    return ''.join(out)


def main():
    apply_changes = '--apply' in sys.argv
    for slug, name, booknum in BOOKS:
        path = Path(f'xml_esv/{slug}_1.xml')
        existing = path.read_text(encoding='utf-8')
        before = len(re.findall(r'<v n=', existing))
        soup = fetch(name)
        verses, headings = parse(soup, slug, booknum)
        if not verses:
            print(f'  {slug}: NO VERSES PARSED — skipped')
            continue
        rebuilt = build(existing, booknum, verses, headings)
        gaps = [v for v in range(1, max(verses) + 1) if v not in verses]
        print(f'  {slug:<10} {before} -> {len(verses)} verses, '
              f'{len(headings)} headings{"  GAPS " + str(gaps) if gaps else ""}')
        for verse, text in headings:
            print(f'       heading v{verse}: {text}')
        if apply_changes:
            path.write_text(rebuilt, encoding='utf-8')
        time.sleep(0.5)
    print('applied' if apply_changes else 'DRY RUN — pass --apply to write')


if __name__ == '__main__':
    main()
