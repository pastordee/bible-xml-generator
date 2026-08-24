#!/usr/bin/env python3
"""Repair words jammed together where a line break was lost in generation.

The API.Bible-sourced versions concatenate poetry lines without a separator, so
verses read "is my shepherd;I shall not want." and "its riderHe has thrown into
the sea!". KJV and BBE, which come from elsewhere, are unaffected.

The fix inserts a single space at the boundary. It deliberately does NOT try to
restore line breaks: the reader renders a verse as flowing text, so a space is
what makes it correct there, and inventing line structure that the source no
longer carries would be guesswork.

Only text BETWEEN tags is touched. Attribute values are left alone — otherwise
bookAbbr="exo" and <name> would be rewritten, which is where the false
positives in a naive grep come from.

Usage:
    python3 fix_lost_linebreak_spacing.py --dry-run      # report only
    python3 fix_lost_linebreak_spacing.py                # apply
    python3 fix_lost_linebreak_spacing.py xml_nkjv       # one version
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent

# A lowercase letter or sentence punctuation, immediately followed by a
# capital. In running scripture that only happens where a separator was
# dropped.
#
# Digits are excluded from the left side on purpose: the metadata carries ISO
# timestamps like 2025-10-28T16:18:52.000Z, which sit in a text node and would
# otherwise be rewritten to "2025-10-28 T16...".
#
# The capital is not required to be followed by a lowercase letter, or "I", "A"
# and "O" would be missed — and they are exactly the words that open a line of
# a psalm ("shepherd;I shall not want").
JAM = re.compile(r'(?<=[a-z,;:!?])(?=[A-Z])')

# Splits a document into tags and the text between them, keeping both.
TAG_SPLIT = re.compile(r'(<[^>]*>)')
TAG_NAME = re.compile(r'<\s*(/?)\s*([A-Za-z_][\w.-]*)')

# Elements whose text is not scripture. Their contents are codes, dates and
# licence text — "engKJV" is a version identifier, not two jammed words, and
# rewriting it to "eng KJV" would corrupt every file in the version.
SKIP_ELEMENTS = {
    'abbreviation', 'name', 'last_updated', 'generated_date',
    'api_compliance', 'next_refresh_due', 'copyright', 'metadata',
    'generation_info',
}


def repair(xml_text):
    """Returns (fixed_text, number_of_insertions)."""
    parts = TAG_SPLIT.split(xml_text)
    fixed = 0
    skip_depth = 0
    for i, part in enumerate(parts):
        if part.startswith('<'):
            match = TAG_NAME.match(part)
            if match:
                closing, tag = match.group(1), match.group(2).lower()
                self_closing = part.rstrip().endswith('/>')
                if tag in SKIP_ELEMENTS and not self_closing:
                    skip_depth += -1 if closing else 1
                    skip_depth = max(skip_depth, 0)
            continue
        if skip_depth:
            continue
        repaired, n = JAM.subn(' ', part)
        if n:
            parts[i] = repaired
            fixed += n
    return ''.join(parts), fixed


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    dry_run = '--dry-run' in sys.argv
    targets = [ROOT / a for a in args] if args else sorted(ROOT.glob('xml_*'))

    grand_total = 0
    for version_dir in targets:
        if not version_dir.is_dir():
            continue
        files = sorted(version_dir.glob('*.xml'))
        changed_files = 0
        inserted = 0
        for path in files:
            original = path.read_text(encoding='utf-8')
            fixed_text, n = repair(original)
            if n:
                changed_files += 1
                inserted += n
                if not dry_run:
                    path.write_text(fixed_text, encoding='utf-8')
        grand_total += inserted
        if inserted:
            print(f'{version_dir.name:<14} files={len(files):<5} '
                  f'changed={changed_files:<5} spaces_inserted={inserted}')
    verb = 'would insert' if dry_run else 'inserted'
    print(f'\nTotal {verb}: {grand_total}')


if __name__ == '__main__':
    main()
