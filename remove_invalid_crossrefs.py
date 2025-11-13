#!/usr/bin/env python3
"""
Remove Invalid Cross-References Script
Removes ALL cross-references from verses that don't have any in the comprehensive data files.
This cleans up fake/placeholder cross-references.
"""

import os
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from collections import defaultdict


def parse_crossref_data_file(file_path):
    """Parse a cross-reference data file and return verse IDs that SHOULD have crossrefs."""
    verses_with_crossrefs = set()
    
    if not file_path.exists():
        return verses_with_crossrefs
    
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    current_verse = None
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        if line.startswith('V '):
            verse_id = line.split()[1]
            verses_with_crossrefs.add(verse_id)
    
    return verses_with_crossrefs


def remove_invalid_crossrefs(xml_file, verses_with_crossrefs):
    """Remove cross-references from verses that shouldn't have them."""
    
    try:
        tree = ET.parse(xml_file)
        root = tree.getroot()
    except ET.ParseError as e:
        print(f"    ❌ Parse error: {e}")
        return False, 0
    
    crossrefs_removed = 0
    
    # Find all crossref elements
    for parent in root.iter():
        for crossref_elem in list(parent.findall('crossref')):
            cid = crossref_elem.get('cid')
            if not cid:
                continue
            
            # Extract verse ID from cid
            match = re.match(r'c(\d{8})', cid)
            if not match:
                continue
            
            verse_id = match.group(1)
            
            # If this verse shouldn't have cross-references, remove it
            if verse_id not in verses_with_crossrefs:
                parent.remove(crossref_elem)
                crossrefs_removed += 1
    
    if crossrefs_removed > 0:
        tree.write(xml_file, encoding='utf-8', xml_declaration=True)
        return True, crossrefs_removed
    
    return False, 0


def process_version(version_name, version_dir, crossref_base_dir):
    """Process all XML files for a specific Bible version."""
    
    print(f"\n{'='*80}")
    print(f"Removing Invalid Cross-References from {version_name.upper()}")
    print(f"{'='*80}")
    
    xml_files = sorted(Path(version_dir).glob("*.xml"))
    
    if not xml_files:
        print(f"  ⚠️  No XML files found in {version_dir}")
        return
    
    total_files = len(xml_files)
    updated_files = 0
    skipped_files = 0
    total_removed = 0
    
    for xml_file in xml_files:
        # Extract book and chapter from filename
        filename = xml_file.stem
        parts = filename.rsplit('_', 1)
        
        if len(parts) != 2:
            skipped_files += 1
            continue
        
        book_name, chapter = parts
        
        # Find corresponding crossref data file
        crossref_dir = Path(crossref_base_dir) / book_name
        crossref_file = crossref_dir / f"{chapter}.txt"
        
        if not crossref_file.exists():
            skipped_files += 1
            continue
        
        # Parse crossref data to get verses that SHOULD have crossrefs
        verses_with_crossrefs = parse_crossref_data_file(crossref_file)
        
        # Remove invalid crossrefs
        updated, removed = remove_invalid_crossrefs(str(xml_file), verses_with_crossrefs)
        
        if updated:
            updated_files += 1
            total_removed += removed
            print(f"  ✅ {filename}: Removed {removed} invalid crossrefs")
    
    print(f"\n📊 Summary for {version_name.upper()}:")
    print(f"  Total files: {total_files}")
    print(f"  Updated: {updated_files}")
    print(f"  Skipped: {skipped_files}")
    print(f"  Total crossrefs removed: {total_removed:,}")
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
    print("REMOVE INVALID CROSS-REFERENCES")
    print("="*80)
    print(f"\nCross-reference data location: {crossref_base_dir}")
    print(f"Found {len(list(crossref_base_dir.iterdir()))} book directories")
    
    # Check which versions exist
    existing_versions = {name: path for name, path in versions.items() if path.exists()}
    
    if not existing_versions:
        print("\n❌ No version directories found!")
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
    print("✅ CLEANUP COMPLETE")
    print("="*80)
    print(f"\nProcessed {len(versions_to_process)} version(s):")
    for name in versions_to_process:
        print(f"  ✓ {name}")
    
    print("\nNext step: Run integrate_all_crossrefs.py to fix remaining crossref letters")


if __name__ == "__main__":
    main()
