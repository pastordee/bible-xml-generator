#!/usr/bin/env python3
# Created: 2026-08-30
"""Fetch section headings per chapter, for versions whose import dropped them.

Background / the bug this feeds
-------------------------------
Two importers lost every mid-chapter section heading:

* ``create_other_version_chapters.py`` sets ``has_heading = True`` after the
  FIRST heading of a chapter and never emits another, so every later heading was
  absorbed into the preceding ``<v>`` with no separating space — producing text
  like ``...the life of its owners.The Call of Wisdom`` (NKJV Prov 1:19).
* ``create_esv_version_chapters.py`` keeps only "lines before any verse numbers"
  as headings, so ESV's mid-chapter headings were discarded outright and cannot
  be recovered from the XML at all.

Splitting the glued text back out by heuristic is NOT safe: "Selah" looks like a
glued heading in 61 Psalms verses, and a separate spacing defect (missing space
after a mid-verse period, e.g. 1 Kings 13:6) is indistinguishable from a real
seam. So we fetch the authoritative heading list per chapter instead, and let
``apply_headings.py`` do exact-string surgery with it.

Output: raw/headings/<version>.json — {"<book>_<chapter>": [[verse, "text"], ...]}
Resumable: already-fetched chapters are skipped, so a re-run costs nothing.
"""

import json
import re
import sys
import time
from pathlib import Path

import copy

import requests
from bs4 import BeautifulSoup

# (slug, display name, chapter count, USFM id, book number)
ALL_BOOKS = [
    ('genesis', 'Genesis', 50, 'GEN', 1), ('exodus', 'Exodus', 40, 'EXO', 2),
    ('leviticus', 'Leviticus', 27, 'LEV', 3), ('numbers', 'Numbers', 36, 'NUM', 4),
    ('deuteronomy', 'Deuteronomy', 34, 'DEU', 5), ('joshua', 'Joshua', 24, 'JOS', 6),
    ('judges', 'Judges', 21, 'JDG', 7), ('ruth', 'Ruth', 4, 'RUT', 8),
    ('1_samuel', '1 Samuel', 31, '1SA', 9), ('2_samuel', '2 Samuel', 24, '2SA', 10),
    ('1_kings', '1 Kings', 22, '1KI', 11), ('2_kings', '2 Kings', 25, '2KI', 12),
    ('1_chronicles', '1 Chronicles', 29, '1CH', 13), ('2_chronicles', '2 Chronicles', 36, '2CH', 14),
    ('ezra', 'Ezra', 10, 'EZR', 15), ('nehemiah', 'Nehemiah', 13, 'NEH', 16),
    ('esther', 'Esther', 10, 'EST', 17), ('job', 'Job', 42, 'JOB', 18),
    ('psalms', 'Psalms', 150, 'PSA', 19), ('proverbs', 'Proverbs', 31, 'PRO', 20),
    ('ecclesiastes', 'Ecclesiastes', 12, 'ECC', 21), ('song_of_solomon', 'Song of Solomon', 8, 'SNG', 22),
    ('isaiah', 'Isaiah', 66, 'ISA', 23), ('jeremiah', 'Jeremiah', 52, 'JER', 24),
    ('lamentations', 'Lamentations', 5, 'LAM', 25), ('ezekiel', 'Ezekiel', 48, 'EZK', 26),
    ('daniel', 'Daniel', 12, 'DAN', 27), ('hosea', 'Hosea', 14, 'HOS', 28),
    ('joel', 'Joel', 3, 'JOL', 29), ('amos', 'Amos', 9, 'AMO', 30),
    ('obadiah', 'Obadiah', 1, 'OBA', 31), ('jonah', 'Jonah', 4, 'JON', 32),
    ('micah', 'Micah', 7, 'MIC', 33), ('nahum', 'Nahum', 3, 'NAM', 34),
    ('habakkuk', 'Habakkuk', 3, 'HAB', 35), ('zephaniah', 'Zephaniah', 3, 'ZEP', 36),
    ('haggai', 'Haggai', 2, 'HAG', 37), ('zechariah', 'Zechariah', 14, 'ZEC', 38),
    ('malachi', 'Malachi', 4, 'MAL', 39),
    ('matthew', 'Matthew', 28, 'MAT', 40), ('mark', 'Mark', 16, 'MRK', 41),
    ('luke', 'Luke', 24, 'LUK', 42), ('john', 'John', 21, 'JHN', 43),
    ('acts', 'Acts', 28, 'ACT', 44), ('romans', 'Romans', 16, 'ROM', 45),
    ('1_corinthians', '1 Corinthians', 16, '1CO', 46), ('2_corinthians', '2 Corinthians', 13, '2CO', 47),
    ('galatians', 'Galatians', 6, 'GAL', 48), ('ephesians', 'Ephesians', 6, 'EPH', 49),
    ('philippians', 'Philippians', 4, 'PHP', 50), ('colossians', 'Colossians', 4, 'COL', 51),
    ('1_thessalonians', '1 Thessalonians', 5, '1TH', 52), ('2_thessalonians', '2 Thessalonians', 3, '2TH', 53),
    ('1_timothy', '1 Timothy', 6, '1TI', 54), ('2_timothy', '2 Timothy', 4, '2TI', 55),
    ('titus', 'Titus', 3, 'TIT', 56), ('philemon', 'Philemon', 1, 'PHM', 57),
    ('hebrews', 'Hebrews', 13, 'HEB', 58), ('james', 'James', 5, 'JAS', 59),
    ('1_peter', '1 Peter', 5, '1PE', 60), ('2_peter', '2 Peter', 3, '2PE', 61),
    ('1_john', '1 John', 5, '1JN', 62), ('2_john', '2 John', 1, '2JN', 63),
    ('3_john', '3 John', 1, '3JN', 64), ('jude', 'Jude', 1, 'JUD', 65),
    ('revelation', 'Revelation', 22, 'REV', 66),
]

# version -> (source, remote id). esv.org and Bible Gateway are already used by
# rebuild_esv_poetry.py / rebuild_nkjv_nt_with_woc.py; helloao covers the two
# Bible Gateway can't serve with headings.
SOURCES = {
    'esv':  ('esv',     None),
    'nkjv': ('gateway', 'NKJV'),
    'amp':  ('gateway', 'AMP'),
    'nlt':  ('gateway', 'NLT'),
    'msg':  ('gateway', 'MSG'),
    'bsb':  ('helloao', 'BSB'),
    'web':  ('helloao', 'ENGWEBP'),
}

UA = {'User-Agent': 'Mozilla/5.0'}
SKIP_HEADINGS = {'Footnotes', 'Cross references', 'Cross References'}


def heading_text(el):
    """Heading string with crossref/footnote superscripts removed.

    Bible Gateway nests ``<sup class="crossreference">`` inside the ``<h3>``,
    which would otherwise yield 'The Beatitudes ( A )'.
    """
    el = copy.copy(el)
    for junk in el.find_all(['sup', 'a'], class_=['crossreference', 'footnote']):
        junk.decompose()
    for junk in el.find_all('sup'):
        junk.decompose()
    return re.sub(r'\s+', ' ', el.get_text(' ', strip=True)).strip()


def _get(url, **kw):
    """GET with a few retries; returns None if the chapter is genuinely absent."""
    for attempt in range(4):
        try:
            r = requests.get(url, timeout=30, headers=UA, **kw)
            if r.status_code == 404:
                return None
            if r.status_code == 200:
                return r
            time.sleep(2 * (attempt + 1))
        except requests.RequestException:
            time.sleep(2 * (attempt + 1))
    return None


def fetch_esv(book_name, chapter, _id):
    """esv.org anchors every heading to a data-ref like 20001020 (book/ch/verse)."""
    r = _get(f"https://www.esv.org/{book_name.replace(' ', '+')}+{chapter}/")
    if r is None:
        return None
    body = BeautifulSoup(r.text, 'html.parser')
    booknum = BOOKNUM_BY_NAME[book_name]
    out = []
    for h in body.find_all(['h3', 'h4']):
        text = heading_text(h)
        if not text or text in SKIP_HEADINGS:
            continue
        nxt = h.find_next(attrs={'data-ref': True})
        if nxt is None:
            continue
        ref = nxt.get('data-ref')
        m = re.fullmatch(r'(\d{2})(\d{3})(\d{3})', ref)
        # The page bleeds into neighbouring chapters and books; keep only this one.
        if not m or int(m.group(1)) != booknum or int(m.group(2)) != chapter:
            continue
        out.append([int(m.group(3)), text])
    return out


def fetch_gateway(book_name, chapter, version):
    """Bible Gateway tags each verse span with a class like ``Prov-1-8``.

    MSG uses ranges (``Prov-1-1-Prov-1-6``); the first verse of the range is the
    heading's anchor, which is what we want.
    """
    r = _get("https://www.biblegateway.com/passage/",
             params={'search': f'{book_name} {chapter}', 'version': version})
    if r is None:
        return None
    soup = BeautifulSoup(r.text, 'html.parser')
    body = soup.select_one('.passage-text')
    if body is None:
        return None
    out = []
    for h in body.find_all(['h3', 'h4']):
        text = heading_text(h)
        if not text or text in SKIP_HEADINGS:
            continue
        verse = None
        for sib in h.find_all_next('span', class_='text'):
            for cls in sib.get('class', []):
                m = re.match(r'^[A-Za-z0-9]+-(\d+)-(\d+)', cls)
                if m and int(m.group(1)) == chapter:
                    verse = int(m.group(2))
                    break
            if verse is not None:
                break
        if verse is not None:
            out.append([verse, text])
    return out


USFM_BY_NAME = {name: usfm for _slug, name, _ch, usfm, _num in ALL_BOOKS}
BOOKNUM_BY_NAME = {name: num for _slug, name, _ch, _usfm, num in ALL_BOOKS}


def fetch_helloao(book_name, chapter, translation):
    """helloao interleaves heading/verse nodes; a heading anchors to the next verse."""
    usfm = USFM_BY_NAME[book_name]
    r = _get(f"https://bible.helloao.org/api/{translation}/{usfm}/{chapter}.json")
    if r is None:
        return None
    try:
        content = r.json()['chapter']['content']
    except (ValueError, KeyError):
        return None
    out = []
    pending = []
    for node in content:
        if not isinstance(node, dict):
            continue
        if node.get('type') == 'heading':
            parts = node.get('content') or []
            text = ' '.join(p for p in parts if isinstance(p, str)).strip()
            if text and text not in SKIP_HEADINGS:
                pending.append(text)
        elif node.get('type') == 'verse' and pending:
            verse = node.get('number')
            if isinstance(verse, int):
                out.extend([verse, t] for t in pending)
            pending = []
    return out


FETCHERS = {'esv': fetch_esv, 'gateway': fetch_gateway, 'helloao': fetch_helloao}


def main():
    versions = sys.argv[1:] or list(SOURCES)
    outdir = Path('raw/headings')
    outdir.mkdir(parents=True, exist_ok=True)

    for version in versions:
        source, remote = SOURCES[version]
        fetcher = FETCHERS[source]
        path = outdir / f'{version}.json'
        data = json.loads(path.read_text()) if path.exists() else {}
        delay = 1.2 if source == 'gateway' else (1.0 if source == 'esv' else 0.25)

        todo = [(s, n, c) for s, n, ch, _u, _n in ALL_BOOKS for c in range(1, ch + 1)
                if f'{s}_{c}' not in data]
        print(f'{version}: {len(data)} cached, {len(todo)} to fetch from {source}', flush=True)

        for i, (slug, name, chapter) in enumerate(todo, 1):
            result = fetcher(name, chapter, remote)
            if result is None:
                print(f'  !! {slug} {chapter}: fetch failed, will retry on next run', flush=True)
                time.sleep(delay)
                continue
            data[f'{slug}_{chapter}'] = result
            if i % 25 == 0 or i == len(todo):
                path.write_text(json.dumps(data, ensure_ascii=False, indent=0))
                got = sum(len(v) for v in data.values())
                print(f'  {i}/{len(todo)}  {slug} {chapter}  ({got} headings so far)', flush=True)
            time.sleep(delay)

        path.write_text(json.dumps(data, ensure_ascii=False, indent=0))
        print(f'{version}: done — {sum(len(v) for v in data.values())} headings '
              f'across {len(data)} chapters', flush=True)


if __name__ == '__main__':
    main()
