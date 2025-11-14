#!/usr/bin/env python3
"""
Extract NKJV Bible text from PDF and split into chapter files.
"""

import re
from pathlib import Path
import pdfplumber

# Bible book structure: (book_name, number_of_chapters, testament)
BIBLE_STRUCTURE = [
    # Old Testament
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
    # New Testament
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

def extract_pdf_text(pdf_path):
    """Extract all text from PDF."""
    print(f"Opening PDF: {pdf_path}")
    
    full_text = []
    with pdfplumber.open(pdf_path) as pdf:
        total_pages = len(pdf.pages)
        print(f"Total pages: {total_pages}")
        
        for i, page in enumerate(pdf.pages):
            if (i + 1) % 50 == 0:
                print(f"  Processing page {i + 1}/{total_pages}...")
            
            text = page.extract_text()
            if text:
                full_text.append(text)
    
    return '\n'.join(full_text)

def find_chapter_boundaries(text):
    """Find chapter boundaries in the extracted text."""
    # Look for patterns like "GENESIS 1", "EXODUS 12", etc.
    # or verse 1 at the start of a new chapter
    
    chapter_pattern = re.compile(
        r'(?:^|\n)([A-Z12 ]+)\s+(\d+)\s*\n\s*1\s+',
        re.MULTILINE
    )
    
    matches = list(chapter_pattern.finditer(text))
    print(f"Found {len(matches)} potential chapter markers")
    
    return matches

def split_chapters_from_pdf(pdf_path):
    """Extract and split Bible chapters from PDF."""
    
    # Create output directories
    ot_dir = Path('raw/chapter_texts_nkjv_ot')
    nt_dir = Path('raw/chapter_texts_nkjv_nt')
    ot_dir.mkdir(parents=True, exist_ok=True)
    nt_dir.mkdir(parents=True, exist_ok=True)
    
    # Extract PDF text
    text = extract_pdf_text(pdf_path)
    
    print(f"\nExtracted {len(text)} characters")
    
    # Save full extracted text for inspection
    debug_file = Path('raw/nkjv_pdf_extracted.txt')
    with open(debug_file, 'w', encoding='utf-8') as f:
        f.write(text)
    print(f"Saved extracted text to: {debug_file}")
    
    # Find chapter boundaries
    matches = find_chapter_boundaries(text)
    
    # Build chapter mapping
    chapter_to_book = {}
    global_chapter = 1
    
    for book_name, num_chapters, testament in BIBLE_STRUCTURE:
        for local_chapter in range(1, num_chapters + 1):
            chapter_to_book[global_chapter] = (book_name, local_chapter, testament)
            global_chapter += 1
    
    # Extract chapters
    chapters_created = 0
    
    for i, match in enumerate(matches):
        book_name_raw = match.group(1).strip()
        chapter_num = int(match.group(2))
        
        # Get content
        start = match.end()
        if i + 1 < len(matches):
            end = matches[i + 1].start()
        else:
            end = len(text)
        
        chapter_content = text[start:end].strip()
        
        # Try to match book name
        book_name_normalized = book_name_raw.lower().replace(' ', '_')
        
        # Find matching book in structure
        for book, num_chaps, testament in BIBLE_STRUCTURE:
            if book.replace('_', '') in book_name_normalized.replace('_', ''):
                output_dir = ot_dir if testament == 'ot' else nt_dir
                filename = f"{book}_{chapter_num}.txt"
                filepath = output_dir / filename
                
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(chapter_content)
                
                chapters_created += 1
                break
    
    return chapters_created

def main():
    print("=" * 80)
    print("EXTRACTING NKJV FROM PDF")
    print("=" * 80)
    print()
    
    pdf_path = 'assets/new-king-james-version-en.pdf'
    
    if not Path(pdf_path).exists():
        print(f"Error: PDF not found: {pdf_path}")
        return
    
    total = split_chapters_from_pdf(pdf_path)
    
    print()
    print(f"✓ Created {total} chapter files")
    print()
    print("=" * 80)
    print("COMPLETE")
    print("=" * 80)

if __name__ == '__main__':
    main()
