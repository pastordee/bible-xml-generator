#!/usr/bin/env python3
"""Resume ESV Bible generation from a specified starting book (default: Acts).

This script will:
- Extract the ESV API key from `create_esv_version_chapters.py`
- Import helper functions from that module
- Resume downloading chapters from the specified starting book onward
- Retry transient failures (None responses) with exponential backoff
"""
import re
import os
import time
from pathlib import Path

# Import helpers from the ESV generator
from create_esv_version_chapters import fetch_esv_chapter_content, create_detailed_chapter_xml, save_xml_file

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ESV_DIR = os.path.join(BASE_DIR, "esv")
os.makedirs(ESV_DIR, exist_ok=True)

# Read ESV API key from the generator file (non-invasive)
def read_esv_api_key(generator_path):
    with open(generator_path, 'r') as f:
        txt = f.read()
    m = re.search(r'esv_api_key\s*=\s*["\']([A-Za-z0-9_\-]+)["\']', txt)
    if m:
        return m.group(1)
    return None

GENERATOR_PY = os.path.join(BASE_DIR, 'create_esv_version_chapters.py')
ESV_API_KEY = read_esv_api_key(GENERATOR_PY)
if not ESV_API_KEY:
    raise SystemExit('Could not read ESV API key from create_esv_version_chapters.py')

# Books to process from Acts onward
books_after_acts = [
    {"id":44, "title":"Acts", "abbr":"act", "testament":"new"},
    {"id":45, "title":"Romans", "abbr":"rom", "testament":"new"},
    {"id":46, "title":"1 Corinthians", "abbr":"1co", "testament":"new"},
    {"id":47, "title":"2 Corinthians", "abbr":"2co", "testament":"new"},
    {"id":48, "title":"Galatians", "abbr":"gal", "testament":"new"},
    {"id":49, "title":"Ephesians", "abbr":"eph", "testament":"new"},
    {"id":50, "title":"Philippians", "abbr":"php", "testament":"new"},
    {"id":51, "title":"Colossians", "abbr":"col", "testament":"new"},
    {"id":52, "title":"1 Thessalonians", "abbr":"1th", "testament":"new"},
    {"id":53, "title":"2 Thessalonians", "abbr":"2th", "testament":"new"},
    {"id":54, "title":"1 Timothy", "abbr":"1ti", "testament":"new"},
    {"id":55, "title":"2 Timothy", "abbr":"2ti", "testament":"new"},
    {"id":56, "title":"Titus", "abbr":"tit", "testament":"new"},
    {"id":57, "title":"Philemon", "abbr":"phm", "testament":"new"},
    {"id":58, "title":"Hebrews", "abbr":"heb", "testament":"new"},
    {"id":59, "title":"James", "abbr":"jas", "testament":"new"},
    {"id":60, "title":"1 Peter", "abbr":"1pe", "testament":"new"},
    {"id":61, "title":"2 Peter", "abbr":"2pe", "testament":"new"},
    {"id":62, "title":"1 John", "abbr":"1jn", "testament":"new"},
    {"id":63, "title":"2 John", "abbr":"2jn", "testament":"new"},
    {"id":64, "title":"3 John", "abbr":"3jn", "testament":"new"},
    {"id":65, "title":"Jude", "abbr":"jud", "testament":"new"},
    {"id":66, "title":"Revelation", "abbr":"rev", "testament":"new"},
]

# Chapter counts for the New Testament books (copied from generator)
chapter_counts = {
    "act": 28, "rom": 16, "1co": 16, "2co": 13, "gal": 6, "eph": 6,
    "php": 4, "col": 4, "1th": 5, "2th": 3, "1ti": 6, "2ti": 4,
    "tit": 3, "phm": 1, "heb": 13, "jas": 5, "1pe": 5, "2pe": 3,
    "1jn": 5, "2jn": 1, "3jn": 1, "jud": 1, "rev": 22
}

# Retry/backoff policy
MAX_RETRIES = 8
INITIAL_BACKOFF = 5  # seconds


def resume_esv(start_books=books_after_acts):
    print(f"Resuming ESV download from Acts onward ({len(start_books)} books)")
    for book in start_books:
        abbr = book['abbr']
        title = book['title']
        max_chapters = chapter_counts.get(abbr, 1)
        print(f"\nProcessing {title} ({abbr}) - {max_chapters} chapters")
        safe_title = title.lower().replace(' ', '_')

        for chapter_num in range(1, max_chapters + 1):
            out_path = os.path.join(ESV_DIR, f"{safe_title}_{chapter_num}.xml")
            if os.path.exists(out_path):
                print(f"  Skipping {title} {chapter_num} (already exists)")
                continue

            retries = 0
            backoff = INITIAL_BACKOFF
            while retries <= MAX_RETRIES:
                print(f"  Fetching {title} chapter {chapter_num} (try {retries+1})...")
                content = fetch_esv_chapter_content(abbr, chapter_num, ESV_API_KEY)
                if content:
                    # create_detailed_chapter_xml expects book_info with keys like 'num','id','title','testament','abbr'
                    book_info = {
                        'num': book.get('id', book.get('num', 0)),
                        'id': book.get('id', 0),
                        'title': book.get('title', title),
                        'testament': book.get('testament', 'new'),
                        'abbr': book.get('abbr', abbr)
                    }
                    xml_tree = create_detailed_chapter_xml(book_info, chapter_num, content)
                    save_xml_file(xml_tree, out_path)
                    time.sleep(1)  # polite delay
                    break
                else:
                    retries += 1
                    if retries > MAX_RETRIES:
                        print(f"  ✖ Failed after {MAX_RETRIES} retries: {title} {chapter_num}")
                        break
                    print(f"    - No content returned; backing off {backoff}s before retrying...")
                    time.sleep(backoff)
                    backoff = min(backoff * 2, 600)

    print("\nResume process completed.")

if __name__ == '__main__':
    resume_esv()
