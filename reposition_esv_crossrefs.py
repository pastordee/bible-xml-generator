#!/usr/bin/env python3
"""
Reposition existing ESV cross-references to their correct inline positions
using the ESV Study Bible PDF as a positioning guide.
"""

import pdfplumber
import re
from pathlib import Path
import xml.etree.ElementTree as ET
from collections import defaultdict

def extract_verse_with_markers(pdf_path, page_num, verse_marker):
    """
    Extract verse text from PDF with cross-reference letter positions.
    Returns dict of {letter: word_before_letter}
    """
    with pdfplumber.open(pdf_path) as pdf:
        if page_num >= len(pdf.pages):
            return {}
        
        page = pdf.pages[page_num]
        text = page.extract_text()
        
        # Find the verse
        pattern = rf'{verse_marker}[†]?\s+(.+?)(?=\d+[†]?\s+|[A-Z][a-z]+\s+\d+:\d+|$)'
        match = re.search(pattern, text, re.DOTALL)
        
        if not match:
            return {}
        
        verse_text = match.group(1).strip()
        verse_text = re.sub(r'\n+', ' ', verse_text)
        
        # Find all letter markers and the words before them
        # Pattern: word + punctuation? + space? + letter + space/punctuation
        positions = {}
        pattern = r'(\w+[.,;:!?]?)\s*([a-z])(?=\s|[.,;:!?]|\)|]|$)'
        
        for match in re.finditer(pattern, verse_text):
            word = match.group(1).strip('.,;:!?()')
            letter = match.group(2)
            positions[letter] = word
        
        return positions

def reposition_crossrefs_in_verse(verse_elem, letter_positions):
    """
    Move crossref elements from end of verse to their correct inline positions.
    """
    if not letter_positions:
        return 0
    
    # Find all crossrefs in this verse
    crossrefs = []
    for crossref in verse_elem.findall('.//crossref'):
        letter = crossref.get('let', '')
        if letter in letter_positions:
            crossrefs.append((letter, crossref, letter_positions[letter]))
    
    if not crossrefs:
        return 0
    
    repositioned = 0
    
    # Remove all crossrefs first (they're at the end)
    for letter, crossref, word in crossrefs:
        # Store the tail text before removing
        tail = crossref.tail or ''
        parent = None
        for elem in verse_elem.iter():
            if crossref in list(elem):
                parent = elem
                break
        
        if parent is not None:
            parent.remove(crossref)
            # Add tail text to parent
            if parent.text:
                parent.text += tail
            else:
                parent.text = tail
    
    # Now insert them at correct positions
    for letter, crossref, target_word in crossrefs:
        inserted = insert_crossref_after_word(verse_elem, crossref, target_word)
        if inserted:
            repositioned += 1
            print(f"      Moved '{letter}' after '{target_word}'")
        else:
            # If we can't find the word, append at end as fallback
            verse_elem.append(crossref)
            print(f"      Warning: Couldn't find '{target_word}', kept at end")
    
    return repositioned

def insert_crossref_after_word(verse_elem, crossref, target_word):
    """
    Insert crossref element after a specific word in the verse.
    """
    word_pattern = rf'\b{re.escape(target_word)}\b'
    
    def search_in_element(elem, parent=None, idx=0):
        """Recursively search text and tail for the target word."""
        # Check element's text
        if elem.text:
            match = re.search(word_pattern, elem.text, re.IGNORECASE)
            if match:
                # Split text and insert crossref
                before = elem.text[:match.end()]
                after = elem.text[match.end():]
                
                # Create marker element to split text
                elem.text = before
                crossref.tail = after
                
                # Insert crossref as first child
                elem.insert(0, crossref)
                return True
        
        # Check children
        for i, child in enumerate(list(elem)):
            if search_in_element(child, elem, i):
                return True
            
            # Check child's tail
            if child.tail:
                match = re.search(word_pattern, child.tail, re.IGNORECASE)
                if match:
                    # Split tail and insert crossref after this child
                    before = child.tail[:match.end()]
                    after = child.tail[match.end():]
                    
                    child.tail = before
                    crossref.tail = after
                    
                    # Insert crossref after this child
                    elem.insert(i + 1, crossref)
                    return True
        
        return False
    
    return search_in_element(verse_elem)

def process_chapter(pdf_path, xml_file, book_num, chapter_num, start_page, verse_range):
    """
    Reposition all crossrefs in a chapter using PDF positions.
    """
    tree = ET.parse(xml_file)
    root = tree.getroot()
    
    total_repositioned = 0
    
    for verse_num in verse_range:
        # Find verse in XML
        verse_elem = root.find(f'.//v[@n="{verse_num}"]')
        if verse_elem is None:
            print(f"  Verse {verse_num}: Not found in XML")
            continue
        
        # Check if verse has crossrefs
        crossrefs = verse_elem.findall('.//crossref')
        if not crossrefs:
            continue
        
        # Extract positions from PDF
        verse_marker = f"{verse_num}"
        positions = extract_verse_with_markers(pdf_path, start_page, verse_marker)
        
        if not positions:
            print(f"  Verse {verse_num}: No positions found in PDF")
            continue
        
        print(f"  Verse {verse_num}: Found {len(positions)} positions - {list(positions.keys())}")
        
        # Reposition crossrefs
        moved = reposition_crossrefs_in_verse(verse_elem, positions)
        total_repositioned += moved
    
    if total_repositioned > 0:
        tree.write(xml_file, encoding='utf-8', xml_declaration=True)
        print(f"\n  ✓ Repositioned {total_repositioned} cross-references")
        return True
    
    return False

def main():
    print("=" * 80)
    print("ESV CROSS-REFERENCE REPOSITIONING")
    print("=" * 80)
    print()
    
    # Check for PDF
    pdf_path = Path('raw/ESV Global Study Bible - Crossway Bibles-3.pdf')
    if not pdf_path.exists():
        print(f"ERROR: PDF not found at {pdf_path}")
        print("This script requires the ESV Study Bible PDF for positioning.")
        return
    
    # Test with Acts 2
    xml_file = Path('xml_esv/acts_2.xml')
    if not xml_file.exists():
        print(f"ERROR: {xml_file} not found")
        return
    
    print("Processing Acts 2...")
    print("=" * 80)
    
    # Acts is in the NT, estimate page (you'll need to find exact page)
    # For now, let's process verses 1-10 as a test
    process_chapter(
        pdf_path=pdf_path,
        xml_file=xml_file,
        book_num='44',
        chapter_num='2',
        start_page=4100,  # You'll need to find the correct page
        verse_range=range(1, 48)  # Acts 2 has 47 verses
    )

if __name__ == '__main__':
    main()
