#!/usr/bin/env python3
"""
Universal Cross-Reference Integration Script
Integrates cross-references from raw data files into ALL Bible version XML files.
"""

import os
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from collections import defaultdict

# Book name mapping: data file folder name -> book number
BOOK_MAPPING = {
    '1_chronicles': 13, '1_corinthians': 46, '1_john': 62, '1_kings': 11,
    '1_peter': 60, '1_samuel': 9, '1_thessalonians': 52, '1_timothy': 54,
    '2_chronicles': 14, '2_corinthians': 47, '2_john': 63, '2_kings': 12,
    '2_peter': 61, '2_samuel': 10, '2_thessalonians': 53, '2_timothy': 55,
    '3_john': 64, 'acts': 44, 'amos': 30, 'colossians': 51, 'daniel': 27,
    'deuteronomy': 5, 'ecclesiastes': 21, 'ephesians': 49, 'esther': 17,
    'exodus': 2, 'ezekiel': 26, 'ezra': 15, 'galatians': 48, 'genesis': 1,
    'habakkuk': 35, 'haggai': 37, 'hebrews': 58, 'hosea': 28, 'isaiah': 23,
    'james': 59, 'jeremiah': 24, 'job': 18, 'joel': 29, 'john': 43,
    'jonah': 32, 'joshua': 6, 'jude': 65, 'judges': 7, 'lamentations': 25,
    'leviticus': 3, 'luke': 42, 'malachi': 39, 'mark': 41, 'matthew': 40,
    'micah': 33, 'nahum': 34, 'nehemiah': 16, 'numbers': 4, 'obadiah': 31,
    'philemon': 57, 'philippians': 50, 'proverbs': 20, 'psalms': 19,
    'revelation': 66, 'romans': 45, 'ruth': 8, 'song_of_solomon': 22,
    'titus': 56, 'zechariah': 38, 'zephaniah': 36
}

# Reverse mapping: book number -> standard name for file lookup
BOOK_NUM_TO_NAME = {
    1: 'genesis', 2: 'exodus', 3: 'leviticus', 4: 'numbers', 5: 'deuteronomy',
    6: 'joshua', 7: 'judges', 8: 'ruth', 9: '1_samuel', 10: '2_samuel',
    11: '1_kings', 12: '2_kings', 13: '1_chronicles', 14: '2_chronicles',
    15: 'ezra', 16: 'nehemiah', 17: 'esther', 18: 'job', 19: 'psalms',
    20: 'proverbs', 21: 'ecclesiastes', 22: 'song_of_solomon', 23: 'isaiah',
    24: 'jeremiah', 25: 'lamentations', 26: 'ezekiel', 27: 'daniel',
    28: 'hosea', 29: 'joel', 30: 'amos', 31: 'obadiah', 32: 'jonah',
    33: 'micah', 34: 'nahum', 35: 'habakkuk', 36: 'zephaniah', 37: 'haggai',
    38: 'zechariah', 39: 'malachi', 40: 'matthew', 41: 'mark', 42: 'luke',
    43: 'john', 44: 'acts', 45: 'romans', 46: '1_corinthians',
    47: '2_corinthians', 48: 'galatians', 49: 'ephesians', 50: 'philippians',
    51: 'colossians', 52: '1_thessalonians', 53: '2_thessalonians',
    54: '1_timothy', 55: '2_timothy', 56: 'titus', 57: 'philemon',
    58: 'hebrews', 59: 'james', 60: '1_peter', 61: '2_peter', 62: '1_john',
    63: '2_john', 64: '3_john', 65: 'jude', 66: 'revelation'
}


def parse_crossref_data_file(file_path):
    """Parse a cross-reference data file and return structured data."""
    crossrefs = defaultdict(list)
    
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    current_verse = None
    current_ref = {}
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # Verse line: V 13001029
        if line.startswith('V '):
            if current_verse and current_ref:
                crossrefs[current_verse].append(current_ref)
            
            verse_id = line.split()[1]
            current_verse = verse_id
            current_ref = {}
        
        # Letter code: c k
        elif line.startswith('c '):
            if current_ref:
                crossrefs[current_verse].append(current_ref)
            current_ref = {'letter': line.split()[1]}
        
        # Cross-reference ID: i c13001029.1
        elif line.startswith('i '):
            current_ref['cid'] = line.split()[1]
    
    # Add last reference
    if current_verse and current_ref:
        crossrefs[current_verse].append(current_ref)
    
    return crossrefs


def integrate_crossrefs_into_xml(xml_file, crossref_data):
    """Update cross-reference letter codes in XML file and remove invalid ones."""
    
    try:
        tree = ET.parse(xml_file)
        root = tree.getroot()
    except ET.ParseError as e:
        print(f"    ❌ Parse error: {e}")
        return False
    
    # Find all crossref elements grouped by verse, keeping track of parent
    from collections import defaultdict
    verse_crossrefs = defaultdict(list)
    
    for crossref_elem in root.findall('.//crossref'):
        cid = crossref_elem.get('cid')
        if not cid:
            continue
        
        # Extract verse ID from cid (e.g., "c43003001.1" -> "43003001")
        match = re.match(r'c(\d{8})', cid)
        if not match:
            continue
        
        verse_id = match.group(1)
        
        # Find parent element
        for parent in root.iter():
            if crossref_elem in list(parent):
                verse_crossrefs[verse_id].append((crossref_elem, parent))
                break
    
    # Update or remove crossrefs
    crossrefs_updated = 0
    crossrefs_removed = 0
    
    for verse_id, crossref_list in verse_crossrefs.items():
        if verse_id not in crossref_data:
            # Verse has no crossrefs in data - remove all crossrefs from XML
            for crossref_elem, parent in crossref_list:
                parent.remove(crossref_elem)
                crossrefs_removed += 1
            continue
        
        # Get the letters from data file for this verse (in order)
        data_letters = [ref['letter'] for ref in crossref_data[verse_id]]
        
        # Update crossrefs that should exist, remove extras
        for idx, (crossref_elem, parent) in enumerate(crossref_list):
            if idx < len(data_letters):
                # Update letter
                old_letter = crossref_elem.get('let')
                new_letter = data_letters[idx]
                
                if old_letter != new_letter:
                    crossref_elem.set('let', new_letter)
                    crossrefs_updated += 1
            else:
                # Extra crossref that shouldn't exist - remove it
                parent.remove(crossref_elem)
                crossrefs_removed += 1
    
    if crossrefs_updated > 0 or crossrefs_removed > 0:
        tree.write(xml_file, encoding='utf-8', xml_declaration=True)
        return True
    
    return False


def process_version(version_name, version_dir, crossref_base_dir):
    """Process all XML files for a specific Bible version."""
    
    print(f"\n{'='*80}")
    print(f"Processing {version_name.upper()}")
    print(f"{'='*80}")
    
    xml_files = sorted(Path(version_dir).glob("*.xml"))
    
    if not xml_files:
        print(f"  ⚠️  No XML files found in {version_dir}")
        return
    
    total_files = len(xml_files)
    updated_files = 0
    skipped_files = 0
    
    for xml_file in xml_files:
        # Extract book and chapter from filename (e.g., "john_3.xml")
        filename = xml_file.stem
        parts = filename.rsplit('_', 1)
        
        if len(parts) != 2:
            print(f"  ⚠️  Skipping {filename} (unexpected format)")
            skipped_files += 1
            continue
        
        book_name, chapter = parts
        
        # Find corresponding crossref data file
        crossref_dir = Path(crossref_base_dir) / book_name
        crossref_file = crossref_dir / f"{chapter}.txt"
        
        if not crossref_file.exists():
            skipped_files += 1
            continue
        
        # Parse crossref data
        crossref_data = parse_crossref_data_file(crossref_file)
        
        if not crossref_data:
            skipped_files += 1
            continue
        
        # Integrate into XML
        if integrate_crossrefs_into_xml(str(xml_file), crossref_data):
            updated_files += 1
            print(f"  ✅ Updated {filename}")
    
    print(f"\n📊 Summary for {version_name.upper()}:")
    print(f"  Total files: {total_files}")
    print(f"  Updated: {updated_files}")
    print(f"  Skipped: {skipped_files}")
    print(f"  Success rate: {(updated_files/total_files*100):.1f}%")


def main():
    """Main execution function."""
    
    base_dir = Path(__file__).parent
    crossref_base_dir = base_dir / "raw" / "cross_refs"
    
    # All Bible versions
    versions = {
        'ESV': base_dir / "xml_esv",
        'KJV': base_dir / "xml_kjv",
        'NKJV': base_dir / "xml_nkjv",
        'WEB': base_dir / "xml_web",
        'ASV': base_dir / "xml_asv",
        'BSB': base_dir / "xml_bsb",
        'MSG': base_dir / "xml_msg",
        'AMP': base_dir / "xml_amp",
        'NLT': base_dir / "xml_nlt",
        'BBE': base_dir / "xml_bbe",
    }
    
    print("="*80)
    print("UNIVERSAL CROSS-REFERENCE INTEGRATION")
    print("="*80)
    print(f"\nCross-reference data location: {crossref_base_dir}")
    print(f"Found {len(list(crossref_base_dir.iterdir()))} book directories")
    
    # Check which versions exist
    existing_versions = {name: path for name, path in versions.items() if path.exists()}
    
    if not existing_versions:
        print("\n❌ No version directories found!")
        print("Expected directories:")
        for name, path in versions.items():
            print(f"  - {path}")
        return
    
    print(f"\nFound {len(existing_versions)} version(s) to process:")
    for name in existing_versions:
        print(f"  ✓ {name}")
    
    # Ask user which versions to process
    print("\n" + "="*80)
    print("Which versions would you like to process?")
    print("="*80)
    print("Options:")
    print("  1. All versions")
    print("  2. Select specific versions")
    print("  3. Single version")
    
    choice = input("\nEnter choice (1-3): ").strip()
    
    versions_to_process = []
    
    if choice == "1":
        versions_to_process = list(existing_versions.keys())
    elif choice == "2":
        print("\nAvailable versions:")
        for i, name in enumerate(existing_versions.keys(), 1):
            print(f"  {i}. {name}")
        
        selections = input("\nEnter version numbers (comma-separated, e.g., 1,3,5): ").strip()
        version_list = list(existing_versions.keys())
        
        for sel in selections.split(','):
            try:
                idx = int(sel.strip()) - 1
                if 0 <= idx < len(version_list):
                    versions_to_process.append(version_list[idx])
            except ValueError:
                continue
    elif choice == "3":
        version_name = input("Enter version name (e.g., ESV, KJV): ").strip().upper()
        if version_name in existing_versions:
            versions_to_process = [version_name]
        else:
            print(f"❌ Version '{version_name}' not found")
            return
    else:
        print("❌ Invalid choice")
        return
    
    if not versions_to_process:
        print("❌ No versions selected")
        return
    
    # Process selected versions
    for version_name in versions_to_process:
        version_dir = existing_versions[version_name]
        process_version(version_name, version_dir, crossref_base_dir)
    
    print("\n" + "="*80)
    print("✅ INTEGRATION COMPLETE")
    print("="*80)
    print(f"\nProcessed {len(versions_to_process)} version(s):")
    for name in versions_to_process:
        print(f"  ✓ {name}")


if __name__ == "__main__":
    main()
