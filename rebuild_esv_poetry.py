#!/usr/bin/env python3
"""Rebuild ESV verse text in-place from esv.org, fixing poetry truncation.

Background / the bug this fixes
-------------------------------
esv.org renders poetry with each line in its own ``<p class="line">``, and it
wraps EVERY line of a verse in its own ``<span class="verse">`` carrying the
same ``data-ref``. The original importer looped over those verse-spans and did
``verse_elem.clear()`` for each one, so for a multi-line (poetry) verse each
line overwrote the previous — leaving only the LAST line in the XML. That
truncated ~3,742 verses across the poetry/prophetic books (Psalms, Isaiah, Job,
Jeremiah, Lamentations, Proverbs, the songs in Deuteronomy/Genesis, NT poetic
quotes, …) to just their final clause.

The fix here groups ALL line-spans of a verse together and concatenates them, so
the full verse text is captured. Inline crossref letters (mapped to cids from
``xml_esv/cross_refs/<book>/<chapter>.txt``), words-of-Christ ``<woc>`` spans and
small-caps ("Lord") are preserved; verse numbers and footnote markers are
dropped.

Usage
-----
    python3 rebuild_esv_poetry.py --auto          # rebuild every chapter that
                                                  # has a truncated verse (vs KJV)
    python3 rebuild_esv_poetry.py isaiah 1        # rebuild a single chapter

Run ``fix_crossref_spacing.py --apply xml_esv`` afterwards, then repackage.
"""
import re
import sys
import time
from collections import OrderedDict
from pathlib import Path

import requests
from bs4 import BeautifulSoup, NavigableString

# book_file -> display name, parsed from the scraper's BOOK list
_SRC = Path('rebuild_esv_from_crossway.py').read_text(encoding='utf-8')
BOOK_NAME = dict(re.findall(r"\('([a-z0-9_]+)', '([^']+)', \d+, \d+\)", _SRC))


def _wordcounts(path: Path) -> dict:
    d = path.read_text(encoding='utf-8', errors='replace')
    out = {}
    for m in re.finditer(r'<v n="(\d+)">(.*?)</v>', d, re.DOTALL):
        t = re.sub(r'<[^>]+>', ' ', m.group(2))
        out[int(m.group(1))] = len(re.sub(r'\s+', ' ', t).split())
    return out


def chapters_needing_rebuild():
    """Chapters with >=1 verse under 50% of the KJV word count (KJV >= 8 words)."""
    todo = []
    for ef in sorted(Path('xml_esv').glob('*.xml')):
        if ef.name == 'books.xml':
            continue
        kf = Path('xml_kjv') / ef.name
        if not kf.exists():
            continue
        ev, kv = _wordcounts(ef), _wordcounts(kf)
        if any(kv.get(n, 0) >= 8 and ew < 0.5 * kv.get(n, 0) for n, ew in ev.items()):
            bf = re.sub(r'_(\d+)\.xml$', '', ef.name)
            ch = int(re.search(r'_(\d+)\.xml$', ef.name).group(1))
            if bf in BOOK_NAME:
                todo.append((bf, BOOK_NAME[bf], ch))
    return todo


def _esc(s: str) -> str:
    return s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')


def _walk(children, cmap, parts, pending):
    def flush():
        if pending:
            parts.append(('t', ' '.join(pending)))
            pending.clear()

    for ch in children:
        if isinstance(ch, NavigableString):
            t = str(ch).strip()
            if t:
                pending.append(t)
        elif ch.name == 'b':            # verse number -> skip
            continue
        elif ch.name == 'sup':
            if 'crossref' in (ch.get('class') or []):
                flush()
                a = ch.find('a')
                if a:
                    let = a.get_text(strip=True).lower()
                    if let in cmap:
                        parts.append(('x', (let, cmap[let])))
            # footnote -> skip
        elif ch.name == 'span' and 'woc' in (ch.get('class') or []):
            flush()
            wp, wpend = [], []
            _walk(ch.children, cmap, wp, wpend)
            parts.append(('w', _render(wp)))
        elif ch.name == 'span' and 'small-caps' in (ch.get('class') or []):
            t = ch.get_text(strip=True)        # "Lord"
            if t:
                pending.append(t)
        else:
            t = ch.get_text(strip=True)
            if t:
                pending.append(t)
    flush()


def _render(parts) -> str:
    out = []
    for kind, val in parts:
        if kind == 't':
            out.append(_esc(val))
        elif kind == 'x':
            out.append(f'<crossref let="{val[0]}" cid="{val[1]}" />')
        elif kind == 'w':
            out.append(f'<woc>{val}</woc>')
    return ' '.join(p for p in out if p)


def _load_cmap(book_file: str, chapter_num: int) -> dict:
    vc = {}
    cf = Path('xml_esv') / 'cross_refs' / book_file / f'{chapter_num}.txt'
    if cf.exists():
        cur = let = None
        for line in cf.read_text(encoding='utf-8').splitlines():
            line = line.strip()
            if not line:
                continue
            parts = line.split(None, 1)
            if len(parts) < 2:
                continue
            f, v = parts
            if f == 'V':
                cur = v
                vc.setdefault(cur, {})
            elif f == 'c' and cur:
                let = v
            elif f == 'i' and cur:
                vc[cur][let] = v
    return vc


def rebuild(book_file: str, book_name: str, chapter_num: int):
    url = f"https://www.esv.org/{book_name.replace(' ', '+')}+{chapter_num}/"
    for attempt in range(3):
        try:
            r = requests.get(url, timeout=25, headers={'User-Agent': 'Mozilla/5.0'})
            r.raise_for_status()
            break
        except Exception as e:                       # noqa: BLE001
            if attempt == 2:
                return ('ERR', f'fetch failed: {e}')
            time.sleep(2.0)
    soup = BeautifulSoup(r.content, 'html.parser')
    vc = _load_cmap(book_file, chapter_num)

    # group every line-span by verse number, in document order
    spans_by_v = OrderedDict()
    for vs in soup.find_all('span', class_='verse'):
        ref = vs.get('data-ref')
        if not ref:
            continue
        try:
            if int(ref[-6:-3]) != chapter_num:
                continue
            vn = int(ref[-3:])
        except ValueError:
            continue
        spans_by_v.setdefault(vn, (ref, []))[1].append(vs)
    if not spans_by_v:
        return ('ERR', 'no verse spans')

    new_inner = {}
    for vn, (ref, spans) in spans_by_v.items():
        cmap = vc.get(ref, {})
        parts, pending = [], []
        for vs in spans:
            _walk(vs.children, cmap, parts, pending)
        if pending:
            parts.append(('t', ' '.join(pending)))
        txt = _render(parts)
        if txt.strip():
            new_inner[vn] = txt

    path = Path('xml_esv') / f'{book_file}_{chapter_num}.xml'
    d = path.read_text(encoding='utf-8')

    def repl(m):
        vn = int(m.group(1))
        return f'<v n="{vn}">{new_inner[vn]}</v>' if vn in new_inner else m.group(0)

    path.write_text(re.sub(r'<v n="(\d+)">.*?</v>', repl, d, flags=re.DOTALL),
                    encoding='utf-8')
    return ('OK', f'{len(new_inner)} verses')


def main(argv):
    if len(argv) == 3:
        bf, ch = argv[1], int(argv[2])
        todo = [(bf, BOOK_NAME.get(bf, bf.replace('_', ' ').title()), ch)]
    elif len(argv) == 2 and argv[1] == '--auto':
        todo = chapters_needing_rebuild()
    else:
        print(__doc__)
        return 1

    print(f'rebuilding {len(todo)} chapter(s)')
    ok = err = 0
    for i, (bf, bn, ch) in enumerate(todo, 1):
        status, msg = rebuild(bf, bn, ch)
        if status == 'OK':
            ok += 1
        else:
            err += 1
            print(f'  ERR {bf}_{ch}: {msg}')
        if i % 25 == 0 or i == len(todo):
            print(f'  progress {i}/{len(todo)}  ok={ok} err={err}')
        time.sleep(0.4)
    print(f'DONE ok={ok} err={err}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main(sys.argv))
