#!/usr/bin/env python3
"""
Split NKJV full text into individual chapter files.
Creates two directories:
- raw/chapter_texts_nkjv_nt/ for New Testament chapters
- raw/chapter_texts_nkjv_ot/ for Old Testament chapters
"""

import re
from pathlib import Path

# Book name mappings and testament classification
BOOKS = {
    # Old Testament
    'Genesis': ('genesis', 50, 'ot'),
    'Exodus': ('exodus', 40, 'ot'),
    'Leviticus': ('leviticus', 27, 'ot'),
    'Numbers': ('numbers', 36, 'ot'),
    'Deuteronomy': ('deuteronomy', 34, 'ot'),
    'Joshua': ('joshua', 24, 'ot'),
    'Judges': ('judges', 21, 'ot'),
    'Ruth': ('ruth', 4, 'ot'),
    '1 Samuel': ('1_samuel', 31, 'ot'),
    '2 Samuel': ('2_samuel', 24, 'ot'),
    '1 Kings': ('1_kings', 22, 'ot'),
    '2 Kings': ('2_kings', 25, 'ot'),
    '1 Chronicles': ('1_chronicles', 29, 'ot'),
    '2 Chronicles': ('2_chronicles', 36, 'ot'),
    'Ezra': ('ezra', 10, 'ot'),
    'Nehemiah': ('nehemiah', 13, 'ot'),
    'Esther': ('esther', 10, 'ot'),
    'Job': ('job', 42, 'ot'),
    'Psalms': ('psalms', 150, 'ot'),
    'Proverbs': ('proverbs', 31, 'ot'),
    'Ecclesiastes': ('ecclesiastes', 12, 'ot'),
    'Song of Solomon': ('song_of_solomon', 8, 'ot'),
    'Isaiah': ('isaiah', 66, 'ot'),
    'Jeremiah': ('jeremiah', 52, 'ot'),
    'Lamentations': ('lamentations', 5, 'ot'),
    'Ezekiel': ('ezekiel', 48, 'ot'),
    'Daniel': ('daniel', 12, 'ot'),
    'Hosea': ('hosea', 14, 'ot'),
    'Joel': ('joel', 3, 'ot'),
    'Amos': ('amos', 9, 'ot'),
    'Obadiah': ('obadiah', 1, 'ot'),
    'Jonah': ('jonah', 4, 'ot'),
    'Micah': ('micah', 7, 'ot'),
    'Nahum': ('nahum', 3, 'ot'),
    'Habakkuk': ('habakkuk', 3, 'ot'),
    'Zephaniah': ('zephaniah', 3, 'ot'),
    'Haggai': ('haggai', 2, 'ot'),
    'Zechariah': ('zechariah', 14, 'ot'),
    'Malachi': ('malachi', 4, 'ot'),
    # New Testament
    'Matthew': ('matthew', 28, 'nt'),
    'Mark': ('mark', 16, 'nt'),
    'Luke': ('luke', 24, 'nt'),
    'John': ('john', 21, 'nt'),
    'Acts': ('acts', 28, 'nt'),
    'Romans': ('romans', 16, 'nt'),
    '1 Corinthians': ('1_corinthians', 16, 'nt'),
    '2 Corinthians': ('2_corinthians', 13, 'nt'),
    'Galatians': ('galatians', 6, 'nt'),
    'Ephesians': ('ephesians', 6, 'nt'),
    'Philippians': ('philippians', 4, 'nt'),
    'Colossians': ('colossians', 4, 'nt'),
    '1 Thessalonians': ('1_thessalonians', 5, 'nt'),
    '2 Thessalonians': ('2_thessalonians', 3, 'nt'),
    '1 Timothy': ('1_timothy', 6, 'nt'),
    '2 Timothy': ('2_timothy', 4, 'nt'),
    'Titus': ('titus', 3, 'nt'),
    'Philemon': ('philemon', 1, 'nt'),
    'Hebrews': ('hebrews', 13, 'nt'),
    'James': ('james', 5, 'nt'),
    '1 Peter': ('1_peter', 5, 'nt'),
    '2 Peter': ('2_peter', 3, 'nt'),
    '1 John': ('1_john', 5, 'nt'),
    '2 John': ('2_john', 1, 'nt'),
    '3 John': ('3_john', 1, 'nt'),
    'Jude': ('jude', 1, 'nt'),
    'Revelation': ('revelation', 22, 'nt'),
}

def find_book_chapter_sections(content):
    """
    Parse the NKJV full text and extract chapter sections.
    Returns dict of {(book_name, chapter_num): chapter_text}
    """
    chapters = {}
    
    # Look for chapter headings like "GENESIS 1:1" or book introductions
    # The format seems to be: book title, then verse numbers start
    
    current_book = None
    current_chapter = None
    current_text = []
    
    lines = content.split('\n')
    
    for i, line in enumerate(lines):
        # Check if this line starts a new chapter (e.g., "4\nGENESIS 1:1")
        # Look for pattern: number at start, possibly followed by book name and verse
        
        # Try to match book chapter header pattern
        # Pattern: "BOOK_NAME CHAPTER:VERSE"
        match = re.match(r'^([A-Z][A-Za-z\s]+)\s+(\d+):(\d+)', line)
        if match:
            # Save previous chapter
            if current_book and current_chapter and current_text:
                chapter_content = '\n'.join(current_text).strip()
                if chapter_content:
                    chapters[(current_book, current_chapter)] = chapter_content
            
            book_name = match.group(1).strip()
            chapter_num = int(match.group(2))
            
            # Find the book in our mapping
            for book_key, (file_name, max_chapters, testament) in BOOKS.items():
                if book_key.upper() == book_name or book_key.upper() in book_name:
                    current_book = file_name
                    current_chapter = chapter_num
                    current_text = [line]
                    break
        elif current_book:
            current_text.append(line)
    
    # Save last chapter
    if current_book and current_chapter and current_text:
        chapter_content = '\n'.join(current_text).strip()
        if chapter_content:
            chapters[(current_book, current_chapter)] = chapter_content
    
    return chapters

def extract_chapters_by_verse_numbers(content):
    """
    Alternative approach: find chapters by looking for verse number patterns.
    """
    chapters = {}
    
    lines = content.split('\n')
    
    # Find all lines that contain chapter:verse references
    for i, line in enumerate(lines):
        # Look for standalone numbers at start of line (verse numbers)
        # Format appears to be: "1 In the beginning..." where 1 is verse number
        
        # Check if line starts with a number followed by space and text
        verse_match = re.match(r'^(\d+)\s+([A-Z])', line)
        if verse_match:
            verse_num = int(verse_match.group(1))
            
            # If verse 1, this likely starts a new chapter
            if verse_num == 1:
                # Look backwards to find the book/chapter header
                for j in range(i-1, max(0, i-10), -1):
                    header_line = lines[j]
                    # Look for "BOOK CHAPTER:1" or similar
                    header_match = re.search(r'([A-Z][A-Za-z\s]+)\s+(\d+):', header_line)
                    if header_match:
                        book_name = header_match.group(1).strip()
                        chapter_num = int(header_match.group(2))
                        
                        # Map to our book names
                        for book_key, (file_name, max_chapters, testament) in BOOKS.items():
                            if book_key.upper() == book_name or book_name in book_key.upper():
                                # Collect chapter text until next chapter 1 or end
                                chapter_lines = []
                                for k in range(i, len(lines)):
                                    next_line = lines[k]
                                    # Stop at next chapter 1
                                    if k > i and re.match(r'^1\s+[A-Z]', next_line):
                                        break
                                    chapter_lines.append(next_line)
                                
                                chapter_text = '\n'.join(chapter_lines).strip()
                                if chapter_text:
                                    chapters[(file_name, chapter_num)] = chapter_text
                                break
                        break
    
    return chapters

def main():
    input_file = Path('raw/nkjv_full_text.txt')
    ot_dir = Path('raw/chapter_texts_nkjv_ot')
    nt_dir = Path('raw/chapter_texts_nkjv_nt')
    
    # Create directories
    ot_dir.mkdir(parents=True, exist_ok=True)
    nt_dir.mkdir(parents=True, exist_ok=True)
    
    print("=" * 80)
    print("SPLITTING NKJV FULL TEXT INTO CHAPTER FILES")
    print("=" * 80)
    print()
    
    # Read full text
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Try to extract chapters
    print("Parsing NKJV text...")
    chapters = extract_chapters_by_verse_numbers(content)
    
    if not chapters:
        print("First method didn't work, trying alternative...")
        chapters = find_book_chapter_sections(content)
    
    print(f"Found {len(chapters)} chapters")
    print()
    
    # Write chapter files
    ot_count = 0
    nt_count = 0
    
    for (book_name, chapter_num), chapter_text in sorted(chapters.items()):
        # Determine testament
        testament = None
        for book_key, (file_name, max_chapters, test) in BOOKS.items():
            if file_name == book_name:
                testament = test
                break
        
        if not testament:
            continue
        
        # Choose directory
        output_dir = nt_dir if testament == 'nt' else ot_dir
        
        # Write file
        output_file = output_dir / f"{book_name}_{chapter_num}.txt"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(chapter_text)
        
        if testament == 'ot':
            ot_count += 1
        else:
            nt_count += 1
    
    print("=" * 80)
    print(f"SUMMARY")
    print(f"Old Testament chapters: {ot_count}")
    print(f"New Testament chapters: {nt_count}")
    print(f"Total chapters: {ot_count + nt_count}")
    print()
    print(f"OT chapters saved to: {ot_dir}")
    print(f"NT chapters saved to: {nt_dir}")
    print("=" * 80)

if __name__ == '__main__':
    main()
