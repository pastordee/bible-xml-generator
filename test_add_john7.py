#!/usr/bin/env python3
"""
Test script: Add missing cross-references to John 7 only.
"""

import xml.etree.ElementTree as ET
from pathlib import Path
import json

def get_existing_crossrefs(verse_elem):
    """Get list of existing cross-reference letters in a verse."""
    existing = []
    for crossref in verse_elem.findall('.//crossref'):
        letter = crossref.get('let', '')
        if letter:
            existing.append(letter)
    return existing

def get_next_cid_sequence(verse_elem):
    """Determine the next CID sequence number for this verse."""
    max_seq = 0
    for crossref in verse_elem.findall('.//crossref'):
        cid = crossref.get('cid', '')
        if cid and '.' in cid:
            try:
                seq = int(cid.split('.')[-1])
                max_seq = max(max_seq, seq)
            except ValueError:
                pass
    return max_seq + 1

def add_crossref_to_verse(verse_elem, book_num, chapter, verse_num, letter, sequence):
    """Add a cross-reference element to the verse."""
    # Generate CID: c + book(2) + chapter(3) + verse(3) + .sequence
    cid = f"c{book_num}{int(chapter):03d}{int(verse_num):03d}.{sequence}"
    
    # Create crossref element
    crossref = ET.Element('crossref', attrib={'let': letter, 'cid': cid})
    crossref.tail = '\n\t\t\t\t'  # Add some formatting
    
    # Add to end of verse (before closing tag)
    verse_elem.append(crossref)
    
    return crossref

def main():
    print("="*80)
    print("TEST: Add missing cross-references to John 7")
    print("="*80)
    print()
    
    # Load missing refs for John 7
    json_file = Path('missing_crossrefs.json')
    with open(json_file, 'r', encoding='utf-8') as f:
        missing_refs = json.load(f)
    
    john_refs = missing_refs.get('JOHN', {}).get('7', {})
    
    if not john_refs:
        print("No missing references found for John 7")
        return
    
    print(f"Missing cross-references in John 7:")
    for verse, letters in sorted(john_refs.items(), key=lambda x: int(x[0])):
        print(f"  Verse {verse}: {', '.join(letters)}")
    
    print()
    response = input("Proceed with adding these to xml_esv/john_7.xml? (yes/no): ")
    
    if response.lower() != 'yes':
        print("Cancelled.")
        return
    
    # Process John 7
    xml_file = Path('xml_esv/john_7.xml')
    
    if not xml_file.exists():
        print(f"Error: {xml_file} not found!")
        return
    
    # Parse XML
    tree = ET.parse(xml_file)
    root = tree.getroot()
    
    book_num = '43'  # John
    chapter = '7'
    
    added_count = 0
    
    print()
    print("Processing...")
    print()
    
    # Process each verse that has missing refs
    for verse_num_str, letters_to_add in sorted(john_refs.items(), key=lambda x: int(x[0])):
        verse_num = int(verse_num_str)
        
        # Find the verse element
        verse_elem = root.find(f".//v[@n='{verse_num}']")
        
        if verse_elem is None:
            print(f"  Warning: Verse {verse_num} not found in XML")
            continue
        
        # Get existing cross-references
        existing_letters = get_existing_crossrefs(verse_elem)
        
        print(f"  Verse {verse_num}:")
        print(f"    Before: {', '.join(existing_letters) if existing_letters else '(none)'}")
        
        # Get next sequence number
        next_seq = get_next_cid_sequence(verse_elem)
        
        # Add each missing letter
        for letter in letters_to_add:
            if letter in existing_letters:
                print(f"    Skipping '{letter}' (already exists)")
                continue
            
            add_crossref_to_verse(verse_elem, book_num, chapter, verse_num, letter, next_seq)
            next_seq += 1
            added_count += 1
        
        # Show after
        new_letters = get_existing_crossrefs(verse_elem)
        print(f"    After:  {', '.join(new_letters)}")
    
    # Save the file
    print()
    print(f"Adding {added_count} cross-references to {xml_file}...")
    
    # Preserve the XML declaration and formatting
    tree.write(xml_file, encoding='utf-8', xml_declaration=True)
    
    print(f"✅ Done! Added {added_count} cross-references to John 7")
    print()
    print("You can verify the changes by running:")
    print("  python3 compare_with_study_bible.py")

if __name__ == '__main__':
    main()
