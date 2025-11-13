#!/usr/bin/env python3
"""
Fix crossref letter mismatches in ESV XML files by updating the 'let' attribute
to match the letters in the corresponding cross_refs text files.
"""

import xml.etree.ElementTree as ET
from pathlib import Path
import re

def get_text_crossref_map(text_file):
    """
    Extract mapping of crossref IDs to letters from text file.
    Returns: dict mapping cid (like 'c13001001.1') to letter (like 'a')
    """
    cid_to_letter = {}
    
    with open(text_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    current_letter = None
    for line in lines:
        line = line.strip()
        if line.startswith('c '):
            # Letter line: "c a"
            current_letter = line[2:].strip()
        elif line.startswith('i ') and current_letter:
            # ID line: "i c13001001.1"
            cid = line[2:].strip()
            cid_to_letter[cid] = current_letter
            current_letter = None  # Reset after assigning
    
    return cid_to_letter

def fix_xml_crossref_letters(xml_file, cid_to_letter):
    """
    Update the 'let' attribute of crossref elements in XML to match text file letters.
    """
    tree = ET.parse(xml_file)
    root = tree.getroot()
    
    changes_made = 0
    
    # Find all crossref elements
    for crossref in root.findall('.//crossref'):
        cid = crossref.get('cid')
        current_letter = crossref.get('let')
        
        if cid in cid_to_letter:
            correct_letter = cid_to_letter[cid]
            if current_letter != correct_letter:
                crossref.set('let', correct_letter)
                changes_made += 1
    
    if changes_made > 0:
        # Save the updated XML
        tree.write(xml_file, encoding='utf-8', xml_declaration=True)
    
    return changes_made

def get_book_chapter_from_xml_filename(xml_filename):
    """
    Convert XML filename to book/chapter format for finding text file.
    Example: "1_chronicles_1.xml" -> "1_chronicles", "1"
    """
    filename = xml_filename.stem  # Remove .xml extension
    
    # Split by last underscore to separate book from chapter
    parts = filename.rsplit('_', 1)
    if len(parts) == 2:
        book = parts[0]
        chapter = parts[1]
        return book, chapter
    
    return None, None

def main():
    xml_dir = Path('xml_esv')
    crossrefs_dir = Path('xml_esv/cross_refs')
    
    xml_files = sorted(xml_dir.glob('*.xml'))
    
    total_files = 0
    total_changes = 0
    files_with_changes = 0
    
    print("=" * 80)
    print("FIXING CROSSREF LETTER MISMATCHES")
    print("=" * 80)
    print()
    
    for xml_file in xml_files:
        book, chapter = get_book_chapter_from_xml_filename(xml_file)
        if not book or not chapter:
            continue
        
        # Find corresponding text file
        text_file = crossrefs_dir / book / f"{chapter}.txt"
        if not text_file.exists():
            continue
        
        # Get the correct letter mapping from text file
        cid_to_letter = get_text_crossref_map(text_file)
        
        # Fix the XML file
        changes = fix_xml_crossref_letters(xml_file, cid_to_letter)
        
        total_files += 1
        total_changes += changes
        if changes > 0:
            files_with_changes += 1
            if files_with_changes <= 20:
                print(f"✓ {xml_file.name}: Fixed {changes} crossref letters")
    
    print()
    print("=" * 80)
    print(f"SUMMARY")
    print(f"Files processed: {total_files}")
    print(f"Files with changes: {files_with_changes}")
    print(f"Total crossref letters fixed: {total_changes}")
    print("=" * 80)

if __name__ == '__main__':
    main()
