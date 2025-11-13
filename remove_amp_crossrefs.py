#!/usr/bin/env python3
"""
Remove all cross-references from AMP XML files only.
"""

import xml.etree.ElementTree as ET
from pathlib import Path


def remove_crossrefs_from_file(xml_file):
    """Remove all <crossref> elements from an XML file."""
    try:
        tree = ET.parse(xml_file)
        root = tree.getroot()
        
        removed_count = 0
        
        # Find all crossref elements and remove them
        for verse in root.findall('.//v'):
            crossrefs = verse.findall('.//crossref')
            for crossref in crossrefs:
                verse.remove(crossref)
                removed_count += 1
        
        if removed_count > 0:
            tree.write(xml_file, encoding='utf-8', xml_declaration=True)
        
        return removed_count
    except Exception as e:
        print(f"  ERROR processing {xml_file.name}: {e}")
        return 0


def main():
    xml_dir = Path('xml_amp')
    
    if not xml_dir.exists():
        print(f"Directory not found: {xml_dir}")
        return
    
    print("=" * 70)
    print("REMOVING ALL CROSS-REFERENCES FROM AMP")
    print("=" * 70)
    
    xml_files = sorted(xml_dir.glob('*.xml'))
    
    if not xml_files:
        print(f"  No XML files found")
        return
    
    total_removed = 0
    files_modified = 0
    
    for xml_file in xml_files:
        removed = remove_crossrefs_from_file(xml_file)
        if removed > 0:
            files_modified += 1
            total_removed += removed
            print(f"  ✓ {xml_file.name.ljust(40)} - Removed {removed:3d} cross-refs")
    
    print(f"\n  Summary:")
    print(f"    Files processed: {len(xml_files)}")
    print(f"    Files modified: {files_modified}")
    print(f"    Total cross-refs removed: {total_removed}")
    print("=" * 70)


if __name__ == '__main__':
    main()
