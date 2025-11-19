#!/usr/bin/env python3
"""
Rebuild NKJV XML files with correct crossref placement.
Matches ESV format with self-closing crossref tags placed at exact word positions.
"""

import os
import re
import xml.etree.ElementTree as ET
from pathlib import Path

def parse_raw_verse_text(raw_file):
    """Parse raw NKJV text to find crossref letter positions.
    
    Returns: {verse_num: [(letter, word_before_letter, position_in_verse)]}
    Example: {1: [('a', 'Adam', 1), ('b', 'Adam', 1), ('c', 'Adam', 1)]}
    """
    verse_letters = {}
    
    with open(raw_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find all verses (lines starting with verse number)
    verse_pattern = r'^(\d+)\s+(.+)$'
    
    for line in content.split('\n'):
        match = re.match(verse_pattern, line.strip())
        if not match:
            continue
        
        verse_num = int(match.group(1))
        verse_text = match.group(2)
        
        # Find all crossref letters in the verse
        # Pattern: letter followed by comma, space, or word
        letter_pattern = r'\b([a-z]{1,2})\b'
        
        # Split verse into words and track positions
        words = []
        current_pos = 0
        
        # Clean up verse text but preserve structure
        text_cleaned = verse_text
        
        # Find all single/double letters that are crossref markers
        letters_found = []
        word_list = text_cleaned.split()
        
        for i, word in enumerate(word_list):
            # Remove punctuation to check if it's a letter marker
            word_clean = word.strip(',.;:!?"\'')
            
            # Check if this word is a 1-2 letter crossref marker
            if len(word_clean) <= 2 and word_clean.isalpha() and word_clean.islower():
                # This might be a crossref letter
                # Store: letter, previous word, position
                if i > 0:
                    # Get previous word
                    prev_word = word_list[i-1].strip(',.;:!?"\'')
                    letters_found.append((word_clean, prev_word, i))
        
        if letters_found:
            verse_letters[verse_num] = letters_found
    
    return verse_letters

def load_crossref_data(crossref_file):
    """Load crossref data from xml_nkjv/cross_refs files.
    
    Returns: {verse_id: [{letter, cid, refs}]}
    """
    crossrefs = {}
    
    with open(crossref_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    current_verse = None
    current_letter = None
    current_id = None
    current_refs = []
    
    for line in lines:
        line = line.rstrip('\n')
        if not line.strip():
            continue
        
        parts = line.split('\t')
        if len(parts) < 2:
            continue
        
        line_type = parts[0]
        
        if line_type == 'V':
            # Save previous crossref if exists
            if current_verse and current_id:
                if current_verse not in crossrefs:
                    crossrefs[current_verse] = []
                crossrefs[current_verse].append({
                    'letter': current_letter,
                    'cid': current_id,
                    'refs': current_refs
                })
            
            current_verse = parts[1].strip()
            current_letter = None
            current_id = None
            current_refs = []
        
        elif line_type == 'c':
            current_letter = parts[1].strip()
        
        elif line_type == 'i':
            current_id = parts[1].strip()
        
        elif line_type == 'r':
            current_refs.append(parts[1].strip())
    
    # Save last crossref
    if current_verse and current_id:
        if current_verse not in crossrefs:
            crossrefs[current_verse] = []
        crossrefs[current_verse].append({
            'letter': current_letter,
            'cid': current_id,
            'refs': current_refs
        })
    
    return crossrefs

def rebuild_xml_with_crossrefs(xml_file, raw_file, crossref_file, output_file=None):
    """Rebuild XML file with correctly placed crossref tags."""
    
    # Parse inputs
    verse_letters = parse_raw_verse_text(raw_file)
    crossrefs = load_crossref_data(crossref_file)
    
    # Parse XML
    tree = ET.parse(xml_file)
    root = tree.getroot()
    
    # Remove all existing crossref elements
    for elem in root.iter():
        # Remove crossref children
        crossrefs_to_remove = []
        for child in elem:
            if child.tag == 'crossref':
                crossrefs_to_remove.append(child)
        
        for crossref in crossrefs_to_remove:
            elem.remove(crossref)
    
    # Process each verse element
    for verse_elem in root.findall('.//v'):
        verse_num = int(verse_elem.get('n'))
        
        # Get the verse ID from the marker before this verse
        marker = None
        parent = None
        
        # Find parent chapter element
        for chapter in root.findall('.//chapter'):
            if verse_elem in list(chapter.iter()):
                parent = chapter
                break
        
        if not parent:
            continue
        
        # Find the marker with mid for this verse
        verse_id_pattern = f"v13001{verse_num:03d}"
        for elem in parent.findall('.//marker'):
            mid = elem.get('mid')
            if mid and verse_id_pattern in mid:
                # Extract verse ID from mid (e.g., "v13001001" -> "13001001")
                verse_id = mid[1:]  # Remove 'v' prefix
                break
        else:
            # Fallback: construct verse ID
            verse_id = f"13001{verse_num:03d}"
        
        # Check if this verse has crossrefs
        if verse_id not in crossrefs:
            continue
        
        verse_crossrefs = crossrefs[verse_id]
        if not verse_crossrefs:
            continue
        
        # Get the letter positions from raw text
        if verse_num not in verse_letters:
            print(f"Warning: No letter positions found for verse {verse_num}")
            continue
        
        raw_letters = verse_letters[verse_num]
        
        # Match letters with crossref data
        # The raw text has letters in order, crossref data also in order
        letter_to_cid = {}
        for cr in verse_crossrefs:
            letter_to_cid[cr['letter']] = cr['cid']
        
        # Now insert crossrefs into the verse element
        # We need to parse the text content and insert at right positions
        
        # Get verse text content (includes text and tail from children)
        verse_text = get_element_text(verse_elem)
        
        # For each letter position, find where to insert in XML
        for letter, prev_word, position in raw_letters:
            if letter not in letter_to_cid:
                continue
            
            cid = letter_to_cid[letter]
            
            # Find the word in the verse text and insert crossref after it
            insert_crossref_after_word(verse_elem, prev_word, letter, cid)
    
    # Write output
    if output_file is None:
        output_file = xml_file
    
    # Format and save
    indent_xml(root)
    tree.write(output_file, encoding='utf-8', xml_declaration=True)
    
    return output_file

def get_element_text(elem):
    """Get all text content from element and its children."""
    text = elem.text or ''
    for child in elem:
        text += child.text or ''
        text += child.tail or ''
    text += elem.tail or ''
    return text

def insert_crossref_after_word(verse_elem, word, letter, cid):
    """Insert crossref element after specified word in verse."""
    
    # Create crossref element
    crossref = ET.Element('crossref')
    crossref.set('let', letter)
    crossref.set('cid', cid)
    
    # Search through verse text and children to find word
    if verse_elem.text and word in verse_elem.text:
        # Word is in the main text
        parts = verse_elem.text.split(word, 1)
        if len(parts) == 2:
            verse_elem.text = parts[0] + word
            # Insert crossref as first child
            verse_elem.insert(0, crossref)
            # Set tail of crossref to remaining text
            if len(verse_elem) > 1:
                # Move old first child's text to crossref tail
                crossref.tail = parts[1] + (verse_elem[1].text or '')
                verse_elem[1].text = ''
            else:
                crossref.tail = parts[1]
        return
    
    # Search in children tails
    for i, child in enumerate(verse_elem):
        if child.tail and word in child.tail:
            parts = child.tail.split(word, 1)
            if len(parts) == 2:
                child.tail = parts[0] + word
                # Insert crossref after this child
                verse_elem.insert(i + 1, crossref)
                crossref.tail = parts[1]
                return

def indent_xml(elem, level=0):
    """Add pretty-printing indentation to XML."""
    indent = "\n" + "\t" * level
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = indent + "\t"
        if not elem.tail or not elem.tail.strip():
            elem.tail = indent
        for child in elem:
            indent_xml(child, level + 1)
        if not child.tail or not child.tail.strip():
            child.tail = indent
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = indent

def test_single_chapter():
    """Test on 1 Chronicles 1."""
    book = '1_chronicles'
    chapter = 1
    
    xml_file = f'xml_nkjv/{book}_{chapter}.xml'
    raw_file = f'raw/nkjv_crossrefs_ot/{book}_{chapter}.txt'
    crossref_file = f'xml_nkjv/cross_refs/{book}/{chapter}.txt'
    output_file = f'xml_nkjv/{book}_{chapter}_rebuilt.xml'
    
    print("=" * 80)
    print("TESTING NKJV CROSSREF REBUILD")
    print("=" * 80)
    print(f"\nTesting {book} chapter {chapter}...")
    print(f"  Input XML: {xml_file}")
    print(f"  Raw text: {raw_file}")
    print(f"  Crossref data: {crossref_file}")
    print(f"  Output XML: {output_file}")
    
    rebuild_xml_with_crossrefs(xml_file, raw_file, crossref_file, output_file)
    
    print(f"✓ Successfully created {output_file}")
    print("\nPlease review the output file before proceeding with all chapters.")

if __name__ == '__main__':
    test_single_chapter()
