#!/usr/bin/env python3
# Created: 2026-08-30
"""Build the missing book of Nahum for amp, nlt, msg and nkjv.

books.xml has always listed Nahum, but the chapter files were never generated
for these four versions, so the book renders blank in the reader.

Sources, each matched to what the version's existing text actually is:
  amp  -> API.Bible, Amplified Bible
  nlt  -> API.Bible, New Living Translation
  msg  -> API.Bible, *Free Bible Version* — xml_msg contains FBV text, not The
          Message, despite the app's label. Using the MSG edition here would
          mix two translations inside one book.
  nkjv -> Bible Gateway. This API.Bible key does not grant the NKJV, and Bible
          Gateway is already the NKJV source for this repo's heading and
          words-of-Christ work.

Output matches the sibling chapters of each version exactly: the same
copyright/metadata header, <marker> before every verse, headings between the
marker and its <v>, and — for NKJV, which has cross_refs/nahum/*.txt — the
crossref elements at the head of each verse, which is where the original
importer put them.

    python3 build_nahum.py             # dry run
    python3 build_nahum.py --apply
"""

import os
import re
import sys
import time
from pathlib import Path

import requests
from bs4 import BeautifulSoup

BOOK_NUM = 34
BOOK_TITLE = 'Nahum'
BOOK_ABBR = 'nah'
CHAPTERS = (1, 2, 3)

API_BASE = 'https://rest.api.bible/v1'
API_BIBLES = {
    'amp': 'a81b73293d3080c9-01',   # Amplified Bible
    'nlt': 'd6e14a625393b4da-01',   # New Living Translation
    'msg': '65eec8e0b60e656b-01',   # Free Bible Version — see module docstring
}
UA = {'User-Agent': 'Mozilla/5.0'}
SKIP_HEADINGS = {'Footnotes', 'Cross references', 'Cross References'}


def esc(s):
    return s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')


# --------------------------------------------------------------------------- API.Bible

def _flatten_text(items):
    for it in items:
        if it.get('type') == 'text':
            yield it.get('text', '')
        elif it.get('items'):
            yield from _flatten_text(it['items'])


def _walk_api(items, state):
    """Collect verse text and s-style headings from API.Bible's USFM JSON."""
    for it in items:
        if it.get('type') != 'tag':
            if it.get('type') == 'text' and state['verse']:
                state['verses'].setdefault(state['verse'], []).append(it.get('text', ''))
            continue
        name, style = it.get('name'), it.get('attrs', {}).get('style', '')
        if name == 'verse':
            state['verse'] = int(it['attrs']['number'].split('-')[0])
            for text in state.pop('pending', []):
                state['headings'].append((state['verse'], text))
            state['pending'] = []
            continue
        if name == 'para' and style.startswith(('s', 'ms', 'mt')) and style != 'sp':
            text = re.sub(r'\s+', ' ', ''.join(_flatten_text(it.get('items', [])))).strip()
            if text and text not in SKIP_HEADINGS:
                state.setdefault('pending', []).append(text)
            continue
        _walk_api(it.get('items', []), state)


def fetch_api(version, chapter):
    key = os.environ['APIBIBLE_KEY']
    url = f"{API_BASE}/bibles/{API_BIBLES[version]}/chapters/{BOOK_ABBR.upper().replace('NAH', 'NAM')}.{chapter}"
    r = requests.get(url, headers={'api-key': key}, timeout=30, params={
        'content-type': 'json', 'include-verse-numbers': 'true',
        'include-titles': 'true', 'include-notes': 'false',
        'include-chapter-numbers': 'false'})
    r.raise_for_status()
    state = {'verse': None, 'verses': {}, 'headings': [], 'pending': []}
    _walk_api(r.json()['data']['content'], state)
    verses = {}
    for n, parts in state['verses'].items():
        text = re.sub(r'\s+', ' ', ''.join(parts)).strip()
        # The verse-number tag emits the number as its own text node.
        text = re.sub(r'^' + str(n) + r'\s*', '', text).strip()
        if text:
            verses[n] = text
    return verses, state['headings']


# --------------------------------------------------------------------------- Bible Gateway

def fetch_gateway(chapter):
    r = requests.get('https://www.biblegateway.com/passage/', timeout=30, headers=UA,
                     params={'search': f'{BOOK_TITLE} {chapter}', 'version': 'NKJV'})
    r.raise_for_status()
    body = BeautifulSoup(r.text, 'html.parser').select_one('.passage-text')
    verses, headings, pending = {}, [], []
    for el in body.find_all(['h3', 'h4', 'span']):
        if el.name in ('h3', 'h4'):
            text = re.sub(r'\s+', ' ', el.get_text(' ', strip=True)).strip()
            if text and text not in SKIP_HEADINGS:
                pending.append(text)
            continue
        classes = el.get('class') or []
        if 'text' not in classes:
            continue
        # Bible Gateway puts the heading inside an <h3> that wraps a span
        # carrying the *following* verse's class, so such a span is heading
        # text, not verse text.
        if el.find_parent(['h3', 'h4']):
            continue
        vn = None
        for cls in classes:
            m = re.fullmatch(r'[A-Za-z0-9]+-' + str(chapter) + r'-(\d+)', cls)
            if m:
                vn = int(m.group(1))
        if vn is None:
            continue
        if pending:
            headings.extend((vn, h) for h in pending)
            pending = []
        frag = BeautifulSoup(str(el), 'html.parser')
        for junk in frag.find_all(['sup', 'h3', 'h4']):
            junk.decompose()
        for junk in frag.find_all(class_=['chapternum', 'versenum']):
            junk.decompose()
        text = re.sub(r'\s+', ' ', frag.get_text(' ', strip=True)).strip()
        if text:
            verses.setdefault(vn, []).append(text)
    return ({n: ' '.join(p) for n, p in verses.items()}, headings)


# --------------------------------------------------------------------------- cross refs

def load_crossrefs(version, chapter):
    """{verse: [(letter, cid)]} from cross_refs/nahum/<chapter>.txt."""
    path = Path(f'xml_{version}/cross_refs/nahum/{chapter}.txt')
    if not path.exists():
        return {}
    out, verse, letter = {}, None, None
    for line in path.read_text(encoding='utf-8').splitlines():
        parts = line.strip().split(None, 1)
        if len(parts) < 2:
            continue
        tag, val = parts
        if tag == 'V':
            verse = int(val[-3:])
        elif tag == 'c':
            letter = val
        elif tag == 'i' and verse is not None and letter is not None:
            out.setdefault(verse, []).append((letter, val))
            letter = None
    return out


# --------------------------------------------------------------------------- emit

def header_for(version):
    """Reuse a sibling chapter's copyright/metadata/generation block verbatim."""
    sample = Path(f'xml_{version}/micah_1.xml').read_text(encoding='utf-8')
    head, sep, _ = sample.partition('\n\t<book ')
    if not sep:
        raise ValueError(f'unexpected shape in xml_{version}/micah_1.xml')
    version_attr = re.search(r'<book [^>]*version="([^"]+)"', sample).group(1)
    return head, version_attr


def build(version, chapter, verses, headings, crossrefs):
    head, version_attr = header_for(version)
    by_verse = {}
    for verse, text in headings:
        by_verse.setdefault(verse, []).append(text)

    def marker(v):
        return f'\t\t\t<marker class="begin-verse" mid="v{BOOK_NUM:02d}{chapter:03d}{v:03d}" />\n'

    out = [head, '\n',
           f'\t<book title="{BOOK_TITLE}" num="{BOOK_NUM}" testament="old" '
           f'version="{version_attr}" bookAbbr="{BOOK_ABBR}">\n',
           f'\t\t<marker class="begin-verse" mid="v{BOOK_NUM:02d}{chapter:03d}001" />\n',
           f'\t\t<chapter num="{chapter}">\n']
    for text in by_verse.get(1, []):
        out.append(f'\t\t\t<heading>{esc(text)}</heading>\n')
    out.append('\t\t\t<begin-paragraph />\n')

    ordered = sorted(verses)
    for i, v in enumerate(ordered):
        if i:
            out.append(marker(v))
            for text in by_verse.get(v, []):
                out.append(f'\t\t\t<heading>{esc(text)}</heading>\n')
        out.append(f'\t\t\t<v n="{v}">\n')
        for letter, cid in crossrefs.get(v, []):
            out.append(f'\t\t\t\t<crossref let="{letter}" cid="{cid}" />\n')
        out.append(f'\t\t\t\t{esc(verses[v])}\n\t\t\t</v>\n')
    out.append(marker(ordered[-1] + 1))
    out.append('\t\t\t<end-paragraph />\n\t\t</chapter>\n\t</book>\n</bible>')
    return ''.join(out)


def main():
    apply_changes = '--apply' in sys.argv
    for version in ('amp', 'nlt', 'msg', 'nkjv'):
        for chapter in CHAPTERS:
            if version == 'nkjv':
                verses, headings = fetch_gateway(chapter)
            else:
                verses, headings = fetch_api(version, chapter)
            crossrefs = load_crossrefs(version, chapter)
            if not verses:
                print(f'  {version} nahum {chapter}: NO VERSES — skipped')
                continue
            gaps = [v for v in range(1, max(verses) + 1) if v not in verses]
            xml = build(version, chapter, verses, headings, crossrefs)
            path = Path(f'xml_{version}/nahum_{chapter}.xml')
            print(f'  {version:<5} nahum_{chapter}: {len(verses)} verses, '
                  f'{len(headings)} headings, {sum(len(c) for c in crossrefs.values())} crossrefs'
                  f'{"  GAPS " + str(gaps) if gaps else ""}'
                  f'{"" if path.exists() else "   (new file)"}')
            for verse, text in headings:
                print(f'         heading v{verse}: {text}')
            if apply_changes:
                path.write_text(xml, encoding='utf-8')
            time.sleep(0.5)
    print('applied' if apply_changes else 'DRY RUN — pass --apply to write')


if __name__ == '__main__':
    main()
