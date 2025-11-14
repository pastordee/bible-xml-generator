#!/usr/bin/env python3
"""
Split NKJV OT/NT text files into chapter files by detecting chapter boundaries.
Uses "BOOK C:V" markers where they exist, and verse number patterns elsewhere.
"""

import re
from pathlib import Path

# Bible structure
BIBLE_STRUCTURE = [
    ('genesis', 50, 'ot'), ('exodus', 40, 'ot'), ('leviticus', 27, 'ot'),
    ('numbers', 36, 'ot'), ('deuteronomy', 34, 'ot'), ('joshua', 24, 'ot'),
    ('judges', 21, 'ot'), ('ruth', 4, 'ot'), ('1_samuel', 31, 'ot'),
    ('2_samuel', 24, 'ot'), ('1_kings', 22, 'ot'), ('2_kings', 25, 'ot'),
    ('1_chronicles', 29, 'ot'), ('2_chronicles', 36, 'ot'), ('ezra', 10, 'ot'),
    ('nehemiah', 13, 'ot'), ('esther', 10, 'ot'), ('job', 42, 'ot'),
    ('psalms', 150, 'ot'), ('proverbs', 31, 'ot'), ('ecclesiastes', 12, 'ot'),
    ('song_of_solomon', 8, 'ot'), ('isaiah', 66, 'ot'), ('jeremiah', 52, 'ot'),
    ('lamentations', 5, 'ot'), ('ezekiel', 48, 'ot'), ('daniel', 12, 'ot'),
    ('hosea', 14, 'ot'), ('joel', 3, 'ot'), ('amos', 9, 'ot'),
    ('obadiah', 1, 'ot'), ('jonah', 4, 'ot'), ('micah', 7, 'ot'),
    ('nahum', 3, 'ot'), ('habakkuk', 3, 'ot'), ('zephaniah', 3, 'ot'),
    ('haggai', 2, 'ot'), ('zechariah', 14, 'ot'), ('malachi', 4, 'ot'),
    ('matthew', 28, 'nt'), ('mark', 16, 'nt'), ('luke', 24, 'nt'),
    ('john', 21, 'nt'), ('acts', 28, 'nt'), ('romans', 16, 'nt'),
    ('1_corinthians', 16, 'nt'), ('2_corinthians', 13, 'nt'),
    ('galatians', 6, 'nt'), ('ephesians', 6, 'nt'), ('philippians', 4, 'nt'),
    ('colossians', 4, 'nt'), ('1_thessalonians', 5, 'nt'),
    ('2_thessalonians', 3, 'nt'), ('1_timothy', 6, 'nt'), ('2_timothy', 4, 'nt'),
    ('titus', 3, 'nt'), ('philemon', 1, 'nt'), ('hebrews', 13, 'nt'),
    ('james', 5, 'nt'), ('1_peter', 5, 'nt'), ('2_peter', 3, 'nt'),
    ('1_john', 5, 'nt'), ('2_john', 1, 'nt'), ('3_john', 1, 'nt'),
    ('jude', 1, 'nt'), ('revelation', 22, 'nt')
]

# Book name mapping (various forms to canonical)
BOOK_NAME_MAP = {
    'genesis': 'genesis', 'exodus': 'exodus', 'leviticus': 'leviticus',
    'numbers': 'numbers', 'deuteronomy': 'deuteronomy', 'joshua': 'joshua',
    'judges': 'judges', 'ruth': 'ruth', '1 samuel': '1_samuel', '2 samuel': '2_samuel',
    '1 kings': '1_kings', '2 kings': '2_kings', '1 chronicles': '1_chronicles',
    '2 chronicles': '2_chronicles', 'ezra': 'ezra', 'nehemiah': 'nehemiah',
    'esther': 'esther', 'job': 'job', 'psalms': 'psalms', 'psalm': 'psalms',
    'proverbs': 'proverbs', 'ecclesiastes': 'ecclesiastes',
    'song of solomon': 'song_of_solomon', 'isaiah': 'isaiah',
    'jeremiah': 'jeremiah', 'lamentations': 'lamentations', 'ezekiel': 'ezekiel',
    'daniel': 'daniel', 'hosea': 'hosea', 'joel': 'joel', 'amos': 'amos',
    'obadiah': 'obadiah', 'jonah': 'jonah', 'micah': 'micah', 'nahum': 'nahum',
    'habakkuk': 'habakkuk', 'zephaniah': 'zephaniah', 'haggai': 'haggai',
    'zechariah': 'zechariah', 'malachi': 'malachi',
    'matthew': 'matthew', 'mark': 'mark', 'luke': 'luke', 'john': 'john',
    'acts': 'acts', 'romans': 'romans', '1 corinthians': '1_corinthians',
    '2 corinthians': '2_corinthians', 'galatians': 'galatians',
    'ephesians': 'ephesians', 'philippians': 'philippians',
    'colossians': 'colossians', '1 thessalonians': '1_thessalonians',
    '2 thessalonians': '2_thessalonians', '1 timothy': '1_timothy',
    '2 timothy': '2_timothy', 'titus': 'titus', 'philemon': 'philemon',
    'hebrews': 'hebrews', 'james': 'james', '1 peter': '1_peter',
    '2 peter': '2_peter', '1 john': '1_john', '2 john': '2_john',
    '3 john': '3_john', 'jude': 'jude', 'revelation': 'revelation'
}

def split_file(input_file, testament):
    """Split NKJV file into chapters."""
    
    with open(input_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Pattern: "BOOKNAME C:V" like "GENESIS 1:1" or "MATTHEW 5:1"
    chapter_marker_pattern = re.compile(r'^([A-Z\s]+)\s+(\d+):(\d+)\s*$')
    
    chapters = []
    current_book = None
    current_chapter = None
    chapter_lines = []
    
    for i, line in enumerate(lines):
        match = chapter_marker_pattern.match(line.strip())
        
        if match:
            book_raw = match.group(1).strip().lower()
            chapter_num = int(match.group(2))
            verse_num = int(match.group(3))
            
            # Only process if it's verse 1 (chapter start marker)
            if verse_num == 1 and book_raw in BOOK_NAME_MAP:
                # Save previous chapter
                if current_book and current_chapter and chapter_lines:
                    chapters.append({
                        'book': current_book,
                        'chapter': current_chapter,
                        'lines': chapter_lines,
                        'testament': testament
                    })
                
                # Start new chapter
                current_book = BOOK_NAME_MAP[book_raw]
                current_chapter = chapter_num
                chapter_lines = [line]
                continue
        
        # Add to current chapter
        if current_chapter:
            chapter_lines.append(line)
    
    # Save last chapter
    if current_book and current_chapter and chapter_lines:
        chapters.append({
            'book': current_book,
            'chapter': current_chapter,
            'lines': chapter_lines,
            'testament': testament
        })
    
    return chapters

def main():
    print("=" * 80)
    print("SPLITTING NKJV FILES INTO CHAPTERS")
    print("=" * 80)
    print()
    
    # Create output directories
    ot_dir = Path('raw/chapter_texts_nkjv_ot')
    nt_dir = Path('raw/chapter_texts_nkjv_nt')
    ot_dir.mkdir(parents=True, exist_ok=True)
    nt_dir.mkdir(parents=True, exist_ok=True)
    
    all_chapters = []
    
    # Process OT
    ot_file = 'raw/nkjv_full_text_ot.txt'
    if Path(ot_file).exists():
        print(f"Processing {ot_file}...")
        ot_chapters = split_file(ot_file, 'ot')
        all_chapters.extend(ot_chapters)
        print(f"  Found {len(ot_chapters)} OT chapters")
    
    # Process NT
    nt_file = 'raw/nkjv_full_text_nt.txt'
    if Path(nt_file).exists():
        print(f"Processing {nt_file}...")
        nt_chapters = split_file(nt_file, 'nt')
        all_chapters.extend(nt_chapters)
        print(f"  Found {len(nt_chapters)} NT chapters")
    
    print()
    print("Writing chapter files...")
    
    # Write all chapters
    for chapter in all_chapters:
        output_dir = ot_dir if chapter['testament'] == 'ot' else nt_dir
        filename = f"{chapter['book']}_{chapter['chapter']}.txt"
        filepath = output_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.writelines(chapter['lines'])
    
    print(f"✓ Created {len(all_chapters)} chapter files total")
    print(f"  - OT: {len([c for c in all_chapters if c['testament'] == 'ot'])} files in {ot_dir}/")
    print(f"  - NT: {len([c for c in all_chapters if c['testament'] == 'nt'])} files in {nt_dir}/")
    print()
    print("=" * 80)
    print("COMPLETE")
    print("=" * 80)

if __name__ == '__main__':
    main()
