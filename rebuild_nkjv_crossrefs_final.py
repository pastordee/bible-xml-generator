#!/usr/bin/env python3
"""
Rebuild NKJV XML files with correct crossref placement based on raw NKJV text.
Inserts self-closing crossref tags at exact positions from NKJV format.
"""

import os
import re
import xml.etree.ElementTree as ET
from pathlib import Path

def parse_nkjv_raw_text(raw_file):
    """Parse NKJV raw text to find exact letter positions in each verse.
    Uses the Cross references section at the bottom to know which letters belong to which verses.
    
    Returns: {verse_num: [(letter, position_type, word_before/after)]}
    """
    with open(raw_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Split into verses section and crossref section
    crossref_match = re.search(r'\bCross references\b', content, re.IGNORECASE)
    if not crossref_match:
        print("Warning: No 'Cross references' section found")
        return {}
    
    verses_section = content[:crossref_match.start()]
    crossref_section = content[crossref_match.end():]
    
    # Parse crossref section to know which letters belong to which verses
    verse_letters_map = {}  # {verse_num: [letters]}
    current_verse = None
    
    for line in crossref_section.split('\n'):
        verse_match = re.match(r'^Verse\s+(\d+):', line)
        if verse_match:
            current_verse = int(verse_match.group(1))
            verse_letters_map[current_verse] = []
        elif current_verse and re.match(r'^\s+([a-z]+):', line):
            letter_match = re.match(r'^\s+([a-z]+):', line)
            if letter_match:
                letter = letter_match.group(1)
                verse_letters_map[current_verse].append(letter)
    
    # Now parse verses section to find WHERE those letters appear
    verse_positions = {}
    
    for line in verses_section.split('\n'):
        verse_match = re.match(r'^(\d+)\s+(.+)$', line.strip())
        if not verse_match:
            continue
        
        verse_num = int(verse_match.group(1))
        verse_text = verse_match.group(2)
        
        # Get the letters that should be in this verse
        if verse_num not in verse_letters_map:
            continue
        
        expected_letters = verse_letters_map[verse_num]
        if not expected_letters:
            continue
        
        # Find positions of these letters in the verse text
        positions = []
        words = verse_text.split()
        
        # Track which letters we've found
        found_letters = []
        
        # Identify real words vs potential letter markers
        last_real_word = None
        in_after_group = False
        
        for i, word in enumerate(words):
            word_clean = word.strip(',.;:!?\'"')
            
            # Check if this word is one of our expected letters
            if word_clean in expected_letters and word_clean not in found_letters:
                # This is a crossref letter for this verse
                found_letters.append(word_clean)
                letter = word_clean
                
                # Determine position
                if in_after_group and last_real_word:
                    positions.append((letter, 'after', last_real_word))
                elif ',' in word:
                    if last_real_word:
                        positions.append((letter, 'after', last_real_word))
                    in_after_group = True
                else:
                    # Goes before next real word
                    for j in range(i + 1, len(words)):
                        next_word_clean = words[j].strip(',.;:!?\'"')
                        if next_word_clean not in expected_letters:
                            positions.append((letter, 'before', next_word_clean))
                            break
                    in_after_group = False
            else:
                # This is a real word (not a crossref letter for this verse)
                last_real_word = word_clean
                if ',' in word:
                    in_after_group = True
                else:
                    in_after_group = False
        
        if positions:
            verse_positions[verse_num] = positions
    
    return verse_positions

def load_crossref_data(crossref_file):
    """Load crossref data to map letters to CIDs."""
    crossrefs = {}
    
    with open(crossref_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    current_verse = None
    current_letter = None
    current_id = None
    
    for line in lines:
        line = line.rstrip('\n')
        if not line.strip():
            continue
        
        parts = line.split('\t')
        if len(parts) < 2:
            continue
        
        line_type = parts[0]
        
        if line_type == 'V':
            # Save previous crossref
            if current_verse and current_letter and current_id:
                if current_verse not in crossrefs:
                    crossrefs[current_verse] = {}
                crossrefs[current_verse][current_letter] = current_id
            
            current_verse = parts[1].strip()
            current_letter = None
            current_id = None
        
        elif line_type == 'c':
            # Save previous letter's CID before starting new one
            if current_verse and current_letter and current_id:
                if current_verse not in crossrefs:
                    crossrefs[current_verse] = {}
                crossrefs[current_verse][current_letter] = current_id
            
            current_letter = parts[1].strip()
            current_id = None
        
        elif line_type == 'i':
            current_id = parts[1].strip()
    
    # Save last crossref
    if current_verse and current_letter and current_id:
        if current_verse not in crossrefs:
            crossrefs[current_verse] = {}
        crossrefs[current_verse][current_letter] = current_id
    
    return crossrefs

def rebuild_xml_with_crossrefs(xml_file, raw_file, crossref_file, output_file=None):
    """Rebuild XML with crossrefs at correct positions."""
    
    # Parse inputs
    verse_letters = parse_nkjv_raw_text(raw_file)
    crossref_cids = load_crossref_data(crossref_file)
    
    print(f"  Found letter positions for {len(verse_letters)} verses")
    print(f"  Found CID mappings for {len(crossref_cids)} verses")
    
    # Parse XML
    tree = ET.parse(xml_file)
    root = tree.getroot()
    
    # Remove ALL existing crossref elements
    for elem in root.iter():
        crossrefs_to_remove = [child for child in elem if child.tag == 'crossref']
        for crossref in crossrefs_to_remove:
            elem.remove(crossref)
    
    print(f"  Removed all existing crossrefs")
    
    # Process each verse element
    verses_processed = 0
    crossrefs_added = 0
    
    for verse_elem in root.findall('.//v'):
        verse_num = int(verse_elem.get('n'))
        
        # Get verse ID
        parent = None
        for chapter in root.findall('.//chapter'):
            if verse_elem in list(chapter.iter()):
                parent = chapter
                break
        
        if not parent:
            continue
        
        # Find verse ID from marker
        verse_id_pattern = f"v13001{verse_num:03d}"
        verse_id = None
        for elem in parent.findall('.//marker'):
            mid = elem.get('mid')
            if mid and verse_id_pattern in mid:
                verse_id = mid[1:]  # Remove 'v' prefix
                break
        
        if not verse_id:
            verse_id = f"13001{verse_num:03d}"
        
        # Check if this verse has letters in raw text
        if verse_num not in verse_letters:
            continue
        
        # Check if we have CID mappings for this verse
        if verse_id not in crossref_cids:
            continue
        
        positions = verse_letters[verse_num]
        cid_map = crossref_cids[verse_id]
        
        # Insert crossrefs at correct positions
        for letter, pos_type, target_word in positions:
            if letter not in cid_map:
                continue
            
            cid = cid_map[letter]
            
            # Find target word in verse and insert crossref
            if pos_type == 'after':
                insert_crossref_after_word(verse_elem, target_word, letter, cid)
                crossrefs_added += 1
            else:  # before
                insert_crossref_before_word(verse_elem, target_word, letter, cid)
                crossrefs_added += 1
        
        verses_processed += 1
    
    print(f"  Processed {verses_processed} verses")
    print(f"  Added {crossrefs_added} crossrefs")
    
    # Write output
    if output_file is None:
        output_file = xml_file
    
    # Format and save
    indent_xml(root)
    tree.write(output_file, encoding='utf-8', xml_declaration=True)
    
    return output_file

def insert_crossref_after_word(verse_elem, word, letter, cid):
    """Insert self-closing crossref element after specified word."""
    crossref = ET.Element('crossref')
    crossref.set('let', letter)
    crossref.set('cid', cid)
    
    # Search in main text
    if verse_elem.text and word in verse_elem.text:
        # Split at first occurrence
        idx = verse_elem.text.find(word)
        if idx != -1:
            end_idx = idx + len(word)
            verse_elem.text = verse_elem.text[:end_idx]
            # Insert crossref as first child
            verse_elem.insert(0, crossref)
            crossref.tail = verse_elem.text[end_idx:] if end_idx < len(verse_elem.text) else ''
            # Adjust text
            remaining = verse_elem.text[end_idx:]
            verse_elem.text = verse_elem.text[:end_idx]
            if len(verse_elem) > 1:
                crossref.tail = remaining + (verse_elem[1].text or '')
                verse_elem[1].text = ''
            else:
                crossref.tail = remaining
            return
    
    # Search in children tails
    for i, child in enumerate(verse_elem):
        if child.tail and word in child.tail:
            idx = child.tail.find(word)
            if idx != -1:
                end_idx = idx + len(word)
                child.tail = child.tail[:end_idx]
                verse_elem.insert(i + 1, crossref)
                crossref.tail = child.tail[end_idx:] if end_idx < len(child.tail) else ''
                child.tail = child.tail[:end_idx]
                return

def insert_crossref_before_word(verse_elem, word, letter, cid):
    """Insert self-closing crossref element before specified word."""
    crossref = ET.Element('crossref')
    crossref.set('let', letter)
    crossref.set('cid', cid)
    
    # Search in main text
    if verse_elem.text and word in verse_elem.text:
        idx = verse_elem.text.find(word)
        if idx != -1:
            verse_elem.text = verse_elem.text[:idx]
            verse_elem.insert(0, crossref)
            crossref.tail = verse_elem.text[idx:] if idx < len(verse_elem.text) else word
            # Adjust
            remaining = verse_elem.text[idx:]
            verse_elem.text = verse_elem.text[:idx]
            if len(verse_elem) > 1:
                crossref.tail = remaining + (verse_elem[1].text or '')
                verse_elem[1].text = ''
            else:
                crossref.tail = remaining
            return
    
    # Search in children tails
    for i, child in enumerate(verse_elem):
        if child.tail and word in child.tail:
            idx = child.tail.find(word)
            if idx != -1:
                child.tail = child.tail[:idx]
                verse_elem.insert(i + 1, crossref)
                crossref.tail = child.tail[idx:] if idx < len(child.tail) else word + (child.tail[idx+len(word):] if idx+len(word) < len(child.tail) else '')
                child.tail = child.tail[:idx]
                return

def indent_xml(elem, level=0):
    """Add pretty-printing indentation."""
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
    print("REBUILDING NKJV CROSSREFS FROM RAW TEXT POSITIONS")
    print("=" * 80)
    print(f"\nTesting {book} chapter {chapter}...")
    print(f"  Input XML: {xml_file}")
    print(f"  Raw text: {raw_file}")
    print(f"  Crossref data: {crossref_file}")
    print(f"  Output XML: {output_file}")
    print()
    
    rebuild_xml_with_crossrefs(xml_file, raw_file, crossref_file, output_file)
    
    print(f"\n✓ Successfully created {output_file}")
    print("\nPlease review the output file before proceeding with all chapters.")

if __name__ == '__main__':
    test_single_chapter()
