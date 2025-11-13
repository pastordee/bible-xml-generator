#!/usr/bin/env python3
"""
Remove extra cross-references from XML files that don't exist in the Study Bible.
Focuses on chapters showing >100% completion.
"""

import xml.etree.ElementTree as ET
from pathlib import Path
import re
from collections import defaultdict

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
        return set()
    
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
    
    return set(matches)

def remove_extra_crossrefs_from_chapter(xml_file, dry_run=True):
    """Remove cross-references from XML that don't exist in Study Bible."""
    
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
        
        removed_count = 0
        kept_count = 0
        changes = []
        
        for verse in verses:
            verse_num = int(verse.get('n'))
            
            # Get expected cross-references from Study Bible
            expected_refs = get_studybible_crossrefs(book_name, chapter_num, verse_num)
            
            # Find all crossref elements in this verse
            crossrefs = verse.findall('.//crossref')
            
            for crossref in crossrefs:
                letter = crossref.get('let')
                
                # If this letter is NOT in the Study Bible, remove it
                if letter and letter not in expected_refs:
                    if not dry_run:
                        # Remove the crossref element
                        parent = verse
                        # Find parent of crossref (might be nested)
                        for elem in verse.iter():
                            if crossref in list(elem):
                                parent = elem
                                break
                        parent.remove(crossref)
                    
                    removed_count += 1
                    changes.append({
                        'verse': verse_num,
                        'letter': letter,
                        'action': 'removed'
                    })
                else:
                    kept_count += 1
        
        if removed_count > 0:
            if not dry_run:
                # Save the modified XML
                tree.write(xml_file, encoding='utf-8', xml_declaration=True)
            
            return {
                'book': book_name,
                'chapter': chapter_num,
                'removed': removed_count,
                'kept': kept_count,
                'changes': changes
            }
        
        return None
        
    except Exception as e:
        print(f"Error processing {xml_file}: {e}")
        return None

def main():
    import sys
    
    dry_run = '--apply' not in sys.argv
    
    if dry_run:
        print("=" * 80)
        print("DRY RUN MODE - No files will be modified")
        print("Run with --apply to actually remove cross-references")
        print("=" * 80)
        print()
    
    xml_dir = Path('xml_esv')
    
    if not xml_dir.exists():
        print("Error: xml_esv directory not found!")
        return
    
    # Focus on over-populated chapters (>100% completion)
    # Based on verify_all_chapters.py output, focus on:
    # - Titus (302%, 234%)
    # - 1 John (195-261%)
    # - Song of Solomon (102-135%)
    # - 1 Corinthians (some chapters >100%)
    
    priority_books = [
        'titus',
        '1_john',
        'song_of_solomon',
        '1_corinthians',
        '1_peter',
        'zechariah',
        'zephaniah'
    ]
    
    xml_files = sorted(xml_dir.glob('*.xml'))
    
    total_removed = 0
    chapters_modified = 0
    
    for xml_file in xml_files:
        # Check if this is a priority book
        is_priority = any(xml_file.name.startswith(book) for book in priority_books)
        
        if not is_priority:
            continue
        
        result = remove_extra_crossrefs_from_chapter(xml_file, dry_run=dry_run)
        
        if result:
            chapters_modified += 1
            total_removed += result['removed']
            
            print(f"{result['book']} {result['chapter']} - Removed: {result['removed']}, Kept: {result['kept']}")
            
            # Show first few changes
            for change in result['changes'][:3]:
                print(f"  Verse {change['verse']}: removed '{change['letter']}'")
            if len(result['changes']) > 3:
                print(f"  ... and {len(result['changes']) - 3} more")
            print()
    
    print("=" * 80)
    print(f"SUMMARY")
    print("=" * 80)
    print(f"Chapters modified: {chapters_modified}")
    print(f"Total cross-references removed: {total_removed}")
    
    if dry_run:
        print()
        print("This was a DRY RUN - no files were modified")
        print("Run with --apply to actually remove the cross-references")
    else:
        print()
        print("Cross-references have been removed from XML files")

if __name__ == '__main__':
    main()
