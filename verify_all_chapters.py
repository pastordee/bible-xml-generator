#!/usr/bin/env python3
"""
Verify all XML chapters sequentially from first to last.
"""

import xml.etree.ElementTree as ET
from pathlib import Path
import re
from collections import defaultdict

def get_xml_crossrefs(xml_file, verse_num):
    """Extract cross-references from XML verse."""
    try:
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
    except:
        return []

def get_studybible_crossrefs(book_name, chapter, verse):
    """Get cross-references from esv_crossrefs_complete.txt"""
    file_path = Path('esv_crossrefs_complete.txt')
    
    # Find the section for this book
    text = file_path.read_text()
    
    # Convert filename book format to Study Bible format
    book_mapping = {
        '1_chronicles': '1 Chronicles',
        '2_chronicles': '2 Chronicles',
        '1_samuel': '1 Samuel',
        '2_samuel': '2 Samuel',
        '1_kings': '1 Kings',
        '2_kings': '2 Kings',
        '1_corinthians': '1 Corinthians',
        '2_corinthians': '2 Corinthians',
        '1_thessalonians': '1 Thessalonians',
        '2_thessalonians': '2 Thessalonians',
        '1_timothy': '1 Timothy',
        '2_timothy': '2 Timothy',
        '1_peter': '1 Peter',
        '2_peter': '2 Peter',
        '1_john': '1 John',
        '2_john': '2 John',
        '3_john': '3 John',
        'song_of_solomon': 'Song of Solomon',
        'psalm': 'Psalm',
        'psalms': 'Psalm'
    }
    
    study_book = book_mapping.get(book_name.lower(), book_name.capitalize())
    
    # Find the book section
    book_pattern = rf'Cross-references for {study_book}'
    book_match = re.search(book_pattern, text, re.IGNORECASE)
    
    if not book_match:
        return []
    
    # Get text from this book section until next book
    start = book_match.end()
    next_book = re.search(r'Cross-references for [A-Z]', text[start:])
    if next_book:
        book_text = text[start:start + next_book.start()]
    else:
        book_text = text[start:]
    
    # Find references for this chapter:verse
    pattern = rf'{chapter}:{verse}\s+([a-z])\s+'
    matches = re.findall(pattern, book_text)
    
    return sorted(set(matches))

def verify_chapter(xml_file):
    """Verify all verses in a chapter."""
    # Parse filename: bookname_chapter.xml
    match = re.match(r'(.+?)_(\d+)\.xml$', xml_file.name)
    if not match:
        return None
    
    book_name = match.group(1)
    chapter_num = int(match.group(2))
    
    try:
        tree = ET.parse(xml_file)
        root = tree.getroot()
        
        # Find all verses
        verses = root.findall('.//v[@n]')
        
        total_refs_expected = 0
        total_refs_present = 0
        missing_count = 0
        mismatches = []
        
        for verse in verses:
            verse_num = int(verse.get('n'))
            
            xml_refs = get_xml_crossrefs(xml_file, verse_num)
            study_refs = get_studybible_crossrefs(book_name, chapter_num, verse_num)
            
            if not study_refs:
                continue
            
            total_refs_expected += len(study_refs)
            total_refs_present += len(xml_refs)
            
            missing = set(study_refs) - set(xml_refs)
            if missing:
                missing_count += len(missing)
                mismatches.append({
                    'verse': verse_num,
                    'expected': study_refs,
                    'present': xml_refs,
                    'missing': sorted(missing)
                })
        
        if total_refs_expected == 0:
            return None
        
        return {
            'book': book_name,
            'chapter': chapter_num,
            'expected': total_refs_expected,
            'present': total_refs_present,
            'missing': missing_count,
            'mismatches': mismatches,
            'completion': (total_refs_present / total_refs_expected * 100) if total_refs_expected > 0 else 0
        }
    except Exception as e:
        return None

def main():
    xml_dir = Path('xml_esv')
    
    if not xml_dir.exists():
        print("Error: xml_esv directory not found!")
        return
    
    # Get all XML files sorted
    xml_files = sorted(xml_dir.glob('*.xml'))
    
    print("="*80)
    print(f"VERIFYING ALL CHAPTERS IN xml_esv/ ({len(xml_files)} files)")
    print("="*80)
    print()
    
    results = []
    
    for i, xml_file in enumerate(xml_files, 1):
        result = verify_chapter(xml_file)
        
        if result:
            results.append(result)
            
            status = "✓" if result['completion'] == 100.0 else " "
            
            print(f"{i:4}. {status} {result['book']:20} {result['chapter']:3} - "
                  f"{result['completion']:5.1f}% ({result['present']:3}/{result['expected']:3}) "
                  f"{result['missing']:3} missing", end="")
            
            # Show first few missing if any
            if result['mismatches']:
                verses_with_missing = [m['verse'] for m in result['mismatches'][:3]]
                print(f" [v{', v'.join(map(str, verses_with_missing))}...]", end="")
            
            print()
    
    # Summary
    print()
    print("="*80)
    print("SUMMARY")
    print("="*80)
    
    total_expected = sum(r['expected'] for r in results)
    total_present = sum(r['present'] for r in results)
    total_missing = sum(r['missing'] for r in results)
    
    complete_100 = len([r for r in results if r['completion'] == 100.0])
    complete_90_99 = len([r for r in results if 90 <= r['completion'] < 100])
    complete_below_90 = len([r for r in results if r['completion'] < 90])
    
    print(f"Chapters verified: {len(results)}")
    print(f"Total cross-references expected: {total_expected}")
    print(f"Total cross-references present: {total_present}")
    print(f"Total missing: {total_missing}")
    print(f"Overall completion: {(total_present/total_expected*100):.2f}%")
    print()
    print(f"Chapters at 100%: {complete_100}")
    print(f"Chapters at 90-99%: {complete_90_99}")
    print(f"Chapters below 90%: {complete_below_90}")
    print("="*80)

if __name__ == '__main__':
    main()
