#!/usr/bin/env python3
"""
Normalize word-boundary spacing around inline <crossref> markers.

Some generators (notably the ESV and NKJV pipelines) insert a <crossref/> tag
between two words without preserving the space, producing data like:

    And the whole multitude<crossref let="u" cid="..."/>sought to...

When the app stitches the verse text together (the marker carries no text), the
two words glue into "multitudesought". This script inserts a single space
*after* the marker (so the marker hugs the preceding word and a space precedes
the following word) ONLY where both sides are word characters — versions that
already space their markers (e.g. KJV) are left untouched.

Run this as the final step after generating/rebuilding any version's chapter
XML. It is idempotent.

Usage:
    python3 fix_crossref_spacing.py <dir> [<dir> ...]          # dry run (report only)
    python3 fix_crossref_spacing.py --apply <dir> [<dir> ...]  # rewrite files
"""

import re
import sys
import glob
import os

# A word-char immediately before a self-closing <crossref ...> tag, immediately
# followed by another word-char => the boundary space was eaten. Insert it after
# the tag. [A-Za-z0-9] mirrors the app-side repair (MultiPartXmlBibleProvider).
JOIN_RE = re.compile(r'([A-Za-z0-9])(<crossref\b[^>]*/>)([A-Za-z0-9])')


def repair_text(xml_text: str) -> tuple[str, int]:
    """Return (repaired_text, num_fixes). Idempotent."""
    # Use a function replacement and loop until stable so runs of adjacent
    # markers are all handled (each pass fixes non-overlapping matches).
    total = 0
    while True:
        new_text, n = JOIN_RE.subn(r'\1\2 \3', xml_text)
        total += n
        xml_text = new_text
        if n == 0:
            break
    return xml_text, total


def process_dir(directory: str, apply: bool) -> tuple[int, int]:
    """Process every *.xml chapter file in a version directory (top level)."""
    files = sorted(glob.glob(os.path.join(directory, '*.xml')))
    files_changed = 0
    total_fixes = 0
    for path in files:
        with open(path, 'r', encoding='utf-8', errors='replace') as fh:
            original = fh.read()
        repaired, n = repair_text(original)
        if n > 0:
            files_changed += 1
            total_fixes += n
            if apply:
                with open(path, 'w', encoding='utf-8') as fh:
                    fh.write(repaired)
    return files_changed, total_fixes


def main():
    args = sys.argv[1:]
    apply = False
    if args and args[0] == '--apply':
        apply = True
        args = args[1:]
    if not args:
        print(__doc__)
        sys.exit(1)

    mode = 'APPLY' if apply else 'DRY RUN'
    print(f"=== crossref spacing normalizer ({mode}) ===\n")
    grand_files = 0
    grand_fixes = 0
    for directory in args:
        if not os.path.isdir(directory):
            print(f"  ⚠ skip (not a directory): {directory}")
            continue
        files_changed, total_fixes = process_dir(directory, apply)
        grand_files += files_changed
        grand_fixes += total_fixes
        verb = 'fixed' if apply else 'would fix'
        print(f"  {directory:12s} {verb} {total_fixes:6d} joins across {files_changed} files")
    print(f"\n  TOTAL: {grand_fixes} joins across {grand_files} files")
    if not apply and grand_fixes:
        print("\n  (dry run — re-run with --apply to write changes)")


if __name__ == '__main__':
    main()
