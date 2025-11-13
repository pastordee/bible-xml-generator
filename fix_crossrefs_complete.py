#!/usr/bin/env python3
"""
Fix ESV crossref positions and letters by:
1. Reading cross_refs text file for correct letter/cid mappings
2. Reading raw chapter text to find exact position of each letter marker
3. Repositioning crossref elements in XML to match raw text positions
"""

import re
from pathlib import Path
import xml.etree.ElementTree as ET

def get_crossref_data_from_text_file(text_file):
    """
    Extract crossref data from cross_refs text file.
    Returns: dict mapping cid to letter
    """
    cid_to_letter = {}
    
    with open(text_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    current_letter = None
    for line in lines:
        line = line.strip()
        if line.startswith('c '):
            current_letter = line[2:].strip()
        elif line.startswith('i ') and current_letter:
            cid = line[2:].strip()
            cid_to_letter[cid] = current_letter
            current_letter = None
    
    return cid_to_letter

def extract_verse_letter_positions(raw_text_file, verse_num, needed_letters):
    """
    Extract letter markers and their positions from raw chapter text for a specific verse.
    Only extracts positions for letters in needed_letters set.
    Returns: dict of {letter: word_before_letter}
    """
    with open(raw_text_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Special handling for verse 1 - it starts after chapter title "BOOK N [†]"
    if verse_num == "1":
        # Pattern: chapter title + [†] + verse 1 text + 2[†]
        verse_pattern = r'[A-Z\s\d]+\[†\](.*?)(?=2\[†\]|$)'
        match = re.search(verse_pattern, content, re.DOTALL)
    else:
        # Regular verses: N[†]text until next verse N+1[†]
        next_verse = str(int(verse_num) + 1)
        verse_pattern = rf'{verse_num}\[†\](.*?)(?={next_verse}\[†\]|$)'
        match = re.search(verse_pattern, content, re.DOTALL)
    
    if not match:
        return {}
    
    verse_text = match.group(1).strip()
    
    # Find all letter markers and the words before them
    # But ONLY include letters that are in needed_letters
    positions = {}
    
    # Look for pattern like "word a " or "word, a " etc.
    pattern = r'(\w+(?:[.,;:!?])?)\s+([a-z])\s'
    
    for match in re.finditer(pattern, verse_text):
        word = match.group(1).strip('.,;:!?()')
        letter = match.group(2)
        
        # Only include if this letter is needed
        if letter in needed_letters:
            positions[letter] = word
    
    return positions

def insert_crossref_after_word(verse_elem, crossref, target_word):
    """
    Insert crossref element after a specific word in the verse.
    Recursively searches through text and tail of all elements.
    """
    word_pattern = rf'\b{re.escape(target_word)}\b'
    
    def search_in_element(elem):
        """Recursively search text and tail for the target word."""
        # Check element's text
        if elem.text:
            match = re.search(word_pattern, elem.text, re.IGNORECASE)
            if match:
                # Split text at end of match
                before = elem.text[:match.end()]
                after = elem.text[match.end():]
                
                elem.text = before
                crossref.tail = after
                
                # Insert crossref as first child
                elem.insert(0, crossref)
                return True
        
        # Check children
        for i, child in enumerate(list(elem)):
            if search_in_element(child):
                return True
            
            # Check child's tail
            if child.tail:
                match = re.search(word_pattern, child.tail, re.IGNORECASE)
                if match:
                    # Split tail at end of match
                    before = child.tail[:match.end()]
                    after = child.tail[match.end():]
                    
                    child.tail = before
                    crossref.tail = after
                    
                    # Insert crossref after this child
                    elem.insert(i + 1, crossref)
                    return True
        
        return False
    
    return search_in_element(verse_elem)

def reposition_crossrefs_in_verse(verse_elem, letter_positions, cid_to_letter):
    """
    Reposition crossref elements in verse to match letter positions from raw text.
    Also fixes the 'let' attribute to match correct letter.
    """
    if not letter_positions:
        return 0
    
    # Find all crossrefs and match them to correct letters
    crossrefs_to_place = []
    
    for crossref in verse_elem.findall('.//crossref'):
        cid = crossref.get('cid', '')
        
        # Get correct letter from cid_to_letter mapping
        if cid in cid_to_letter:
            correct_letter = cid_to_letter[cid]
            
            # Update the letter attribute
            crossref.set('let', correct_letter)
            
            # Get position from raw text
            if correct_letter in letter_positions:
                target_word = letter_positions[correct_letter]
                crossrefs_to_place.append((correct_letter, crossref, target_word))
    
    if not crossrefs_to_place:
        return 0
    
    # Remove all crossrefs first
    for letter, crossref, word in crossrefs_to_place:
        tail = crossref.tail or ''
        parent = None
        
        # Find parent element
        for elem in verse_elem.iter():
            if crossref in list(elem):
                parent = elem
                break
        
        if parent is not None:
            parent.remove(crossref)
            # Preserve tail text
            if parent.text:
                parent.text += tail
            else:
                parent.text = tail
    
    # Insert crossrefs at correct positions
    repositioned = 0
    for letter, crossref, target_word in crossrefs_to_place:
        inserted = insert_crossref_after_word(verse_elem, crossref, target_word)
        if inserted:
            repositioned += 1
        else:
            # Fallback: append at end
            verse_elem.append(crossref)
            print(f"        ⚠ Warning: Couldn't find '{target_word}' for letter '{letter}', kept at end")
    
    return repositioned

def process_xml_file(xml_file, text_file, raw_file):
    """
    Process an XML file to fix all crossref positions and letters.
    """
    # Step 1: Get correct letter mappings
    cid_to_letter = get_crossref_data_from_text_file(text_file)
    
    # Step 2: Parse XML
    tree = ET.parse(xml_file)
    root = tree.getroot()
    
    total_repositioned = 0
    verses_processed = 0
    
    # Step 3: Process each verse
    for verse_elem in root.findall('.//v'):
        verse_num = verse_elem.get('n')
        if not verse_num:
            continue
        
        # Check if verse has crossrefs
        crossrefs = verse_elem.findall('.//crossref')
        if not crossrefs:
            continue
        
        # Get the letters we need from the cross_refs data
        needed_letters = set()
        for crossref in crossrefs:
            cid = crossref.get('cid', '')
            if cid in cid_to_letter:
                needed_letters.add(cid_to_letter[cid])
        
        if not needed_letters:
            continue
        
        # Get letter positions from raw text (only for needed letters)
        letter_positions = extract_verse_letter_positions(raw_file, verse_num, needed_letters)
        
        if not letter_positions:
            continue
        
        # Debug: print letter positions
        print(f"      Verse {verse_num}: Need {sorted(needed_letters)}, Found {letter_positions}")
        
        # Reposition crossrefs
        moved = reposition_crossrefs_in_verse(verse_elem, letter_positions, cid_to_letter)
        
        if moved > 0:
            verses_processed += 1
            total_repositioned += moved
    
    # Save if changes were made
    if total_repositioned > 0:
        tree.write(xml_file, encoding='utf-8', xml_declaration=True)
    
    return verses_processed, total_repositioned

def get_book_chapter_from_filename(xml_filename):
    """
    Convert XML filename to book/chapter format.
    Example: "acts_1.xml" -> "acts", "1"
    """
    filename = xml_filename.stem
    parts = filename.rsplit('_', 1)
    if len(parts) == 2:
        return parts[0], parts[1]
    return None, None

def main():
    xml_dir = Path('xml_esv')
    crossrefs_dir = Path('xml_esv/cross_refs')
    raw_texts_dir = Path('raw/chapter_texts')
    
    print("=" * 80)
    print("FIXING ESV CROSSREF POSITIONS AND LETTERS")
    print("=" * 80)
    print()
    
    # Test with Acts 1 first
    test_file = xml_dir / 'acts_1.xml'
    
    if test_file.exists():
        book, chapter = get_book_chapter_from_filename(test_file)
        text_file = crossrefs_dir / book / f"{chapter}.txt"
        raw_file = raw_texts_dir / f"{book}_{chapter}.txt"
        
        if text_file.exists() and raw_file.exists():
            print(f"Testing with {test_file.name}...")
            print(f"  Cross-refs: {text_file}")
            print(f"  Raw text: {raw_file}")
            print()
            
            verses, crossrefs = process_xml_file(test_file, text_file, raw_file)
            print(f"  ✓ Processed {verses} verses")
            print(f"  ✓ Repositioned {crossrefs} crossrefs")
            print()
            print("Review the output and run on all files if correct.")
        else:
            print(f"Missing required files for {test_file.name}")
    else:
        print(f"Test file not found: {test_file}")

if __name__ == '__main__':
    main()
