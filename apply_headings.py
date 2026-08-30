#!/usr/bin/env python3
# Created: 2026-08-30
"""Restore section headings into the chapter XML, using the fetched heading lists.

Companion to ``fetch_headings.py`` — see that file for the two importer bugs
this repairs. Per chapter:

1. Insert ``<heading>`` at the anchored verse, matching the placement the NKJV
   NT already uses: ``<marker begin-verse>`` then ``<heading>`` then ``<v>``.
2. Strip the glued copy from the tail of the verse that precedes that anchor.
3. ESV only: drop the bogus ``<heading>Proverbs 1</heading>`` chapter titles the
   ESV importer captured as section headings.

The stripping is deliberately narrow. It only ever touches the tail of the one
verse the heading was glued to, so a heading word that also occurs in ordinary
scripture is out of reach — ESV Song of Solomon 2:4 begins "He brought me to the
banqueting house", and "He" is itself a speaker heading in that book.

Dry-run by default; pass --apply to write.
"""

import argparse
import json
import re
from collections import Counter
from pathlib import Path
from xml.sax.saxutils import escape

from fetch_headings import ALL_BOOKS, SOURCES

BOOK_BY_SLUG = {slug: (name, num) for slug, name, _ch, _usfm, num in ALL_BOOKS}

VERSE_RE = re.compile(r'<v n="(\d+)"[^>]*>(.*?)</v>', re.S)
HEADING_RE = re.compile(r'<heading>(.*?)</heading>', re.S)
# A heading element plus the whitespace around it, for stepping over a run of them.
HEADING_BLOCK = re.compile(r'\s*<heading>.*?</heading>[ \t]*\n?', re.S)


def normalise(text):
    """Loose key for 'is this the same heading', ignoring case and punctuation."""
    return re.sub(r'[^a-z0-9]+', ' ', text.lower()).strip()


def similar(a, b):
    """True if two headings are the same heading written differently.

    Covers the two shapes seen in the data: BSB keeps the cross-reference
    parenthetical inside the heading ("From Adam to Abraham(Genesis 5:1-32)"),
    and wording drifts slightly between sources ("Bear and Share the Burdens"
    vs "Bear and Share Burdens"). Distinct headings that merely share an anchor
    — ESV Song of Solomon has "He" and "Others" on the same verse — are not
    similar, so both are kept.
    """
    a, b = normalise(a), normalise(b)
    if not a or not b:
        return False
    if a in b or b in a:
        return True
    wa, wb = set(a.split()), set(b.split())
    return len(wa & wb) / len(wa | wb) >= 0.5


def chapter_span(xml):
    """(start, end) offsets of the <chapter> element's inner content."""
    m = re.search(r'<chapter\b[^>]*>', xml)
    end = xml.rfind('</chapter>')
    if not m or end == -1:
        return None
    return m.end(), end


def verse_spans(xml):
    """[(verse number, inner start, inner end)] in document order."""
    return [(int(m.group(1)), m.start(2), m.end(2)) for m in VERSE_RE.finditer(xml)]


def headings_at(xml, at):
    """The <heading> texts already stacked at an insertion point."""
    out = []
    while True:
        m = HEADING_BLOCK.match(xml, at)
        if not m:
            return out
        out.append(re.sub(r'\s+', ' ', HEADING_RE.search(m.group(0)).group(1)).strip())
        at = m.end()


def anchor_offset(xml, booknum, chapter, verse):
    """Where a heading for `verse` belongs: just after its begin-verse marker."""
    span = chapter_span(xml)
    if span is None:
        return None
    body_start, body_end = span
    if verse == 1:
        # Verse 1's marker sits outside <chapter>, so a v1 heading opens the
        # chapter — which is where the surviving headings already are.
        return body_start
    mid = f'v{booknum:02d}{chapter:03d}{verse:03d}'
    body = xml[body_start:body_end]
    # Markers appear both self-closed (NKJV) and with a separate end tag (ESV).
    for pattern in (r'<marker\b[^>]*mid="' + mid + r'"[^>]*/>[ \t]*\n?',
                    r'<marker\b[^>]*mid="' + mid + r'"[^>]*>.*?</marker>[ \t]*\n?'):
        m = re.search(pattern, body, re.S)
        if m:
            return body_start + m.end()
    m = re.search(r'[ \t]*<v n="' + str(verse) + r'"[ >]', body)
    return body_start + m.start() if m else None


def strip_glued(xml, inner_start, inner_end, heading):
    """Remove `heading` from the tail of one verse's content.

    The import concatenated the heading onto the verse with no separator, and
    package_all.sh's fix_lost_linebreak_spacing.py has since inserted a space in
    front of any heading glued after ``,;:!?`` — so both spacings are handled.

    The character before the match must not be '>': that would mean the text is
    the verse's own opening word rather than something welded onto its end.
    """
    inner = xml[inner_start:inner_end]
    pattern = re.compile(r'(?<=[^>])' + re.escape(heading) + r'(?=(?:\s*<[^>]+>)*\s*$)')
    m = pattern.search(inner)
    if not m:
        return xml, False
    cut = inner[:m.start()].rstrip() + inner[m.end():]
    return xml[:inner_start] + cut + xml[inner_end:], True


def drop_bogus_titles(xml, book_name, chapter, report):
    """ESV captured the chapter title ('Proverbs 1') as a section heading."""
    want = normalise(f'{book_name} {chapter}')

    def repl(m):
        if normalise(m.group(1)) == want:
            report['bogus_removed'] += 1
            return ''
        return m.group(0)

    return re.sub(r'[ \t]*<heading>(.*?)</heading>[ \t]*\n?', repl, xml, flags=re.S)


def heading_anchors(xml):
    """[(verse, text)] for headings in the file, by the <v> each one precedes."""
    out = []
    for m in HEADING_RE.finditer(xml):
        nxt = re.search(r'<v n="(\d+)"', xml[m.end():])
        if nxt:
            out.append((int(nxt.group(1)), re.sub(r'\s+', ' ', m.group(1)).strip()))
    return out


def process_version(version, apply_changes, only_book=None):
    cache = Path(f'raw/headings/{version}.json')
    if not cache.exists():
        print(f'{version}: no cache at {cache} — run fetch_headings.py first')
        return
    data = json.loads(cache.read_text())
    report = Counter()

    # Held in memory so a chapter-opening heading can be unglued from the tail of
    # the PREVIOUS chapter's file, which is where the import left it.
    files = {}

    def load(path):
        if path not in files:
            files[path] = path.read_text(encoding='utf-8') if path.exists() else None
        return files[path]

    for key, headings in sorted(data.items()):
        slug, chapter = key.rsplit('_', 1)
        chapter = int(chapter)
        if only_book and slug != only_book:
            continue
        path = Path(f'xml_{version}/{slug}_{chapter}.xml')
        if load(path) is None:
            report['missing_file'] += 1
            continue
        book_name, booknum = BOOK_BY_SLUG[slug]

        if version == 'esv':
            files[path] = drop_bogus_titles(files[path], book_name, chapter, report)

        # Group by anchor: several headings can share one verse (Song of
        # Solomon stacks a section heading and a speaker label), and they were
        # all glued onto the tail of the same preceding verse.
        grouped = {}
        for verse, text in headings:
            text = re.sub(r'\s+', ' ', text).strip()
            if not text:
                continue
            if text.isdigit():
                # Bible Gateway marks MSG's numbered "sayings of the wise" with
                # <h3 class="psalm-acrostic">6</h3>. A bare number rendered as a
                # section heading would read as a defect, so leave them out.
                report['skipped_numeric'] += 1
                continue
            grouped.setdefault(verse, []).append(text)

        for verse, texts in grouped.items():
            # 1. Unglue. Peel from the end backwards, since only the last of a
            #    run sits flush against the close of the verse.
            spans = verse_spans(files[path])
            idx = next((i for i, (n, _s, _e) in enumerate(spans) if n == verse), None)
            if idx is not None and idx > 0:
                for text in reversed(texts):
                    _n, s, e = verse_spans(files[path])[idx - 1]
                    files[path], done = strip_glued(files[path], s, e, text)
                    report['unglued'] += done
            elif idx == 0 or verse == 1:
                prev = Path(f'xml_{version}/{slug}_{chapter - 1}.xml')
                if chapter > 1 and load(prev) is not None:
                    for text in reversed(texts):
                        pspans = verse_spans(files[prev])
                        if not pspans:
                            break
                        _n, s, e = pspans[-1]
                        files[prev], done = strip_glued(files[prev], s, e, text)
                        report['unglued_prev_chapter'] += done

            # 2. Insert, unless the same heading is already stacked at the anchor.
            for text in texts:
                at = anchor_offset(files[path], booknum, chapter, verse)
                if at is None:
                    report['no_anchor'] += 1
                    continue
                stacked = headings_at(files[path], at)
                if any(similar(h, text) for h in stacked):
                    report['already_present'] += 1
                    continue
                after = at
                for _h in stacked:
                    after = HEADING_BLOCK.match(files[path], after).end()
                indent = re.match(r'[ \t]*', files[path][after:]).group(0) or '\t\t\t'
                files[path] = (files[path][:after]
                               + f'{indent}<heading>{escape(text)}</heading>\n'
                               + files[path][after:])
                report['inserted'] += 1

    changed = 0
    for path, text in files.items():
        if text is None:
            continue
        if text != path.read_text(encoding='utf-8'):
            changed += 1
            if apply_changes:
                path.write_text(text, encoding='utf-8')

    verb = 'applied' if apply_changes else 'DRY RUN'
    print(f'{version}: {verb} — {changed} files changed; ' +
          ', '.join(f'{k}={v}' for k, v in sorted(report.items())))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('versions', nargs='*', default=None)
    ap.add_argument('--apply', action='store_true', help='write changes (default: dry run)')
    ap.add_argument('--book', help='limit to one book slug, e.g. proverbs')
    args = ap.parse_args()
    for version in (args.versions or list(SOURCES)):
        process_version(version, args.apply, args.book)


if __name__ == '__main__':
    main()
