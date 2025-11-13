#!/usr/bin/env python3
"""
Automatically add missing cross-references to ESV XML files.
Strategy: Add missing crossrefs at the end of each verse (safest position).
Users can manually reposition them later if exact placement is critical.
"""

import xml.etree.ElementTree as ET
from pathlib import Path
import json
from collections import defaultdict
import re

# Book name to number mapping (for CID generation)
BOOK_NUMBERS = {
    '1 CHRONICLES': '13', '1 CORINTHIANS': '46', '1 JOHN': '62', '1 KINGS': '11',
    '1 PETER': '60', '1 SAMUEL': '09', '1 THESSALONIANS': '52', '1 TIMOTHY': '54',
    '2 CHRONICLES': '14', '2 CORINTHIANS': '47', '2 JOHN': '63', '2 KINGS': '12',
    '2 PETER': '61', '2 SAMUEL': '10', '2 THESSALONIANS': '53', '2 TIMOTHY': '55',
    '3 JOHN': '64', 'ACTS': '44', 'AMOS': '30', 'COLOSSIANS': '51', 
    'DANIEL': '27', 'DEUTERONOMY': '05', 'ECCLESIASTES': '21', 'EPHESIANS': '49',
    'ESTHER': '17', 'EXODUS': '02', 'EZEKIEL': '26', 'EZRA': '15',
    'GALATIANS': '48', 'GENESIS': '01', 'HABAKKUK': '35', 'HAGGAI': '37',
    'HEBREWS': '58', 'HOSEA': '28', 'ISAIAH': '23', 'JAMES': '59',
    'JEREMIAH': '24', 'JOB': '18', 'JOEL': '29', 'JOHN': '43',
    'JONAH': '32', 'JOSHUA': '06', 'JUDE': '65', 'JUDGES': '07',
    'LAMENTATIONS': '25', 'LEVITICUS': '03', 'LUKE': '42', 'MALACHI': '39',
    'MARK': '41', 'MATTHEW': '40', 'MICAH': '33', 'NAHUM': '34',
    'NEHEMIAH': '16', 'NUMBERS': '04', 'OBADIAH': '31', 'PHILEMON': '57',
    'PHILIPPIANS': '50', 'PROVERBS': '20', 'PSALM': '19', 'REVELATION': '66',
    'ROMANS': '45', 'RUTH': '08', 'SONG OF SOLOMON': '22', 'TITUS': '56',
    'ZECHARIAH': '38', 'ZEPHANIAH': '36'
}

def load_missing_refs(json_file):
    """Load the missing cross-references from JSON."""
    with open(json_file, 'r', encoding='utf-8') as f:
        return json.load(f)

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
    
    # Add to end of verse (before closing tag)
    verse_elem.append(crossref)
    
    return crossref

def process_chapter_file(xml_file, book_name, chapter, missing_verses, dry_run=True):
    """Process one chapter XML file and add missing cross-references."""
    
    try:
        tree = ET.parse(xml_file)
        root = tree.getroot()
        
        added_count = 0
        skipped_count = 0
        
        book_num = BOOK_NUMBERS.get(book_name.upper())
        if not book_num:
            print(f"  Warning: Unknown book number for {book_name}")
            return 0, 0
        
        # Process each verse that has missing refs
        for verse_num_str, letters_to_add in missing_verses.items():
            verse_num = int(verse_num_str)
            
            # Find the verse element
            verse_elem = root.find(f".//v[@n='{verse_num}']")
            
            if verse_elem is None:
                print(f"    Warning: Verse {verse_num} not found in XML")
                skipped_count += len(letters_to_add)
                continue
            
            # Get existing cross-references
            existing_letters = get_existing_crossrefs(verse_elem)
            
            # Get next sequence number
            next_seq = get_next_cid_sequence(verse_elem)
            
            # Add each missing letter
            for letter in letters_to_add:
                if letter in existing_letters:
                    print(f"    Note: Letter '{letter}' already exists in verse {verse_num}, skipping")
                    skipped_count += 1
                    continue
                
                if not dry_run:
                    add_crossref_to_verse(verse_elem, book_num, chapter, verse_num, letter, next_seq)
                
                next_seq += 1
                added_count += 1
        
        # Save the file if not dry run
        if not dry_run and added_count > 0:
            # Preserve the XML declaration
            tree.write(xml_file, encoding='utf-8', xml_declaration=True)
            print(f"  ✓ Saved {xml_file}")
        
        return added_count, skipped_count
        
    except Exception as e:
        print(f"  Error processing {xml_file}: {e}")
        return 0, 0

def main():
    print("="*80)
    print("ESV CROSS-REFERENCE AUTO-ADDITION TOOL")
    print("="*80)
    print()
    
    json_file = Path('missing_crossrefs.json')
    xml_dir = Path('xml_esv')
    
    if not json_file.exists():
        print(f"Error: {json_file} not found!")
        print("Please run generate_missing_crossrefs_csv.py first.")
        return
    
    if not xml_dir.exists():
        print(f"Error: {xml_dir} directory not found!")
        return
    
    # Load missing refs
    print("Loading missing cross-references...")
    missing_refs = load_missing_refs(json_file)
    
    total_books = len(missing_refs)
    total_missing = sum(
        sum(len(verses[v]) for v in verses)
        for book_data in missing_refs.values()
        for verses in book_data.values()
    )
    
    print(f"Found {total_missing} missing cross-references across {total_books} books")
    print()
    
    # Ask for confirmation
    response = input("Do you want to proceed? This will ADD cross-references to XML files.\n(Type 'yes' to continue, 'dry-run' to preview, or anything else to cancel): ")
    
    dry_run = response.lower() != 'yes'
    
    if response.lower() not in ['yes', 'dry-run']:
        print("Cancelled.")
        return
    
    if dry_run:
        print("\n🔍 DRY RUN MODE - No files will be modified\n")
    else:
        print("\n✏️  LIVE MODE - Files will be modified\n")
    
    print("="*80)
    
    total_added = 0
    total_skipped = 0
    
    # Process each book
    for book_name, chapters in sorted(missing_refs.items()):
        print(f"\n{book_name}")
        print("-"*80)
        
        for chapter_str, verses in sorted(chapters.items(), key=lambda x: int(x[0])):
            chapter = int(chapter_str)
            
            # Build XML filename
            xml_filename = f"{book_name.lower().replace(' ', '_')}_{chapter}.xml"
            xml_file = xml_dir / xml_filename
            
            if not xml_file.exists():
                print(f"  Warning: {xml_file} not found, skipping")
                continue
            
            print(f"  Chapter {chapter}...", end=' ')
            
            added, skipped = process_chapter_file(xml_file, book_name, chapter, verses, dry_run)
            
            total_added += added
            total_skipped += skipped
            
            if dry_run:
                print(f"Would add {added} refs" + (f" (skip {skipped})" if skipped > 0 else ""))
            else:
                print(f"Added {added} refs" + (f" (skipped {skipped})" if skipped > 0 else ""))
    
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    
    if dry_run:
        print(f"Would add:     {total_added} cross-references")
        print(f"Would skip:    {total_skipped} (already present)")
        print(f"\nTo actually add them, run again and type 'yes' when prompted.")
    else:
        print(f"Added:         {total_added} cross-references")
        print(f"Skipped:       {total_skipped} (already present)")
        print(f"\n✅ All missing cross-references have been added to ESV XML files!")
        print(f"\nNote: Cross-references were added at the end of each verse.")
        print(f"If exact positioning is critical, you can manually adjust them.")
    
    print("="*80)

if __name__ == '__main__':
    main()
