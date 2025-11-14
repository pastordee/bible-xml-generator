#!/usr/bin/env python3
"""
Split NKJV OT and NT files into individual chapter files.
Creates:
- raw/chapter_texts_nkjv_ot/ for Old Testament chapters
- raw/chapter_texts_nkjv_nt/ for New Testament chapters
"""

import re
from pathlib import Path

# Book name mappings (full name to abbreviation)
BOOK_MAPPINGS = {
    # Old Testament
    'genesis': 'genesis',
    'exodus': 'exodus',
    'leviticus': 'leviticus',
    'numbers': 'numbers',
    'deuteronomy': 'deuteronomy',
    'joshua': 'joshua',
    'judges': 'judges',
    'ruth': 'ruth',
    '1 samuel': '1_samuel',
    '2 samuel': '2_samuel',
    '1 kings': '1_kings',
    '2 kings': '2_kings',
    '1 chronicles': '1_chronicles',
    '2 chronicles': '2_chronicles',
    'ezra': 'ezra',
    'nehemiah': 'nehemiah',
    'esther': 'esther',
    'job': 'job',
    'psalms': 'psalms',
    'proverbs': 'proverbs',
    'ecclesiastes': 'ecclesiastes',
    'song of solomon': 'song_of_solomon',
    'isaiah': 'isaiah',
    'jeremiah': 'jeremiah',
    'lamentations': 'lamentations',
    'ezekiel': 'ezekiel',
    'daniel': 'daniel',
    'hosea': 'hosea',
    'joel': 'joel',
    'amos': 'amos',
    'obadiah': 'obadiah',
    'jonah': 'jonah',
    'micah': 'micah',
    'nahum': 'nahum',
    'habakkuk': 'habakkuk',
    'zephaniah': 'zephaniah',
    'haggai': 'haggai',
    'zechariah': 'zechariah',
    'malachi': 'malachi',
    # New Testament
    'matthew': 'matthew',
    'mark': 'mark',
    'luke': 'luke',
    'john': 'john',
    'acts': 'acts',
    'romans': 'romans',
    '1 corinthians': '1_corinthians',
    '2 corinthians': '2_corinthians',
    'galatians': 'galatians',
    'ephesians': 'ephesians',
    'philippians': 'philippians',
    'colossians': 'colossians',
    '1 thessalonians': '1_thessalonians',
    '2 thessalonians': '2_thessalonians',
    '1 timothy': '1_timothy',
    '2 timothy': '2_timothy',
    'titus': 'titus',
    'philemon': 'philemon',
    'hebrews': 'hebrews',
    'james': 'james',
    '1 peter': '1_peter',
    '2 peter': '2_peter',
    '1 john': '1_john',
    '2 john': '2_john',
    '3 john': '3_john',
    'jude': 'jude',
    'revelation': 'revelation'
}

def extract_book_name(line):
    """Extract book name from chapter marker (must be at start of line, not in notes)."""
    line_stripped = line.strip()
    
    # Must be EXACTLY a chapter marker format: "BOOKNAME C:V" at start of line
    # Should not have lowercase letters before it (which would indicate it's in notes/references)
    match = re.match(r'^([A-Z][A-Z\s]+?)\s+(\d+):(\d+)$', line_stripped)
    if match:
        book_name = match.group(1).strip().lower()
        chapter_num = match.group(2)
        verse_num = match.group(3)
        
        # Handle numbered books (e.g., "1 SAMUEL" -> "1 samuel")
        book_name = re.sub(r'(\d)\s+', r'\1 ', book_name)
        
        # Only accept if this is verse 1 (chapter start markers)
        if verse_num == '1':
            return book_name, chapter_num
    
    return None, None

def split_into_chapters(input_file, output_dir):
    """Split NKJV file into individual chapter files."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    lines = content.split('\n')
    
    current_book = None
    current_chapter = None
    chapter_content = []
    chapters_created = 0
    
    i = 0
    while i < len(lines):
        line = lines[i]
        
        # Check if line starts a new chapter (e.g., "GENESIS 1:1" or "MATTHEW 1:1")
        book_name, chapter_num = extract_book_name(line)
        if book_name and book_name in BOOK_MAPPINGS:
            # Save previous chapter if exists
            if current_book and current_chapter and chapter_content:
                book_abbr = BOOK_MAPPINGS[current_book]
                chapter_file = output_dir / f"{book_abbr}_{current_chapter}.txt"
                
                with open(chapter_file, 'w', encoding='utf-8') as f:
                    f.write('\n'.join(chapter_content))
                
                chapters_created += 1
                if chapters_created % 50 == 0:
                    print(f"  Created {chapters_created} chapter files...")
            
            # Start new chapter
            current_book = book_name
            current_chapter = chapter_num
            chapter_content = [line]
            i += 1
            continue
        
        # Add line to current chapter
        if current_chapter:
            chapter_content.append(line)
        
        i += 1
    
    # Save last chapter
    if current_book and current_chapter and chapter_content:
        book_abbr = BOOK_MAPPINGS[current_book]
        chapter_file = output_dir / f"{book_abbr}_{current_chapter}.txt"
        
        with open(chapter_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(chapter_content))
        
        chapters_created += 1
    
    return chapters_created

def main():
    print("=" * 80)
    print("SPLITTING NKJV INTO CHAPTER FILES")
    print("=" * 80)
    print()
    
    # Process Old Testament
    print("Processing Old Testament...")
    ot_file = 'raw/nkjv_full_text_ot.txt'
    ot_output = 'raw/chapter_texts_nkjv_ot'
    
    if Path(ot_file).exists():
        ot_count = split_into_chapters(ot_file, ot_output)
        print(f"  ✓ Created {ot_count} OT chapter files in {ot_output}/")
    else:
        print(f"  ✗ File not found: {ot_file}")
    
    print()
    
    # Process New Testament
    print("Processing New Testament...")
    nt_file = 'raw/nkjv_full_text_nt.txt'
    nt_output = 'raw/chapter_texts_nkjv_nt'
    
    if Path(nt_file).exists():
        nt_count = split_into_chapters(nt_file, nt_output)
        print(f"  ✓ Created {nt_count} NT chapter files in {nt_output}/")
    else:
        print(f"  ✗ File not found: {nt_file}")
    
    print()
    print("=" * 80)
    print("COMPLETE")
    print("=" * 80)

if __name__ == '__main__':
    main()
