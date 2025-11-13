#!/usr/bin/env python3
"""
Remove duplicate cross-references from XML files.
Keeps only one instance of each letter per verse.
"""

import xml.etree.ElementTree as ET
from pathlib import Path
import sys

def deduplicate_verse_crossrefs(verse_elem):
    """Remove duplicate crossref elements from a verse, keeping only the first occurrence."""
    seen_letters = set()
    to_remove = []
    
    # Find all crossref elements in this verse
    for crossref in verse_elem.findall('.//crossref'):
        letter = crossref.get('let')
        
        if letter in seen_letters:
            # Mark for removal - this is a duplicate
            to_remove.append(crossref)
        else:
            seen_letters.add(letter)
    
    return to_remove, len(seen_letters)

def deduplicate_chapter(xml_file, dry_run=True):
    """Remove duplicate cross-references from all verses in a chapter."""
    try:
        tree = ET.parse(xml_file)
        root = tree.getroot()
        
        total_removed = 0
        total_kept = 0
        modified_verses = []
        
        # Process each verse
        for verse in root.findall('.//v[@n]'):
            verse_num = verse.get('n')
            
            # Get duplicates to remove
            to_remove, kept = deduplicate_verse_crossrefs(verse)
            
            if to_remove:
                modified_verses.append({
                    'verse': verse_num,
                    'removed': len(to_remove),
                    'kept': kept
                })
                
                if not dry_run:
                    # Remove duplicates
                    for crossref in to_remove:
                        # Find parent element
                        for parent in verse.iter():
                            if crossref in list(parent):
                                parent.remove(crossref)
                                break
                
                total_removed += len(to_remove)
                total_kept += kept
        
        if total_removed > 0:
            if not dry_run:
                # Save the modified XML
                tree.write(xml_file, encoding='utf-8', xml_declaration=True)
            
            return {
                'file': xml_file.name,
                'removed': total_removed,
                'kept': total_kept,
                'verses': modified_verses
            }
        
        return None
        
    except Exception as e:
        print(f"Error processing {xml_file}: {e}")
        return None

def main():
    dry_run = '--apply' not in sys.argv
    
    if dry_run:
        print("=" * 80)
        print("DRY RUN MODE - No files will be modified")
        print("Run with --apply to actually remove duplicates")
        print("=" * 80)
        print()
    
    xml_dir = Path('xml_esv')
    
    if not xml_dir.exists():
        print("Error: xml_esv directory not found!")
        return
    
    xml_files = sorted(xml_dir.glob('*.xml'))
    
    total_files_modified = 0
    total_duplicates_removed = 0
    
    for xml_file in xml_files:
        result = deduplicate_chapter(xml_file, dry_run=dry_run)
        
        if result:
            total_files_modified += 1
            total_duplicates_removed += result['removed']
            
            print(f"{result['file']}")
            print(f"  Removed {result['removed']} duplicates, kept {result['kept']} unique")
            
            # Show first few modified verses
            for verse_info in result['verses'][:3]:
                print(f"    Verse {verse_info['verse']}: removed {verse_info['removed']} duplicates")
            
            if len(result['verses']) > 3:
                print(f"    ... and {len(result['verses']) - 3} more verses")
            print()
    
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Files modified: {total_files_modified}")
    print(f"Duplicate cross-references removed: {total_duplicates_removed}")
    
    if dry_run:
        print()
        print("This was a DRY RUN - no files were modified")
        print("Run with --apply to actually remove the duplicates")
    else:
        print()
        print("✓ Duplicates have been removed from XML files")

if __name__ == '__main__':
    main()
