#!/usr/bin/env python3
"""
Sync ESV cross-references between xml_esv/ XML files and xml_esv/cross_refs/ parsed data.

This script will:
1. Compare XML cross-references with parsed cross_refs data
2. Remove cross-references from XML that shouldn't be there
3. Add missing cross-references that should be there
"""

import xml.etree.ElementTree as ET
from pathlib import Path
import re
from collections import defaultdict

# Book name to number mapping
BOOK_NUMBERS = {
    'genesis': '01', 'exodus': '02', 'leviticus': '03', 'numbers': '04', 'deuteronomy': '05',
    'joshua': '06', 'judges': '07', 'ruth': '08', '1_samuel': '09', '2_samuel': '10',
    '1_kings': '11', '2_kings': '12', '1_chronicles': '13', '2_chronicles': '14',
    'ezra': '15', 'nehemiah': '16', 'esther': '17', 'job': '18', 'psalms': '19',
    'proverbs': '20', 'ecclesiastes': '21', 'song_of_solomon': '22', 'song': '22', 
    'isaiah': '23', 'jeremiah': '24', 'lamentations': '25', 'ezekiel': '26', 'daniel': '27',
    'hosea': '28', 'joel': '29', 'amos': '30', 'obadiah': '31', 'jonah': '32',
    'micah': '33', 'nahum': '34', 'habakkuk': '35', 'zephaniah': '36', 'haggai': '37',
    'zechariah': '38', 'malachi': '39', 'matthew': '40', 'mark': '41', 'luke': '42',
    'john': '43', 'acts': '44', 'romans': '45', '1_corinthians': '46', '2_corinthians': '47',
    'galatians': '48', 'ephesians': '49', 'philippians': '50', 'colossians': '51',
    '1_thessalonians': '52', '2_thessalonians': '53', '1_timothy': '54', '2_timothy': '55',
    'titus': '56', 'philemon': '57', 'hebrews': '58', 'james': '59', '1_peter': '60',
    '2_peter': '61', '1_john': '62', '2_john': '63', '3_john': '64', 'jude': '65',
    'revelation': '66'
}


def parse_crossref_file(file_path):
    """Parse a C/V/c/i/m format cross-reference file.
    
    Returns dict: {verse_num: {letter: reference_text}}
    """
    crossrefs = defaultdict(dict)
    
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    current_verse = None
    current_letter = None
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        if not line:
            i += 1
            continue
        
        # Split on whitespace (tab or space)
        parts = line.split(None, 1)  # Split on first whitespace
        if len(parts) != 2:
            i += 1
            continue
        
        marker, value = parts
        
        if marker == 'C':
            # Chapter marker
            pass
        elif marker == 'V':
            # Verse ID: extract verse number (last 3 digits)
            current_verse = int(value[-3:])
        elif marker == 'c':
            # Letter
            current_letter = value
        elif marker == 'i':
            # ID (skip)
            pass
        elif marker == 'm':
            # Reference text
            if current_verse and current_letter:
                crossrefs[current_verse][current_letter] = value
        
        i += 1
    
    return crossrefs


def get_xml_crossrefs(xml_file):
    """Extract cross-references from XML file.
    
    Returns dict: {verse_num: {letter: cid}}
    """
    if not xml_file.exists():
        return {}
    
    try:
        tree = ET.parse(xml_file)
        root = tree.getroot()
    except Exception as e:
        print(f"  ERROR parsing {xml_file}: {e}")
        return {}
    
    xml_crossrefs = defaultdict(dict)
    
    for crossref in root.findall('.//crossref'):
        cid = crossref.get('cid', '')
        letter = crossref.get('let', '')
        
        if cid.startswith('c') and '.' in cid:
            # Format: c{book}{chapter}{verse}.{sequence}
            # Example: c01001001.1
            verse_part = cid.split('.')[0]  # Get c01001001
            if len(verse_part) >= 9:
                verse_id = verse_part[1:9]  # Get 01001001
                try:
                    verse_num = int(verse_id[-3:])  # Last 3 digits = verse
                    xml_crossrefs[verse_num][letter] = cid
                except ValueError:
                    continue
    
    return xml_crossrefs


def compare_chapter_crossrefs(book_name, chapter_num, crossref_file, xml_file):
    """Compare cross-references between parsed file and XML."""
    
    # Parse the cross-reference file
    parsed_refs = parse_crossref_file(crossref_file)
    
    # Get XML cross-references
    xml_refs = get_xml_crossrefs(xml_file)
    
    # Calculate differences
    all_verses = sorted(set(list(parsed_refs.keys()) + list(xml_refs.keys())))
    
    missing = []  # In parsed but not in XML
    extra = []    # In XML but not in parsed
    matching = 0
    
    for verse_num in all_verses:
        parsed_letters = set(parsed_refs.get(verse_num, {}).keys())
        xml_letters = set(xml_refs.get(verse_num, {}).keys())
        
        missing_letters = parsed_letters - xml_letters
        extra_letters = xml_letters - parsed_letters
        matching_letters = parsed_letters & xml_letters
        
        matching += len(matching_letters)
        
        for letter in missing_letters:
            missing.append({
                'verse': verse_num,
                'letter': letter,
                'reference': parsed_refs[verse_num][letter]
            })
        
        for letter in extra_letters:
            extra.append({
                'verse': verse_num,
                'letter': letter,
                'cid': xml_refs[verse_num][letter]
            })
    
    return {
        'missing': missing,
        'extra': extra,
        'matching': matching,
        'parsed_total': sum(len(refs) for refs in parsed_refs.values()),
        'xml_total': sum(len(refs) for refs in xml_refs.values())
    }


def remove_extra_crossrefs(xml_file, extra_refs, dry_run=True):
    """Remove extra cross-references from XML file while preserving tail text."""
    
    if not extra_refs:
        return 0
    
    try:
        tree = ET.parse(xml_file)
        root = tree.getroot()
    except Exception as e:
        print(f"  ERROR parsing {xml_file}: {e}")
        return 0
    
    removed_count = 0
    
    # Build set of CIDs to remove
    cids_to_remove = {ref['cid'] for ref in extra_refs}
    
    # Find all elements that contain crossref children
    for parent in root.iter():
        crossrefs_to_remove = []
        for i, child in enumerate(list(parent)):
            if child.tag == 'crossref':
                cid = child.get('cid', '')
                if cid in cids_to_remove:
                    crossrefs_to_remove.append((i, child))
        
        # Remove crossrefs in reverse order to maintain indices
        for i, crossref in reversed(crossrefs_to_remove):
            # Get the tail text (text after the crossref element)
            tail_text = crossref.tail or ''
            
            # Find previous sibling or use parent's text
            if i > 0:
                # Add tail to previous sibling's tail
                prev_sibling = parent[i-1]
                prev_sibling.tail = (prev_sibling.tail or '') + tail_text
            else:
                # Add to parent's text
                parent.text = (parent.text or '') + tail_text
            
            # Remove the crossref element
            parent.remove(crossref)
            removed_count += 1
    
    if not dry_run and removed_count > 0:
        tree.write(xml_file, encoding='utf-8', xml_declaration=True)
    
    return removed_count


def add_missing_crossrefs(xml_file, book_name, chapter_num, missing_refs, dry_run=True):
    """Add missing cross-references to XML file."""
    
    if not missing_refs:
        return 0
    
    try:
        tree = ET.parse(xml_file)
        root = tree.getroot()
    except Exception as e:
        print(f"  ERROR parsing {xml_file}: {e}")
        return 0
    
    book_num = BOOK_NUMBERS.get(book_name.lower(), '01')
    added_count = 0
    
    for ref in missing_refs:
        verse_num = ref['verse']
        letter = ref['letter']
        reference_text = ref['reference']
        
        # Find the verse element by verse number attribute
        verse_elem = root.find(f".//v[@n='{verse_num}']")
        
        if verse_elem is None:
            print(f"    WARNING: Could not find verse {verse_num} in XML")
            continue
        
        verse_id = f"{book_num}{chapter_num:03d}{verse_num:03d}"
        
        # Generate CID
        existing_crossrefs = verse_elem.findall('.//crossref')
        sequence = len(existing_crossrefs) + 1
        cid = f"c{verse_id}.{sequence}"
        
        # Create new crossref element
        # Note: We need to find the right position in the verse text
        # For now, we'll add it at the end of the verse
        crossref = ET.Element('crossref', attrib={'let': letter, 'cid': cid})
        crossref.text = f" [{reference_text}]"
        crossref.tail = ""
        
        # Add to verse (simplified - should find proper position)
        verse_elem.append(crossref)
        added_count += 1
    
    if not dry_run and added_count > 0:
        tree.write(xml_file, encoding='utf-8', xml_declaration=True)
    
    return added_count


def process_book_chapter(book_name, chapter_num, dry_run=True):
    """Process a single book chapter."""
    
    crossref_file = Path(f'xml_esv/cross_refs/{book_name}/{chapter_num}.txt')
    xml_file = Path(f'xml_esv/{book_name}_{chapter_num}.xml')
    
    if not crossref_file.exists():
        print(f"  ⊘ {book_name} Ch {chapter_num:3d} - No crossref file found")
        return None
    
    if not xml_file.exists():
        print(f"  ⊘ {book_name} Ch {chapter_num:3d} - No XML file found")
        return None
    
    # Compare cross-references
    comparison = compare_chapter_crossrefs(book_name, chapter_num, crossref_file, xml_file)
    
    missing_count = len(comparison['missing'])
    extra_count = len(comparison['extra'])
    matching = comparison['matching']
    
    # Remove extra cross-references
    removed = 0
    if extra_count > 0:
        removed = remove_extra_crossrefs(xml_file, comparison['extra'], dry_run)
    
    # Add missing cross-references
    added = 0
    if missing_count > 0:
        added = add_missing_crossrefs(xml_file, book_name, chapter_num, comparison['missing'], dry_run)
    
    status = "✓" if (missing_count == 0 and extra_count == 0) else "⚠"
    action = " [DRY RUN]" if dry_run else ""
    
    if missing_count > 0 or extra_count > 0:
        print(f"  {status} {book_name.ljust(20)} Ch {chapter_num:3d} - "
              f"Match:{matching:3d} Missing:{missing_count:3d} Extra:{extra_count:3d} "
              f"Added:{added:3d} Removed:{removed:3d}{action}")
    
    return {
        'book': book_name,
        'chapter': chapter_num,
        'matching': matching,
        'missing': missing_count,
        'extra': extra_count,
        'added': added,
        'removed': removed
    }


def process_all_books(dry_run=True):
    """Process all books in xml_esv/cross_refs/."""
    
    crossref_dir = Path('xml_esv/cross_refs')
    
    if not crossref_dir.exists():
        print(f"ERROR: Directory not found: {crossref_dir}")
        return
    
    print("ESV Cross-Reference Sync")
    print("=" * 80)
    print(f"Mode: {'DRY RUN (no changes will be made)' if dry_run else 'LIVE (XML files will be modified)'}")
    print("=" * 80)
    
    stats = {
        'total_chapters': 0,
        'perfect_matches': 0,
        'with_differences': 0,
        'total_matching': 0,
        'total_missing': 0,
        'total_extra': 0,
        'total_added': 0,
        'total_removed': 0
    }
    
    results = []
    
    # Process each book
    for book_dir in sorted(crossref_dir.iterdir()):
        if not book_dir.is_dir():
            continue
        
        book_name = book_dir.name
        
        # Process each chapter
        for chapter_file in sorted(book_dir.glob('*.txt')):
            chapter_num = int(chapter_file.stem)
            
            result = process_book_chapter(book_name, chapter_num, dry_run)
            
            if result:
                results.append(result)
                stats['total_chapters'] += 1
                stats['total_matching'] += result['matching']
                stats['total_missing'] += result['missing']
                stats['total_extra'] += result['extra']
                stats['total_added'] += result['added']
                stats['total_removed'] += result['removed']
                
                if result['missing'] == 0 and result['extra'] == 0:
                    stats['perfect_matches'] += 1
                else:
                    stats['with_differences'] += 1
    
    # Print summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Total chapters processed: {stats['total_chapters']}")
    print(f"Perfect matches: {stats['perfect_matches']}")
    print(f"Chapters with differences: {stats['with_differences']}")
    print(f"\nCross-references:")
    print(f"  Matching: {stats['total_matching']}")
    print(f"  Missing (to add): {stats['total_missing']}")
    print(f"  Extra (to remove): {stats['total_extra']}")
    print(f"\nActions {'(DRY RUN)' if dry_run else '(COMPLETED)'}:")
    print(f"  Added: {stats['total_added']}")
    print(f"  Removed: {stats['total_removed']}")
    print("=" * 80)
    
    return results, stats


def main():
    import sys
    
    dry_run = True
    
    # Check for --live flag
    if len(sys.argv) > 1 and sys.argv[1] == '--live':
        dry_run = False
        print("\n⚠️  WARNING: Running in LIVE mode - XML files WILL be modified!")
        response = input("Continue? (yes/no): ")
        if response.lower() != 'yes':
            print("Aborted.")
            return
    
    results, stats = process_all_books(dry_run)
    
    if dry_run:
        print("\n💡 To apply changes, run: python3 sync_esv_crossrefs.py --live")


if __name__ == '__main__':
    main()
