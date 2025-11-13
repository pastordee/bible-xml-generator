#!/usr/bin/env python3
"""
Extract cross-reference positions from ESV Study Bible PDF.
This will show us WHERE in each verse the letter markers appear.
"""

import pdfplumber
import re
from pathlib import Path
from collections import defaultdict

def extract_chapter_with_positions(pdf_path, book_name, chapter_num, start_page, end_page):
    """
    Extract a chapter from PDF and identify cross-reference letter positions.
    Returns dict of {verse_num: [(letter, position, word_before)]}
    """
    print(f"\nExtracting {book_name} {chapter_num} from pages {start_page}-{end_page}...")
    
    with pdfplumber.open(pdf_path) as pdf:
        text = ""
        for page_num in range(start_page, end_page + 1):
            if page_num < len(pdf.pages):
                page = pdf.pages[page_num]
                text += page.extract_text() + "\n"
    
    # Look for verse pattern: number followed by text
    # Cross-references appear as superscript letters in the text
    verse_pattern = rf'{chapter_num}:(\d+)\s+(.+?)(?={chapter_num}:\d+|$)'
    
    crossref_positions = defaultdict(list)
    
    verses = re.finditer(verse_pattern, text, re.DOTALL)
    
    for match in verses:
        verse_num = int(match.group(1))
        verse_text = match.group(2).strip()
        
        # Look for single lowercase letters that might be cross-reference markers
        # They typically appear after words
        words = verse_text.split()
        
        for i, word in enumerate(words):
            # Check if word ends with a superscript letter or has letter markers
            # Pattern: word followed by single letter(s)
            letter_matches = re.findall(r'([a-z])(?=\s|,|\.|\)|;|$)', word)
            
            for letter in letter_matches:
                # Try to get the word before the marker
                word_clean = re.sub(r'[a-z]+$', '', word).strip('.,;:!?)(')
                
                if word_clean:
                    crossref_positions[verse_num].append({
                        'letter': letter,
                        'word_before': word_clean,
                        'context': ' '.join(words[max(0, i-2):min(len(words), i+3)])
                    })
    
    return crossref_positions

def compare_with_complete_refs(positions, book_name, chapter_num, complete_file):
    """
    Compare extracted positions with complete cross-reference list.
    """
    # Load complete cross-references
    text = Path(complete_file).read_text(encoding='utf-8')
    
    # Find the book section
    book_pattern = f'Cross-references for {book_name}'
    start = text.find(book_pattern)
    
    if start == -1:
        print(f"Could not find {book_name} in complete file")
        return
    
    # Find next book section
    next_book = text.find('Cross-references for', start + len(book_pattern))
    section = text[start:next_book] if next_book != -1 else text[start:]
    
    # Extract expected letters for this chapter
    expected_refs = defaultdict(list)
    pattern = rf'{chapter_num}:(\d+)\s+([a-z])\s+'
    
    matches = re.finditer(pattern, section)
    for match in matches:
        verse_num = int(match.group(1))
        letter = match.group(2)
        expected_refs[verse_num].append(letter)
    
    # Compare
    print(f"\n{book_name} {chapter_num} - Position Analysis:")
    print("="*80)
    
    for verse_num in sorted(expected_refs.keys()):
        expected = expected_refs[verse_num]
        found = positions.get(verse_num, [])
        found_letters = [f['letter'] for f in found]
        
        print(f"\nVerse {verse_num}:")
        print(f"  Expected: {', '.join(expected)}")
        print(f"  Found:    {', '.join(found_letters)}")
        
        if found:
            print(f"  Positions:")
            for pos in found:
                print(f"    {pos['letter']}: after '{pos['word_before']}' - context: {pos['context'][:60]}...")

def main():
    pdf_path = Path('raw/ESV Global Study Bible - Crossway Bibles-3.pdf')
    complete_file = Path('esv_crossrefs_complete.txt')
    
    if not pdf_path.exists():
        print(f"Error: PDF not found at {pdf_path}")
        return
    
    if not complete_file.exists():
        print(f"Error: Complete cross-reference file not found at {complete_file}")
        return
    
    # Test with John 7 first
    print("Testing with John 7...")
    print("="*80)
    
    # John 7 is around page 3936 (0-indexed: 3935)
    positions = extract_chapter_with_positions(
        pdf_path,
        'John',
        7,
        3934,  # Start page (0-indexed)
        3936   # End page (0-indexed)
    )
    
    print(f"\nExtracted {sum(len(v) for v in positions.values())} cross-reference positions")
    
    # Compare with complete list
    compare_with_complete_refs(positions, 'John', 7, complete_file)

if __name__ == '__main__':
    main()
