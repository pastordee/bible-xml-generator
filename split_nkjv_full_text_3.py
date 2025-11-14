#!/usr/bin/env python3
"""
Split nkjv_full_text_3.txt into individual chapter files using CHAPTER N markers.
Uses Bible book structure to determine which chapters belong to which book.
"""

import re
from pathlib import Path

# Bible book structure: (book_name, number_of_chapters, testament)
BIBLE_STRUCTURE = [
    # Old Testament
    ('genesis', 50, 'ot'),
    ('exodus', 40, 'ot'),
    ('leviticus', 27, 'ot'),
    ('numbers', 36, 'ot'),
    ('deuteronomy', 34, 'ot'),
    ('joshua', 24, 'ot'),
    ('judges', 21, 'ot'),
    ('ruth', 4, 'ot'),
    ('1_samuel', 31, 'ot'),
    ('2_samuel', 24, 'ot'),
    ('1_kings', 22, 'ot'),
    ('2_kings', 25, 'ot'),
    ('1_chronicles', 29, 'ot'),
    ('2_chronicles', 36, 'ot'),
    ('ezra', 10, 'ot'),
    ('nehemiah', 13, 'ot'),
    ('esther', 10, 'ot'),
    ('job', 42, 'ot'),
    ('psalms', 150, 'ot'),
    ('proverbs', 31, 'ot'),
    ('ecclesiastes', 12, 'ot'),
    ('song_of_solomon', 8, 'ot'),
    ('isaiah', 66, 'ot'),
    ('jeremiah', 52, 'ot'),
    ('lamentations', 5, 'ot'),
    ('ezekiel', 48, 'ot'),
    ('daniel', 12, 'ot'),
    ('hosea', 14, 'ot'),
    ('joel', 3, 'ot'),
    ('amos', 9, 'ot'),
    ('obadiah', 1, 'ot'),
    ('jonah', 4, 'ot'),
    ('micah', 7, 'ot'),
    ('nahum', 3, 'ot'),
    ('habakkuk', 3, 'ot'),
    ('zephaniah', 3, 'ot'),
    ('haggai', 2, 'ot'),
    ('zechariah', 14, 'ot'),
    ('malachi', 4, 'ot'),
    # New Testament
    ('matthew', 28, 'nt'),
    ('mark', 16, 'nt'),
    ('luke', 24, 'nt'),
    ('john', 21, 'nt'),
    ('acts', 28, 'nt'),
    ('romans', 16, 'nt'),
    ('1_corinthians', 16, 'nt'),
    ('2_corinthians', 13, 'nt'),
    ('galatians', 6, 'nt'),
    ('ephesians', 6, 'nt'),
    ('philippians', 4, 'nt'),
    ('colossians', 4, 'nt'),
    ('1_thessalonians', 5, 'nt'),
    ('2_thessalonians', 3, 'nt'),
    ('1_timothy', 6, 'nt'),
    ('2_timothy', 4, 'nt'),
    ('titus', 3, 'nt'),
    ('philemon', 1, 'nt'),
    ('hebrews', 13, 'nt'),
    ('james', 5, 'nt'),
    ('1_peter', 5, 'nt'),
    ('2_peter', 3, 'nt'),
    ('1_john', 5, 'nt'),
    ('2_john', 1, 'nt'),
    ('3_john', 1, 'nt'),
    ('jude', 1, 'nt'),
    ('revelation', 22, 'nt')
]

def split_into_chapters(input_file):
    """Split NKJV file into individual chapter files based on CHAPTER N markers."""
    
    # Create output directories
    ot_dir = Path('raw/chapter_texts_nkjv_ot')
    nt_dir = Path('raw/chapter_texts_nkjv_nt')
    ot_dir.mkdir(parents=True, exist_ok=True)
    nt_dir.mkdir(parents=True, exist_ok=True)
    
    # Read entire file
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Split by "CHAPTER N" markers
    chapter_pattern = re.compile(r'^CHAPTER (\d+)$', re.MULTILINE)
    matches = list(chapter_pattern.finditer(content))
    
    print(f"Found {len(matches)} chapter markers")
    
    # Build chapter number to book mapping
    chapter_to_book = {}
    global_chapter = 1
    
    for book_name, num_chapters, testament in BIBLE_STRUCTURE:
        for local_chapter in range(1, num_chapters + 1):
            chapter_to_book[global_chapter] = (book_name, local_chapter, testament)
            global_chapter += 1
    
    print(f"Total chapters in Bible structure: {global_chapter - 1}")
    
    # Extract each chapter
    chapters_created = 0
    
    for i, match in enumerate(matches):
        chapter_num = int(match.group(1))
        
        # Get start position (right after the CHAPTER N line)
        start = match.end()
        
        # Get end position (start of next chapter or end of file)
        if i + 1 < len(matches):
            end = matches[i + 1].start()
        else:
            end = len(content)
        
        # Extract chapter content
        chapter_content = content[start:end].strip()
        
        # Determine which book this chapter belongs to
        if chapter_num in chapter_to_book:
            book_name, local_chapter, testament = chapter_to_book[chapter_num]
            
            # Choose output directory
            output_dir = ot_dir if testament == 'ot' else nt_dir
            
            # Create filename
            filename = f"{book_name}_{local_chapter}.txt"
            filepath = output_dir / filename
            
            # Write chapter file
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(chapter_content)
            
            chapters_created += 1
            
            if chapters_created % 100 == 0:
                print(f"  Created {chapters_created} chapter files...")
        else:
            print(f"  Warning: Chapter {chapter_num} exceeds Bible structure!")
    
    return chapters_created

def main():
    print("=" * 80)
    print("SPLITTING NKJV TEXT INTO CHAPTER FILES")
    print("=" * 80)
    print()
    
    input_file = 'raw/nkjv_full_text_3.txt'
    
    if not Path(input_file).exists():
        print(f"Error: File not found: {input_file}")
        return
    
    total = split_into_chapters(input_file)
    
    print()
    print(f"✓ Successfully created {total} chapter files")
    print(f"  - Old Testament: raw/chapter_texts_nkjv_ot/")
    print(f"  - New Testament: raw/chapter_texts_nkjv_nt/")
    print()
    print("=" * 80)
    print("COMPLETE")
    print("=" * 80)

if __name__ == '__main__':
    main()
