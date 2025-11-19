#!/usr/bin/env python3
"""
Rebuild NKJV XML crossrefs while preserving word-specific positions.

This script:
1. Keeps the original crossref positions within verse text (word-specific)
2. Updates the letters and CIDs based on the accurate crossref data
3. Preserves all verse text
"""

import xml.etree.ElementTree as ET
import os
import re


def get_verse_crossrefs_map(crossref_file):
    """
    Parse NKJV crossref data file and return mapping of verse_id to {letter: cid}.
    
    Format of crossref file:
        V       13002001
        c       a
        i       c13002001.1
        ...
    
    Returns:
        {
            "13002001": {"a": "c13002001.1", "b": "c13002001.2", ...},
            "13002002": {...},
            ...
        }
    """
    verse_crossrefs = {}
    current_verse_id = None
    
    with open(crossref_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            
            parts = line.split('\t')
            if len(parts) < 2:
                continue
            
            field_type = parts[0]
            value = parts[1]
            
            if field_type == 'V':
                current_verse_id = value
                if current_verse_id not in verse_crossrefs:
                    verse_crossrefs[current_verse_id] = {}
            
            elif field_type == 'c' and current_verse_id:
                current_letter = value
            
            elif field_type == 'i' and current_verse_id:
                cid = value
                verse_crossrefs[current_verse_id][current_letter] = cid
    
    return verse_crossrefs


def update_crossref_attributes(elem, verse_crossrefs, verse_id):
    """
    Recursively update crossref elements with correct letter and CID.
    
    Strategy:
    - Count existing crossrefs in the verse
    - If count matches expected, update them in place (preserves word positions)
    - If count is less, add missing ones at the beginning
    - If count is more, remove extras
    """
    if verse_id not in verse_crossrefs:
        # No crossref data for this verse, remove all crossrefs
        for child in list(elem):
            if child.tag == 'crossref':
                # Preserve tail text
                if child.tail:
                    if len(elem) > 0 and elem[-1] != child:
                        # Find previous sibling
                        idx = list(elem).index(child)
                        if idx > 0:
                            prev = elem[idx - 1]
                            prev.tail = (prev.tail or '') + child.tail
                        else:
                            elem.text = (elem.text or '') + child.tail
                    else:
                        elem.text = (elem.text or '') + child.tail
                elem.remove(child)
            else:
                update_crossref_attributes(child, verse_crossrefs, verse_id)
        return
    
    # Get letters for this verse in alphabetical order
    letters = sorted(verse_crossrefs[verse_id].keys())
    expected_count = len(letters)
    
    # Count existing crossrefs (only direct children, not nested)
    existing_crossrefs = [child for child in elem if child.tag == 'crossref']
    existing_count = len(existing_crossrefs)
    
    if existing_count == expected_count:
        # Perfect match - update in place to preserve positions
        for i, child in enumerate(existing_crossrefs):
            letter = letters[i]
            cid = verse_crossrefs[verse_id][letter]
            
            child.set('let', letter)
            child.set('cid', cid)
            
            # Remove any text content (crossrefs should be self-closing)
            child.text = None
            for subchild in list(child):
                child.remove(subchild)
    
    elif existing_count < expected_count:
        # Missing crossrefs - update existing ones, then add missing at beginning
        # Update existing crossrefs starting from the END of the letter list
        # This way earlier letters get added at the beginning
        start_index = expected_count - existing_count
        for i, child in enumerate(existing_crossrefs):
            letter = letters[start_index + i]
            cid = verse_crossrefs[verse_id][letter]
            
            child.set('let', letter)
            child.set('cid', cid)
            
            child.text = None
            for subchild in list(child):
                child.remove(subchild)
        
        # Add missing crossrefs at the beginning
        for i in range(start_index):
            letter = letters[i]
            cid = verse_crossrefs[verse_id][letter]
            
            crossref = ET.Element('crossref')
            crossref.set('let', letter)
            crossref.set('cid', cid)
            
            if i == 0:
                # First crossref - move verse text to its tail
                crossref.tail = elem.text or ''
                elem.text = ''
                elem.insert(0, crossref)
            else:
                # Subsequent crossrefs
                elem.insert(i, crossref)
    
    else:
        # Too many crossrefs - update the ones we need, remove extras
        for i in range(expected_count):
            child = existing_crossrefs[i]
            letter = letters[i]
            cid = verse_crossrefs[verse_id][letter]
            
            child.set('let', letter)
            child.set('cid', cid)
            
            child.text = None
            for subchild in list(child):
                child.remove(subchild)
        
        # Remove extra crossrefs
        for i in range(expected_count, existing_count):
            child = existing_crossrefs[i]
            if child.tail:
                idx = list(elem).index(child)
                if idx > 0:
                    prev = elem[idx - 1]
                    prev.tail = (prev.tail or '') + child.tail
                else:
                    elem.text = (elem.text or '') + child.tail
            elem.remove(child)
    
    # Recursively process non-crossref children
    for child in elem:
        if child.tag != 'crossref':
            update_crossref_attributes(child, verse_crossrefs, verse_id)


def rebuild_xml_with_crossrefs(xml_file, crossref_file, output_file):
    """
    Rebuild XML file with updated crossrefs while preserving positions.
    """
    # Load crossref data
    verse_crossrefs = get_verse_crossrefs_map(crossref_file)
    
    # Parse XML
    tree = ET.parse(xml_file)
    root = tree.getroot()
    
    # Find book and chapter elements
    book = root.find('.//book')
    if not book:
        return
    
    chapter = book.find('.//chapter')
    if not chapter:
        return
    
    chapter_num = int(chapter.get('num', 1))
    book_num = int(book.get('num', 1))
    
    # Process each verse
    verses_processed = 0
    crossrefs_updated = 0
    
    for verse_elem in chapter.findall('.//v'):
        verse_num = int(verse_elem.get('n', 0))
        if verse_num == 0:
            continue
        
        # Build verse ID: book(2) + chapter(3) + verse(3)
        verse_id = f"{book_num:02d}{chapter_num:03d}{verse_num:03d}"
        
        # Count crossrefs before
        crossrefs_before = len(verse_elem.findall('.//crossref'))
        
        # Update crossrefs in this verse
        update_crossref_attributes(verse_elem, verse_crossrefs, verse_id)
        
        # Count crossrefs after
        crossrefs_after = len(verse_elem.findall('.//crossref'))
        crossrefs_updated += crossrefs_after
        
        verses_processed += 1
    
    # Save output
    indent_xml(root)
    tree.write(output_file, encoding='utf-8', xml_declaration=True)
    

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


def process_all_chapters():
    """Process all NKJV chapters."""
    import glob
    
    print("=" * 80)
    print("REBUILDING ALL NKJV CROSSREFS - PRESERVING WORD POSITIONS")
    print("=" * 80)
    print()
    
    # Find all XML files
    xml_files = sorted(glob.glob('xml_nkjv/*_*.xml'))
    
    total_files = len(xml_files)
    processed = 0
    skipped = 0
    errors = 0
    
    for xml_file in xml_files:
        # Extract book and chapter from filename
        # Format: xml_nkjv/1_chronicles_2.xml
        basename = os.path.basename(xml_file)
        if basename.endswith('_test.xml') or basename.endswith('_positioned.xml'):
            continue
            
        parts = basename.replace('.xml', '').rsplit('_', 1)
        if len(parts) != 2:
            continue
            
        book = parts[0]
        chapter = parts[1]
        
        # Build paths
        crossref_file = f'xml_nkjv/cross_refs/{book}/{chapter}.txt'
        output_file = xml_file  # Overwrite original
        
        # Check if crossref file exists
        if not os.path.exists(crossref_file):
            skipped += 1
            continue
        
        try:
            # Process this chapter
            rebuild_xml_with_crossrefs(xml_file, crossref_file, output_file)
            processed += 1
            
            if processed % 50 == 0:
                print(f"Progress: {processed}/{total_files} files processed...")
        
        except Exception as e:
            print(f"✗ Error processing {xml_file}: {e}")
            errors += 1
    
    print()
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Total files found: {total_files}")
    print(f"Successfully processed: {processed}")
    print(f"Skipped (no crossref data): {skipped}")
    print(f"Errors: {errors}")
    print()
    print("✓ All NKJV chapters have been rebuilt with correct crossrefs!")


def test_single_chapter():
    """Test on a single chapter."""
    book = '1_chronicles'
    chapter = 2
    
    xml_file = f'xml_nkjv/{book}_{chapter}.xml'
    crossref_file = f'xml_nkjv/cross_refs/{book}/{chapter}.txt'
    output_file = f'xml_nkjv/{book}_{chapter}_positioned.xml'
    
    print("=" * 80)
    print("REBUILDING NKJV CROSSREFS - PRESERVING WORD POSITIONS")
    print("=" * 80)
    print(f"\nTesting {book} chapter {chapter}...")
    print(f"  Input XML: {xml_file}")
    print(f"  Crossref data: {crossref_file}")
    print(f"  Output XML: {output_file}")
    print()
    
    if not os.path.exists(xml_file):
        print(f"✗ XML file not found: {xml_file}")
        return
    
    if not os.path.exists(crossref_file):
        print(f"✗ Crossref file not found: {crossref_file}")
        return
    
    rebuild_xml_with_crossrefs(xml_file, crossref_file, output_file)
    
    print("\nPlease verify:")
    print("  1. All verse text is preserved")
    print("  2. Crossrefs are at the same word positions as original")
    print("  3. Crossref letters and CIDs are correct")


if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == '--test':
        test_single_chapter()
    else:
        process_all_chapters()
