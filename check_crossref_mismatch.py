#!/usr/bin/env python3
"""
Check for mismatches between XML crossref letters and cross_refs text file letters.
"""

import xml.etree.ElementTree as ET
from pathlib import Path
import re

def get_xml_crossref_letters(xml_file):
    """Extract all crossref letters from XML file in order."""
    try:
        tree = ET.parse(xml_file)
        root = tree.getroot()
        
        letters = []
        for crossref in root.findall('.//crossref'):
            letter = crossref.get('let')
            if letter:
                letters.append(letter)
        
        return letters
    except Exception as e:
        return None

def get_text_crossref_letters(text_file):
    """Extract all crossref letters from cross_refs text file in order."""
    try:
        with open(text_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        letters = []
        for line in lines:
            if line.startswith('c '):
                letter = line[2:].strip()
                letters.append(letter)
        
        return letters
    except Exception as e:
        return None

def main():
    xml_dir = Path('xml_esv')
    crossref_dir = Path('xml_esv/cross_refs')
    
    print("=" * 80)
    print("CHECKING CROSSREF LETTER MISMATCHES")
    print("=" * 80)
    print()
    
    mismatches = []
    
    # Check all XML files
    for xml_file in sorted(xml_dir.glob('*.xml')):
        # Skip esv.xml
        if xml_file.stem in ['esv', 'esv_old']:
            continue
        
        # Get corresponding cross_refs file
        book_name = xml_file.stem
        chapter_num = book_name.split('_')[-1]
        book_base = '_'.join(book_name.split('_')[:-1])
        
        text_file = crossref_dir / book_base / f"{chapter_num}.txt"
        
        if not text_file.exists():
            continue
        
        xml_letters = get_xml_crossref_letters(xml_file)
        text_letters = get_text_crossref_letters(text_file)
        
        if xml_letters is None or text_letters is None:
            continue
        
        # Compare
        if xml_letters != text_letters:
            mismatches.append({
                'xml_file': xml_file.name,
                'text_file': str(text_file.relative_to(Path('xml_esv'))),
                'xml_letters': xml_letters,
                'text_letters': text_letters,
                'xml_first': xml_letters[0] if xml_letters else None,
                'text_first': text_letters[0] if text_letters else None
            })
    
    # Report mismatches
    if mismatches:
        print(f"Found {len(mismatches)} files with mismatches:\n")
        
        for item in mismatches[:20]:  # Show first 20
            print(f"XML: {item['xml_file']}")
            print(f"  XML letters: {', '.join(item['xml_letters'][:10])}...")
            print(f"  Text letters: {', '.join(item['text_letters'][:10])}...")
            print(f"  First letter: XML={item['xml_first']}, Text={item['text_first']}")
            print()
        
        if len(mismatches) > 20:
            print(f"... and {len(mismatches) - 20} more files")
    else:
        print("✓ No mismatches found!")
    
    print()
    print("=" * 80)
    print(f"Total files checked: {len(list(xml_dir.glob('*.xml'))) - 1}")
    print(f"Files with mismatches: {len(mismatches)}")
    print("=" * 80)

if __name__ == '__main__':
    main()
