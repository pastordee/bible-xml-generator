#!/usr/bin/env python3
"""
Extract verse text with cross-reference positions from PDF.
Match against XML and insert cross-references at correct word positions.
"""

import pdfplumber
import re
from pathlib import Path
import xml.etree.ElementTree as ET
from difflib import SequenceMatcher

def clean_text(text):
    """Remove extra whitespace and normalize."""
    return re.sub(r'\s+', ' ', text).strip()

def extract_verse_from_pdf(pdf_path, page_num, verse_marker):
    """
    Extract a specific verse from PDF with cross-reference letters in position.
    Returns the raw text with letters embedded.
    """
    with pdfplumber.open(pdf_path) as pdf:
        if page_num >= len(pdf.pages):
            return None
        
        page = pdf.pages[page_num]
        text = page.extract_text()
        
        # Find the verse
        # Pattern: verse_marker followed by text until next verse or section
        pattern = rf'{verse_marker}[†]?\s+(.+?)(?=\d+[†]?\s+|[A-Z][a-z]+\s+\d+:\d+|$)'
        
        match = re.search(pattern, text, re.DOTALL)
        if match:
            verse_text = match.group(1).strip()
            # Clean up line breaks but preserve structure
            verse_text = re.sub(r'\n+', ' ', verse_text)
            return verse_text
    
    return None

def find_word_with_letter(pdf_text, letter):
    """
    Find the word that comes before a cross-reference letter in PDF text.
    Returns (word, position_in_text)
    """
    # Look for: word + optional punctuation + single letter + space/punctuation
    pattern = rf'(\w+[.,;:!?]?)\s*{letter}(?=\s|[.,;:!?]|\)|]|$)'
    
    matches = list(re.finditer(pattern, pdf_text, re.IGNORECASE))
    
    if matches:
        # Return the last word before the letter (most specific match)
        match = matches[-1]
        word = match.group(1).strip('.,;:!?()')
        return (word, match.start())
    
    return (None, -1)

def insert_crossref_at_word(verse_elem, word_to_find, letter, book_num, chapter, verse_num, sequence):
    """
    Insert cross-reference element after a specific word in the verse XML.
    """
    cid = f"c{book_num}{int(chapter):03d}{int(verse_num):03d}.{sequence}"
    
    # Walk through the verse element's text and tail content
    # This is complex because XML mixes text with elements
    
    def search_and_insert(elem, word, is_tail=False):
        """Recursively search text/tail and insert crossref."""
        text_attr = 'tail' if is_tail else 'text'
        text = getattr(elem, text_attr, None)
        
        if text and word.lower() in text.lower():
            # Find the word position
            word_pattern = rf'\b{re.escape(word)}\b'
            match = re.search(word_pattern, text, re.IGNORECASE)
            
            if match:
                # Split text at word end
                before = text[:match.end()]
                after = text[match.end():]
                
                # Create crossref element
                crossref = ET.Element('crossref', attrib={'let': letter, 'cid': cid})
                crossref.tail = after
                
                # Update the text
                setattr(elem, text_attr, before + '\n\t\t\t\t')
                
                # Insert crossref after current element
                if is_tail:
                    parent = verse_elem
                    idx = list(parent).index(elem) + 1
                    parent.insert(idx, crossref)
                else:
                    # Insert as first child
                    verse_elem.insert(0, crossref)
                
                return True
        
        return False
    
    # Try to find in verse text first
    if search_and_insert(verse_elem, word_to_find, False):
        return True
    
    # Try in all child elements' tails
    for child in verse_elem:
        if search_and_insert(child, word_to_find, True):
            return True
    
    return False

def process_verse(pdf_path, xml_file, book_num, chapter, verse_num, pdf_page, missing_letters):
    """
    Process one verse: extract from PDF, find positions, update XML.
    """
    print(f"\n  Processing verse {verse_num}...")
    
    # Extract verse from PDF
    verse_marker = f'{chapter}:{verse_num}'
    pdf_text = extract_verse_from_pdf(pdf_path, pdf_page, verse_marker)
    
    if not pdf_text:
        print(f"    Warning: Could not extract verse from PDF")
        return False
    
    print(f"    PDF text: {pdf_text[:100]}...")
    
    # Parse XML
    tree = ET.parse(xml_file)
    root = tree.getroot()
    verse_elem = root.find(f".//v[@n='{verse_num}']")
    
    if verse_elem is None:
        print(f"    Warning: Verse not found in XML")
        return False
    
    # Get current sequence number
    max_seq = 0
    for crossref in verse_elem.findall('.//crossref'):
        cid = crossref.get('cid', '')
        if cid and '.' in cid:
            try:
                seq = int(cid.split('.')[-1])
                max_seq = max(max_seq, seq)
            except ValueError:
                pass
    
    next_seq = max_seq + 1
    
    # For each missing letter, find its position and insert
    added = 0
    for letter in missing_letters:
        word, pos = find_word_with_letter(pdf_text, letter)
        
        if word:
            print(f"    Letter '{letter}' -> after word '{word}'")
            
            if insert_crossref_at_word(verse_elem, word, letter, book_num, chapter, verse_num, next_seq):
                added += 1
                next_seq += 1
            else:
                print(f"      Warning: Could not find '{word}' in XML to insert")
        else:
            print(f"    Warning: Could not find position for letter '{letter}' in PDF")
    
    if added > 0:
        # Save the file
        tree.write(xml_file, encoding='utf-8', xml_declaration=True)
        print(f"    ✓ Added {added} cross-references")
        return True
    
    return False

def main():
    print("="*80)
    print("POSITION-AWARE CROSS-REFERENCE INSERTION")
    print("="*80)
    print()
    print("This script extracts verse text from PDF to find exact word positions")
    print("for cross-reference letters, then inserts them at the correct location.")
    print()
    
    # Test with John 7:28 which is missing 'f' and 'g'
    pdf_path = Path('raw/ESV Global Study Bible - Crossway Bibles-3.pdf')
    xml_file = Path('xml_esv/john_7.xml')
    
    if not pdf_path.exists():
        print(f"Error: PDF not found at {pdf_path}")
        return
    
    if not xml_file.exists():
        print(f"Error: XML not found at {xml_file}")
        return
    
    print("Testing with John 7:28 (should add 'f' and 'g')")
    print("="*80)
    
    # John 7 is on page 3934-3936 (0-indexed)
    process_verse(
        pdf_path=pdf_path,
        xml_file=xml_file,
        book_num='43',
        chapter='7',
        verse_num=28,
        pdf_page=3935,
        missing_letters=['f', 'g']
    )

if __name__ == '__main__':
    main()
