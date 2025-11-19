#!/usr/bin/env python3
"""
Update NKJV XML files with cross-reference data from cross_refs directory.
Matches the ESV format.
"""

import xml.etree.ElementTree as ET
import re
from pathlib import Path

def load_crossref_data(crossref_file):
    """Load cross-reference data from the cross_refs text file."""
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
        
        # Split by tab
        parts = line.split('\t')
        if len(parts) < 2:
            continue
        
        tag = parts[0]
        value = parts[1] if len(parts) > 1 else ''
        
        if tag == 'C':
            # Chapter header
            continue
        elif tag == 'V':
            # New verse
            current_verse = value
            if current_verse not in crossrefs:
                crossrefs[current_verse] = []
        elif tag == 'c':
            # Save previous crossref if exists
            if current_letter and current_id:
                crossrefs[current_verse].append({
                    'letter': current_letter,
                    'id': current_id,
                    'refs': current_refs.copy()
                })
            
            # New crossref letter
            current_letter = value
            current_refs = []
        elif tag == 'i':
            # Crossref ID
            current_id = value
        elif tag == 'r':
            # Reference line
            current_refs.append(value)
        elif tag == 'm':
            # Message/note line
            current_refs.append(value)
    
    # Save last crossref
    if current_letter and current_id and current_verse:
        crossrefs[current_verse].append({
            'letter': current_letter,
            'id': current_id,
            'refs': current_refs.copy()
        })
    
    return crossrefs

def format_crossref_text(refs):
    """Format cross-reference text from refs list."""
    if not refs:
        return ''
    
    # Join all references
    text_parts = []
    for ref in refs:
        # ref format is like "01001027 Gen. 1:27"
        # We want just the display part (after the code)
        if ' ' in ref:
            parts = ref.split(' ', 1)
            text_parts.append(parts[1])
        else:
            text_parts.append(ref)
    
    return ' '.join(text_parts)

def update_xml_with_crossrefs(xml_file, crossref_file, output_file=None):
    """Update XML file with cross-reference data."""
    
    # Load cross-reference data
    crossrefs = load_crossref_data(crossref_file)
    
    # Parse XML
    tree = ET.parse(xml_file)
    root = tree.getroot()
    
    # Find all crossref elements
    for crossref_elem in root.findall('.//crossref'):
        # Get the cid attribute
        cid = crossref_elem.get('cid')
        if not cid:
            continue
        
        # Find matching crossref data
        # The cid format is like "c13001001.1" which matches our crossref IDs
        found = False
        for verse_id, verse_crossrefs in crossrefs.items():
            for cr_data in verse_crossrefs:
                if cr_data['id'] == cid:
                    # Update the crossref element
                    crossref_elem.set('let', cr_data['letter'])
                    crossref_elem.text = ' [' + format_crossref_text(cr_data['refs']) + ']'
                    found = True
                    break
            if found:
                break
    
    # Write output
    if output_file is None:
        output_file = xml_file
    
    # Write with proper formatting
    ET.indent(tree, space='\t', level=0)
    tree.write(output_file, encoding='utf-8', xml_declaration=True)
    
    return True

def test_single_chapter(book_name, chapter_num):
    """Test updating a single chapter."""
    xml_file = Path(f'xml_nkjv/{book_name}_{chapter_num}.xml')
    crossref_file = Path(f'xml_nkjv/cross_refs/{book_name}/{chapter_num}.txt')
    output_file = Path(f'xml_nkjv/{book_name}_{chapter_num}_updated.xml')
    
    if not xml_file.exists():
        print(f"✗ XML file not found: {xml_file}")
        return False
    
    if not crossref_file.exists():
        print(f"✗ Crossref file not found: {crossref_file}")
        return False
    
    print(f"Testing {book_name} chapter {chapter_num}...")
    print(f"  Input XML: {xml_file}")
    print(f"  Crossref data: {crossref_file}")
    print(f"  Output XML: {output_file}")
    
    try:
        update_xml_with_crossrefs(xml_file, crossref_file, output_file)
        print(f"✓ Successfully created {output_file}")
        print()
        print("Please review the output file before proceeding with all chapters.")
        return True
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    # Test on 1 Chronicles 1
    print("=" * 80)
    print("TESTING NKJV CROSSREF UPDATE")
    print("=" * 80)
    print()
    
    test_single_chapter('1_chronicles', 1)
