#!/usr/bin/env python3
"""
Compare a specific verse between XML and Study Bible.
"""

import xml.etree.ElementTree as ET
from pathlib import Path

def get_xml_crossrefs(xml_file, verse_num):
    """Extract cross-references from XML verse."""
    tree = ET.parse(xml_file)
    root = tree.getroot()
    verse = root.find(f".//v[@n='{verse_num}']")
    
    if verse is None:
        return []
    
    crossrefs = []
    for crossref in verse.findall('.//crossref'):
        letter = crossref.get('let')
        if letter:
            crossrefs.append(letter)
    
    return sorted(crossrefs)

def get_studybible_crossrefs(book, chapter, verse):
    """Get cross-references from esv_crossrefs_complete.txt"""
    file_path = Path('esv_crossrefs_complete.txt')
    text = file_path.read_text()
    
    # Search for the pattern "chapter:verse letter"
    import re
    pattern = rf'{chapter}:{verse}\s+([a-z])\s+'
    
    matches = re.findall(pattern, text)
    return sorted(set(matches))

def main():
    # Genesis 24:48
    book = "Genesis"
    chapter = 24
    verse = 48
    
    xml_file = Path(f'xml_esv/genesis_{chapter}.xml')
    
    print("="*80)
    print(f"VERIFICATION: {book} {chapter}:{verse}")
    print("="*80)
    print()
    
    # Get cross-references from both sources
    xml_refs = get_xml_crossrefs(xml_file, verse)
    study_refs = get_studybible_crossrefs(book, chapter, verse)
    
    print(f"Study Bible has: {', '.join(study_refs)}")
    print(f"XML file has:    {', '.join(xml_refs)}")
    print()
    
    missing = set(study_refs) - set(xml_refs)
    extra = set(xml_refs) - set(study_refs)
    
    if missing:
        print(f"✗ MISSING from XML: {', '.join(sorted(missing))}")
    
    if extra:
        print(f"⚠ EXTRA in XML (not in Study Bible): {', '.join(sorted(extra))}")
    
    if not missing and not extra:
        print("✓ PERFECT MATCH!")
    
    print()
    print("="*80)
    
    # Show the verse text from XML
    print("XML VERSE TEXT:")
    print("="*80)
    tree = ET.parse(xml_file)
    root = tree.getroot()
    verse_elem = root.find(f".//v[@n='{verse}']")
    
    if verse_elem is not None:
        # Reconstruct verse text
        text_parts = []
        if verse_elem.text:
            text_parts.append(verse_elem.text.strip())
        
        for child in verse_elem:
            if child.tag == 'crossref':
                text_parts.append(f"[{child.get('let')}]")
            if child.tail:
                text_parts.append(child.tail.strip())
        
        print(' '.join(text_parts))
    
    print("="*80)

if __name__ == '__main__':
    main()
