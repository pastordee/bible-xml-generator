#!/usr/bin/env python3
"""Fetch Nahum (chapters 1-3) for selected versions and save XML files.
This script uses the helpers in create_other_version_chapters.py to fetch content
and to create/save XML files in the per-version folders (lowercase folder names).
"""
import os
import time
from create_other_version_chapters import (
    fetch_bible_metadata,
    fetch_api_bible_chapter_content,
    create_detailed_chapter_xml,
    save_xml_file
)

API_KEY = "pyExkJPN1XXpoJ39Xa8Xi"
# Versions to try (those that previously were missing Nahum)
VERSIONS = ["KJV", "WEB", "ASV", "BSB", "MSG", "NKJV", "AMP", "NLT"]

CHAPTERS = [1, 2, 3]

base_dir = os.path.dirname(os.path.abspath(__file__))

for version in VERSIONS:
    print(f"\n=== Processing {version} ===")
    version_dir = os.path.join(base_dir, version.lower())
    os.makedirs(version_dir, exist_ok=True)

    meta = fetch_bible_metadata(version, API_KEY)
    if meta:
        print(f"Metadata: {meta.get('name')} ({meta.get('abbreviation')})")
    else:
        print("  Could not fetch metadata; continuing but requests may fail.")

    for ch in CHAPTERS:
        safe_title = "nahum"
        out_file = os.path.join(version_dir, f"{safe_title}_{ch}.xml")
        if os.path.exists(out_file):
            print(f"  Skipping {version} Nahum {ch} (already exists)")
            continue

        print(f"  Fetching {version} Nahum {ch}...")
        content = fetch_api_bible_chapter_content(version, 'nah', ch, API_KEY)
        if content:
            # Build minimal book_info structure expected by create_detailed_chapter_xml
            book_info = {"id": 34, "num": 34, "title": "Nahum", "testament": "old", "abbr": "nah"}
            xml_tree = create_detailed_chapter_xml(version, book_info, ch, content, meta)
            save_xml_file(xml_tree, out_file)
            print(f"  Saved {out_file}")
        else:
            print(f"  Failed to fetch {version} Nahum {ch}")

        # short delay to avoid hammering API
        time.sleep(2)

print('\nDone.')
