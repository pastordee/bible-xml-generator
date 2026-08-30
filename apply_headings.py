#!/usr/bin/env python3
# Created: 2026-08-30
"""Restore section headings into the chapter XML, using the fetched heading lists.

Companion to ``fetch_headings.py`` — see that file for the two importer bugs
this repairs. Three edits per chapter:

1. Insert ``<heading>`` before the anchored verse, matching the placement the
   NKJV NT already uses: ``<marker begin-verse> <heading> <v>``.
2. Strip the glued copy out of the preceding verse. Only an exact match of the
   fetched heading, only where it is welded to a non-space character (the
   signature of the import bug), is removed — so "Selah" and the separate
   mid-verse spacing defect are never touched.
3. ESV only: drop the bogus ``<heading>Proverbs 1</heading>`` chapter titles the
   ESV importer captured as section headings.

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


def normalise(text):
    """Loose key for 'is this the same heading', ignoring case and punctuation."""
    return re.sub(r'[^a-z0-9]+', ' ', text.lower()).strip()


def chapter_span(xml):
    """(start, end) offsets of the <chapter> element's inner content."""
    m = re.search(r'<chapter\b[^>]*>', xml)
    end = xml.rfind('</chapter>')
    if not m or end == -1:
        return None
    return m.end(), end


def strip_glued(xml, heading, report):
    """Remove `heading` where the import left it sitting at the end of a <v>.

    The import concatenated the heading with no separator, so the usual giveaway
    is a non-whitespace character immediately before it. But package_all.sh runs
    fix_lost_linebreak_spacing.py, whose ``(?<=[a-z,;:!?])(?=[A-Z])`` rule has
    since inserted a space in front of any heading glued after ``,;:!?`` — e.g.
    NKJV Proverbs 24:22 "...who knows the ruin those two can bring? Further
    Sayings of the Wise". So both spacings have to be handled, or that heading
    would be shown twice: once in the verse and once as the new element.

    Either way the match must be the exact heading text and must sit at the very
    end of the verse, which is what keeps ordinary scripture out of range —
    verses end in punctuation, so a trailing word never matches a bare heading.
    """
    tail = r'(?=\s*(?:<crossref\b|<woc\b|</woc>|</v>))'
    xml, n = re.subn(r'(?<=\S)' + re.escape(heading) + tail, '', xml)
    if n:
        report['unglued'] += n
        return xml
    xml, n = re.subn(r'\s' + re.escape(heading) + tail, '', xml)
    if n:
        report['unglued_spaced'] += n
    return xml


def occupied(xml, at):
    """True if a <heading> already sits at this insertion point."""
    return xml[at:].lstrip()[:9] == '<heading>'


def marker_id(booknum, chapter, verse):
    return f'v{booknum:02d}{chapter:03d}{verse:03d}'


def insert_heading(xml, booknum, chapter, verse, heading, report):
    """Place <heading> after the verse's begin-verse marker, before its <v>."""
    tag = f'<heading>{escape(heading)}</heading>'
    span = chapter_span(xml)
    if span is None:
        report['no_chapter'] += 1
        return xml
    body_start, body_end = span

    if verse == 1:
        # Verse 1's marker sits outside <chapter>, so a v1 heading opens the
        # chapter — which is exactly where the surviving headings already are.
        if occupied(xml, body_start):
            report['anchor_occupied'] += 1
            return xml
        indent = re.match(r'\s*', xml[body_start:body_start + 40]).group(0) or '\n\t\t\t'
        report['inserted'] += 1
        return xml[:body_start] + f'{indent}{tag}' + xml[body_start:]

    mid = marker_id(booknum, chapter, verse)
    m = re.search(r'[ \t]*<marker\b[^>]*mid="' + mid + r'"[^>]*/>[ \t]*\n?', xml[body_start:body_end])
    if m:
        at = body_start + m.end()
    else:
        # No marker (some chapters omit them); fall back to the verse element.
        mv = re.search(r'[ \t]*<v n="' + str(verse) + r'"[ >]', xml[body_start:body_end])
        if not mv:
            report['no_anchor'] += 1
            return xml
        at = body_start + mv.start()
    if occupied(xml, at):
        # A heading is already anchored here — the wording just differs between
        # our import source and the fetch source. Keep what shipped; adding ours
        # would show the reader the same heading twice.
        report['anchor_occupied'] += 1
        return xml
    indent = re.match(r'[ \t]*', xml[at:]).group(0) or '\t\t\t'
    report['inserted'] += 1
    return xml[:at] + f'{indent}{tag}\n' + xml[at:]


def heading_anchors(xml):
    """[(verse, text)] for headings already in the file, by the <v> each precedes."""
    out = []
    for m in re.finditer(r'<heading>(.*?)</heading>', xml, re.S):
        nxt = re.search(r'<v n="(\d+)"', xml[m.end():])
        if nxt:
            out.append((int(nxt.group(1)), re.sub(r'\s+', ' ', m.group(1)).strip()))
    return out


def existing_headings(xml):
    return [re.sub(r'\s+', ' ', h).strip()
            for h in re.findall(r'<heading>(.*?)</heading>', xml, re.S)]


def drop_bogus_titles(xml, book_name, chapter, report):
    """ESV captured the chapter title ('Proverbs 1') as a section heading."""
    want = normalise(f'{book_name} {chapter}')

    def repl(m):
        if normalise(m.group(1)) == want:
            report['bogus_removed'] += 1
            return ''
        return m.group(0)

    return re.sub(r'[ \t]*<heading>(.*?)</heading>[ \t]*\n?', repl, xml, flags=re.S)


def process_version(version, apply_changes, only_book=None):
    cache = Path(f'raw/headings/{version}.json')
    if not cache.exists():
        print(f'{version}: no cache at {cache} — run fetch_headings.py first')
        return
    data = json.loads(cache.read_text())
    report = Counter()
    changed_files = 0

    for key, headings in sorted(data.items()):
        slug, chapter = key.rsplit('_', 1)
        chapter = int(chapter)
        if only_book and slug != only_book:
            continue
        path = Path(f'xml_{version}/{slug}_{chapter}.xml')
        if not path.exists():
            report['missing_file'] += 1
            continue
        book_name, booknum = BOOK_BY_SLUG[slug]
        original = xml = path.read_text(encoding='utf-8')

        if version == 'esv':
            xml = drop_bogus_titles(xml, book_name, chapter, report)

        # A heading the import kept but anchored to the wrong verse is skipped as
        # "already present"; count those so they are visible rather than silent.
        anchored = {normalise(h): v for v, h in heading_anchors(xml)}
        for verse, text in headings:
            at = anchored.get(normalise(re.sub(r'\s+', ' ', text).strip()))
            if at is not None and at != verse:
                report['present_but_misplaced'] += 1

        have = {normalise(h) for h in existing_headings(xml)}
        for verse, text in headings:
            text = re.sub(r'\s+', ' ', text).strip()
            if not text:
                continue
            key_n = normalise(text)
            xml = strip_glued(xml, text, report)
            if key_n in have:
                report['already_present'] += 1
                continue
            xml = insert_heading(xml, booknum, chapter, verse, text, report)
            have.add(key_n)

        if xml != original:
            changed_files += 1
            if apply_changes:
                path.write_text(xml, encoding='utf-8')

    verb = 'applied' if apply_changes else 'DRY RUN'
    print(f'{version}: {verb} — {changed_files} files changed; ' +
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
