#!/usr/bin/env python3
"""Download only CEV Bible version."""

import os
import time
from create_other_version_chapters import (
    fetch_bible_metadata, 
    fetch_api_bible_chapter_content, 
    create_detailed_chapter_xml, 
    save_xml_file
)

API_KEY = "pyExkJPN1XXpoJ39Xa8Xi"
VERSION = "CEV"

# Complete Bible book information
BOOKS = [
    # Old Testament
    {"id": 1, "num": 1, "title": "Genesis", "testament": "old", "abbr": "gen", "chapters": 50},
    {"id": 2, "num": 2, "title": "Exodus", "testament": "old", "abbr": "exo", "chapters": 40},
    {"id": 3, "num": 3, "title": "Leviticus", "testament": "old", "abbr": "lev", "chapters": 27},
    {"id": 4, "num": 4, "title": "Numbers", "testament": "old", "abbr": "num", "chapters": 36},
    {"id": 5, "num": 5, "title": "Deuteronomy", "testament": "old", "abbr": "deu", "chapters": 34},
    {"id": 6, "num": 6, "title": "Joshua", "testament": "old", "abbr": "jos", "chapters": 24},
    {"id": 7, "num": 7, "title": "Judges", "testament": "old", "abbr": "jdg", "chapters": 21},
    {"id": 8, "num": 8, "title": "Ruth", "testament": "old", "abbr": "rut", "chapters": 4},
    {"id": 9, "num": 9, "title": "1 Samuel", "testament": "old", "abbr": "1sa", "chapters": 31},
    {"id": 10, "num": 10, "title": "2 Samuel", "testament": "old", "abbr": "2sa", "chapters": 24},
    {"id": 11, "num": 11, "title": "1 Kings", "testament": "old", "abbr": "1ki", "chapters": 22},
    {"id": 12, "num": 12, "title": "2 Kings", "testament": "old", "abbr": "2ki", "chapters": 25},
    {"id": 13, "num": 13, "title": "1 Chronicles", "testament": "old", "abbr": "1ch", "chapters": 29},
    {"id": 14, "num": 14, "title": "2 Chronicles", "testament": "old", "abbr": "2ch", "chapters": 36},
    {"id": 15, "num": 15, "title": "Ezra", "testament": "old", "abbr": "ezr", "chapters": 10},
    {"id": 16, "num": 16, "title": "Nehemiah", "testament": "old", "abbr": "neh", "chapters": 13},
    {"id": 17, "num": 17, "title": "Esther", "testament": "old", "abbr": "est", "chapters": 10},
    {"id": 18, "num": 18, "title": "Job", "testament": "old", "abbr": "job", "chapters": 42},
    {"id": 19, "num": 19, "title": "Psalms", "testament": "old", "abbr": "psa", "chapters": 150},
    {"id": 20, "num": 20, "title": "Proverbs", "testament": "old", "abbr": "pro", "chapters": 31},
    {"id": 21, "num": 21, "title": "Ecclesiastes", "testament": "old", "abbr": "ecc", "chapters": 12},
    {"id": 22, "num": 22, "title": "Song of Solomon", "testament": "old", "abbr": "sng", "chapters": 8},
    {"id": 23, "num": 23, "title": "Isaiah", "testament": "old", "abbr": "isa", "chapters": 66},
    {"id": 24, "num": 24, "title": "Jeremiah", "testament": "old", "abbr": "jer", "chapters": 52},
    {"id": 25, "num": 25, "title": "Lamentations", "testament": "old", "abbr": "lam", "chapters": 5},
    {"id": 26, "num": 26, "title": "Ezekiel", "testament": "old", "abbr": "ezk", "chapters": 48},
    {"id": 27, "num": 27, "title": "Daniel", "testament": "old", "abbr": "dan", "chapters": 12},
    {"id": 28, "num": 28, "title": "Hosea", "testament": "old", "abbr": "hos", "chapters": 14},
    {"id": 29, "num": 29, "title": "Joel", "testament": "old", "abbr": "jol", "chapters": 3},
    {"id": 30, "num": 30, "title": "Amos", "testament": "old", "abbr": "amo", "chapters": 9},
    {"id": 31, "num": 31, "title": "Obadiah", "testament": "old", "abbr": "oba", "chapters": 1},
    {"id": 32, "num": 32, "title": "Jonah", "testament": "old", "abbr": "jon", "chapters": 4},
    {"id": 33, "num": 33, "title": "Micah", "testament": "old", "abbr": "mic", "chapters": 7},
    {"id": 34, "num": 34, "title": "Nahum", "testament": "old", "abbr": "nah", "chapters": 3},
    {"id": 35, "num": 35, "title": "Habakkuk", "testament": "old", "abbr": "hab", "chapters": 3},
    {"id": 36, "num": 36, "title": "Zephaniah", "testament": "old", "abbr": "zep", "chapters": 3},
    {"id": 37, "num": 37, "title": "Haggai", "testament": "old", "abbr": "hag", "chapters": 2},
    {"id": 38, "num": 38, "title": "Zechariah", "testament": "old", "abbr": "zec", "chapters": 14},
    {"id": 39, "num": 39, "title": "Malachi", "testament": "old", "abbr": "mal", "chapters": 4},
    # New Testament
    {"id": 40, "num": 40, "title": "Matthew", "testament": "new", "abbr": "mat", "chapters": 28},
    {"id": 41, "num": 41, "title": "Mark", "testament": "new", "abbr": "mrk", "chapters": 16},
    {"id": 42, "num": 42, "title": "Luke", "testament": "new", "abbr": "luk", "chapters": 24},
    {"id": 43, "num": 43, "title": "John", "testament": "new", "abbr": "jhn", "chapters": 21},
    {"id": 44, "num": 44, "title": "Acts", "testament": "new", "abbr": "act", "chapters": 28},
    {"id": 45, "num": 45, "title": "Romans", "testament": "new", "abbr": "rom", "chapters": 16},
    {"id": 46, "num": 46, "title": "1 Corinthians", "testament": "new", "abbr": "1co", "chapters": 16},
    {"id": 47, "num": 47, "title": "2 Corinthians", "testament": "new", "abbr": "2co", "chapters": 13},
    {"id": 48, "num": 48, "title": "Galatians", "testament": "new", "abbr": "gal", "chapters": 6},
    {"id": 49, "num": 49, "title": "Ephesians", "testament": "new", "abbr": "eph", "chapters": 6},
    {"id": 50, "num": 50, "title": "Philippians", "testament": "new", "abbr": "php", "chapters": 4},
    {"id": 51, "num": 51, "title": "Colossians", "testament": "new", "abbr": "col", "chapters": 4},
    {"id": 52, "num": 52, "title": "1 Thessalonians", "testament": "new", "abbr": "1th", "chapters": 5},
    {"id": 53, "num": 53, "title": "2 Thessalonians", "testament": "new", "abbr": "2th", "chapters": 3},
    {"id": 54, "num": 54, "title": "1 Timothy", "testament": "new", "abbr": "1ti", "chapters": 6},
    {"id": 55, "num": 55, "title": "2 Timothy", "testament": "new", "abbr": "2ti", "chapters": 4},
    {"id": 56, "num": 56, "title": "Titus", "testament": "new", "abbr": "tit", "chapters": 3},
    {"id": 57, "num": 57, "title": "Philemon", "testament": "new", "abbr": "phm", "chapters": 1},
    {"id": 58, "num": 58, "title": "Hebrews", "testament": "new", "abbr": "heb", "chapters": 13},
    {"id": 59, "num": 59, "title": "James", "testament": "new", "abbr": "jas", "chapters": 5},
    {"id": 60, "num": 60, "title": "1 Peter", "testament": "new", "abbr": "1pe", "chapters": 5},
    {"id": 61, "num": 61, "title": "2 Peter", "testament": "new", "abbr": "2pe", "chapters": 3},
    {"id": 62, "num": 62, "title": "1 John", "testament": "new", "abbr": "1jn", "chapters": 5},
    {"id": 63, "num": 63, "title": "2 John", "testament": "new", "abbr": "2jn", "chapters": 1},
    {"id": 64, "num": 64, "title": "3 John", "testament": "new", "abbr": "3jn", "chapters": 1},
    {"id": 65, "num": 65, "title": "Jude", "testament": "new", "abbr": "jud", "chapters": 1},
    {"id": 66, "num": 66, "title": "Revelation", "testament": "new", "abbr": "rev", "chapters": 22}
]

def count_existing_files(version):
    """Count how many files already exist for this version."""
    version_dir = version.lower()
    if not os.path.exists(version_dir):
        return 0
    return len([f for f in os.listdir(version_dir) if f.endswith('.xml')])

def main():
    print("="*60)
    print(f"DOWNLOADING {VERSION} ONLY")
    print("="*60)
    
    # Count existing files
    existing = count_existing_files(VERSION)
    total = sum(book['chapters'] for book in BOOKS)
    print(f"\n📊 Current Status: {existing}/{total} chapters ({existing*100//total}%)")
    
    # Fetch metadata
    print(f"\n📖 Fetching metadata for {VERSION}...")
    bible_metadata = fetch_bible_metadata(VERSION, API_KEY)
    if bible_metadata:
        print(f"✅ {bible_metadata.get('name')}")
    else:
        print(f"⚠️  Could not fetch metadata")
    
    # Create directory
    version_dir = VERSION.lower()
    os.makedirs(version_dir, exist_ok=True)
    
    # Download chapters
    chapters_downloaded = 0
    chapters_skipped = 0
    
    for book in BOOKS:
        print(f"\n📚 {book['title']} ({book['chapters']} chapters)")
        
        for chapter_num in range(1, book['chapters'] + 1):
            # Check if file exists
            safe_title = book['title'].lower().replace(' ', '_')
            output_file = os.path.join(version_dir, f"{safe_title}_{chapter_num}.xml")
            
            if os.path.exists(output_file):
                chapters_skipped += 1
                continue
            
            # Download chapter
            print(f"  📥 Chapter {chapter_num}...", end='', flush=True)
            
            content = fetch_api_bible_chapter_content(VERSION, book['abbr'], chapter_num, API_KEY)
            
            if content:
                xml_tree = create_detailed_chapter_xml(VERSION, book, chapter_num, content, bible_metadata)
                save_xml_file(xml_tree, output_file)
                print(" ✅")
                chapters_downloaded += 1
                time.sleep(2)  # 2 second delay
            else:
                print(" ⚠️  Skipped (not available)")
    
    print("\n" + "="*60)
    print(f"✅ {VERSION} Download Complete!")
    print(f"   Downloaded: {chapters_downloaded} new chapters")
    print(f"   Skipped: {chapters_skipped} existing chapters")
    print(f"   Total: {count_existing_files(VERSION)}/{total} chapters")
    print("="*60)

if __name__ == "__main__":
    main()
