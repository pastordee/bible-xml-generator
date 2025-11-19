#!/usr/bin/env python3
"""
Rebuild NKJV XML crossrefs by:
1. Preserving all verse text
2. Removing only crossref tags (keeping their tail text)
3. Inserting new self-closing crossrefs based on crossref data mapping
"""

import os
import re
import xml.etree.ElementTree as ET
from pathlib import Path

def get_verse_crossrefs_map(crossref_file):
    """Load crossref data to map verse IDs to their letters and CIDs.
    Returns: {verse_id: {letter: cid}}
    """
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
            # Save previous letter before starting new one
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

def remove_crossrefs_preserve_text(elem):
    """Remove crossref elements but preserve their tail text."""
    for child in list(elem):
        # Recursively process children first
        remove_crossrefs_preserve_text(child)
    
    # Remove crossref children, preserving tail text
    crossrefs_to_remove = []
    for i, child in enumerate(elem):
        if child.tag == 'crossref':
            # Preserve the tail text by appending it to previous sibling or parent
            tail = child.tail or ''
            
            if i > 0:
                # Append to previous sibling's tail
                prev = elem[i-1]
                prev.tail = (prev.tail or '') + tail
            else:
                # Append to parent's text
                elem.text = (elem.text or '') + tail
            
            crossrefs_to_remove.append(child)
    
    for crossref in crossrefs_to_remove:
        elem.remove(crossref)

def rebuild_xml_with_crossrefs(xml_file, crossref_file, output_file=None):
    """Rebuild XML with correct crossrefs."""
    
    # Load crossref mappings
    crossref_map = get_verse_crossrefs_map(crossref_file)
    
    print(f"  Found crossref mappings for {len(crossref_map)} verses")
    
    # Parse XML
    tree = ET.parse(xml_file)
    root = tree.getroot()
    
    # Remove all existing crossrefs (preserving text)
    remove_crossrefs_preserve_text(root)
    
    print(f"  Removed all existing crossrefs (text preserved)")
    
    # Now insert new crossrefs based on mapping
    # For now, just insert them as self-closing tags in logical positions
    verses_processed = 0
    crossrefs_added = 0
    
    for verse_elem in root.findall('.//v'):
        verse_num = int(verse_elem.get('n'))
        
        # Find verse ID from marker
        parent = None
        for chapter in root.findall('.//chapter'):
            if verse_elem in list(chapter.iter()):
                parent = chapter
                break
        
        if not parent:
            continue
        
        # Get chapter number for constructing verse ID pattern
        chapter_num = int(parent.get('num', 1))
        
        # Get verse ID from marker - pattern is v + book(2) + chapter(3) + verse(3)
        verse_id_pattern = f"v13{chapter_num:03d}{verse_num:03d}"
        verse_id = None
        for elem in parent.findall('.//marker'):
            mid = elem.get('mid')
            if mid and verse_id_pattern in mid:
                verse_id = mid[1:]  # Remove 'v' prefix
                break
        
        if not verse_id:
            # Fallback: construct verse ID
            verse_id = f"13{chapter_num:03d}{verse_num:03d}"
        
        # Check if we have crossrefs for this verse
        if verse_id not in crossref_map:
            continue
        
        letter_cids = crossref_map[verse_id]
        
        # Insert crossrefs at the BEGINNING of the verse (right after verse opening tag)
        # This makes them clearly associated with the verse
        # Create them in alphabetical order
        for i, letter in enumerate(sorted(letter_cids.keys())):
            cid = letter_cids[letter]
            crossref = ET.Element('crossref')
            crossref.set('let', letter)
            crossref.set('cid', cid)
            
            # Insert at beginning - push existing content to tail
            if i == 0:
                # First crossref: set tail to original verse text
                crossref.tail = verse_elem.text or ''
                verse_elem.text = ''
                verse_elem.insert(0, crossref)
            else:
                # Subsequent crossrefs: insert after previous
                verse_elem.insert(i, crossref)
            
            crossrefs_added += 1
        
        verses_processed += 1
    
    print(f"  Processed {verses_processed} verses")
    print(f"  Added {crossrefs_added} crossrefs")
    
    # Write output
    if output_file is None:
        output_file = xml_file
    
    indent_xml(root)
    tree.write(output_file, encoding='utf-8', xml_declaration=True)
    
    return output_file

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
    """Test on 1 Chronicles 2."""
    book = '1_chronicles'
    chapter = 2
    
    xml_file = f'xml_nkjv/{book}_{chapter}.xml'
    crossref_file = f'xml_nkjv/cross_refs/{book}/{chapter}.txt'
    output_file = f'xml_nkjv/{book}_{chapter}_test.xml'
    
    print("=" * 80)
    print("REBUILDING NKJV CROSSREFS - TEXT PRESERVATION TEST")
    print("=" * 80)
    print(f"\nTesting {book} chapter {chapter}...")
    print(f"  Input XML: {xml_file}")
    print(f"  Crossref data: {crossref_file}")
    print(f"  Output XML: {output_file}")
    print()
    
    rebuild_xml_with_crossrefs(xml_file, crossref_file, output_file)
    
    print(f"\n✓ Successfully created {output_file}")
    print("\nPlease verify:")
    print("  1. All verse text is preserved")
    print("  2. Crossrefs are present (at end of verses for now)")

if __name__ == '__main__':
    test_single_chapter()
