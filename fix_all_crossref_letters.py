#!/usr/bin/env python3
"""
Fix crossref letter attributes in ALL ESV XML files using cross_refs data.
Does NOT reposition crossrefs, only corrects the 'let' attribute to match
the letter defined in the cross_refs text files.
"""

import xml.etree.ElementTree as ET
from pathlib import Path

def get_cid_to_letter_mapping(text_file):
    """Extract mapping of cid to correct letter from cross_refs text file."""
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

def fix_crossref_letters(xml_file, cid_to_letter):
    """Update 'let' attribute of crossref elements to match cross_refs data."""
    tree = ET.parse(xml_file)
    root = tree.getroot()
    
    changes = 0
    
    for crossref in root.findall('.//crossref'):
        cid = crossref.get('cid', '')
        current_letter = crossref.get('let', '')
        
        if cid in cid_to_letter:
            correct_letter = cid_to_letter[cid]
            if current_letter != correct_letter:
                crossref.set('let', correct_letter)
                changes += 1
    
    if changes > 0:
        tree.write(xml_file, encoding='utf-8', xml_declaration=True)
    
    return changes

def get_book_chapter_from_filename(xml_filename):
    """Convert XML filename to book/chapter format."""
    filename = xml_filename.stem
    parts = filename.rsplit('_', 1)
    if len(parts) == 2:
        return parts[0], parts[1]
    return None, None

def main():
    xml_dir = Path('xml_esv')
    crossrefs_dir = Path('xml_esv/cross_refs')
    
    print("=" * 80)
    print("FIXING CROSSREF LETTERS IN ALL ESV FILES")
    print("=" * 80)
    print()
    
    xml_files = sorted(xml_dir.glob('*.xml'))
    
    total_files = 0
    total_changes = 0
    files_updated = 0
    missing_text_files = 0
    
    for xml_file in xml_files:
        book, chapter = get_book_chapter_from_filename(xml_file)
        if not book or not chapter:
            continue
        
        text_file = crossrefs_dir / book / f"{chapter}.txt"
        
        if not text_file.exists():
            missing_text_files += 1
            continue
        
        cid_to_letter = get_cid_to_letter_mapping(text_file)
        changes = fix_crossref_letters(xml_file, cid_to_letter)
        
        total_files += 1
        total_changes += changes
        if changes > 0:
            files_updated += 1
        
        if total_files % 100 == 0:
            print(f"  Progress: {total_files} files, {total_changes} letters fixed")
    
    print()
    print("=" * 80)
    print(f"SUMMARY")
    print(f"Files processed: {total_files}")
    print(f"Files updated: {files_updated}")
    print(f"Total letters fixed: {total_changes}")
    print(f"Files skipped (no cross_refs data): {missing_text_files}")
    print("=" * 80)

if __name__ == '__main__':
    main()
