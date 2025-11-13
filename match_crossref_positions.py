#!/usr/bin/env python3
"""
Extract cross-reference positions from ESV Study Bible PDF by matching verse text.
This will identify WHERE each cross-reference letter appears in the verse text.
"""

import pdfplumber
import re
from pathlib import Path
import xml.etree.ElementTree as ET
from collections import defaultdict

def extract_pdf_text(pdf_path, start_page, end_page):
    """Extract text from PDF pages."""
    with pdfplumber.open(pdf_path) as pdf:
        text = ""
        for page_num in range(start_page, end_page + 1):
            if page_num < len(pdf.pages):
                page = pdf.pages[page_num]
                text += page.extract_text() + " "
        return text

def parse_verse_with_crossrefs(text, chapter_num):
    """
    Parse verses from PDF text and identify cross-reference positions.
    Returns dict with verse numbers and their cross-reference positions.
    """
    verses_with_refs = {}
    
    # Find all verses in the chapter
    # Format: "verse_num[†]text with letters scattered in it"
    # The [†] marker indicates a verse with study notes
    
    # First, clean up the text - remove page numbers, headers
    text = re.sub(r'\d{4}\s+JOHN', '', text)
    text = re.sub(r'ESV STUDY BIBLE', '', text)
    
    # Pattern to match verse numbers followed by optional [†] and text
    # We'll look for: number possibly followed by [†] then text until next verse
    verse_pattern = rf'(\d+)\[?†?\]?\s+(.+?)(?=\s+\d+\[?†?\]?\s+|$)'
    
    matches = re.finditer(verse_pattern, text)
    
    for match in matches:
        verse_num = int(match.group(1))
        verse_text = match.group(2).strip()
        
        # Don't process verse numbers that are too high (likely not part of this chapter)
        if verse_num > 100:
            continue
        
        # Extract cross-reference letters and their positions
        # Letters appear as single lowercase letters, often between words
        verse_words = []
        current_pos = 0
        
        # Split by whitespace but keep track of positions
        for word_match in re.finditer(r'\S+', verse_text):
            word = word_match.group()
            word_start = word_match.start()
            
            # Check if this word contains a single lowercase letter
            # that might be a cross-reference marker
            single_letter_pattern = r'\b([a-z])\b'
            letter_matches = list(re.finditer(single_letter_pattern, word))
            
            verse_words.append({
                'word': word,
                'position': word_start,
                'letters': [m.group(1) for m in letter_matches]
            })
        
        if verse_words:
            verses_with_refs[verse_num] = {
                'text': verse_text,
                'words': verse_words
            }
    
    return verses_with_refs

def get_xml_verse_text(xml_file, verse_num):
    """Extract the text content of a verse from XML."""
    tree = ET.parse(xml_file)
    root = tree.getroot()
    
    # Find the verse
    for v_elem in root.findall('.//v[@n="{}"]'.format(verse_num)):
        # Get all text content, including after crossrefs
        text = ''.join(v_elem.itertext())
        return text.strip()
    return None

def find_crossref_positions_by_matching(pdf_path, xml_dir, book_name, chapter_num, pdf_pages):
    """
    Match XML verse text with PDF text to find where cross-refs should be inserted.
    """
    print(f"Processing {book_name} {chapter_num}...")
    
    # Extract PDF text
    pdf_text = extract_pdf_text(pdf_path, pdf_pages[0], pdf_pages[1])
    
    # Parse verses with cross-references from PDF
    pdf_verses = parse_verse_with_crossrefs(pdf_text, chapter_num)
    
    # Get XML file
    xml_filename = f"{book_name.lower().replace(' ', '_')}_{chapter_num}.xml"
    xml_file = xml_dir / xml_filename
    
    if not xml_file.exists():
        print(f"  Warning: {xml_file} not found")
        return {}
    
    # Load expected cross-references from our complete list
    complete_file = Path('esv_crossrefs_complete.txt')
    text = complete_file.read_text(encoding='utf-8')
    
    book_pattern = f'Cross-references for {book_name}'
    start = text.find(book_pattern)
    next_book = text.find('Cross-references for', start + len(book_pattern))
    section = text[start:next_book] if next_book != -1 else text[start:]
    
    expected_refs = defaultdict(list)
    pattern = rf'{chapter_num}:(\d+)\s+([a-z])\s+'
    matches = re.finditer(pattern, section)
    for match in matches:
        verse_num = int(match.group(1))
        letter = match.group(2)
        expected_refs[verse_num].append(letter)
    
    # Analyze each verse
    results = {}
    
    for verse_num, expected_letters in sorted(expected_refs.items()):
        xml_text = get_xml_verse_text(xml_file, verse_num)
        pdf_data = pdf_verses.get(verse_num)
        
        if xml_text and pdf_data:
            print(f"\n  Verse {verse_num}:")
            print(f"    Expected letters: {', '.join(expected_letters)}")
            print(f"    XML text: {xml_text[:100]}...")
            print(f"    PDF text: {pdf_data['text'][:100]}...")
            
            # Try to match letters in PDF text
            pdf_letters = []
            for word_info in pdf_data['words']:
                pdf_letters.extend(word_info['letters'])
            
            print(f"    Found in PDF: {', '.join(pdf_letters)}")
            
            results[verse_num] = {
                'expected': expected_letters,
                'xml_text': xml_text,
                'pdf_text': pdf_data['text'],
                'pdf_letters': pdf_letters
            }
    
    return results

def main():
    pdf_path = Path('raw/ESV Global Study Bible - Crossway Bibles-3.pdf')
    xml_dir = Path('xml_esv')
    
    if not pdf_path.exists():
        print(f"Error: PDF not found at {pdf_path}")
        return
    
    # Test with John 7
    results = find_crossref_positions_by_matching(
        pdf_path,
        xml_dir,
        'John',
        7,
        (3934, 3936)  # Pages for John 7
    )
    
    print(f"\n\nProcessed {len(results)} verses")

if __name__ == '__main__':
    main()
