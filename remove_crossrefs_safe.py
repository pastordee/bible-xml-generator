#!/usr/bin/env python3
"""
Safely remove cross-references from XML files while preserving verse text.
This script properly handles the 'tail' text that comes after crossref elements.
"""

import xml.etree.ElementTree as ET
from pathlib import Path

def remove_crossrefs_safe(xml_file):
    """Remove crossref elements while preserving their tail text."""
    try:
        tree = ET.parse(xml_file)
        root = tree.getroot()
    except Exception as e:
        print(f"  ERROR parsing {xml_file}: {e}")
        return 0
    
    removed_count = 0
    
    # Find all elements that contain crossref children
    for parent in root.iter():
        crossrefs_to_remove = []
        for i, child in enumerate(list(parent)):
            if child.tag == 'crossref':
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
    
    # Write the modified XML back
    tree.write(xml_file, encoding='utf-8', xml_declaration=True)
    return removed_count


def process_directory(dir_name):
    """Process all XML files in a directory."""
    xml_dir = Path(dir_name)
    
    if not xml_dir.exists():
        print(f"ERROR: Directory not found: {xml_dir}")
        return
    
    print(f"\nProcessing {dir_name}...")
    print("=" * 80)
    
    total_files = 0
    total_modified = 0
    total_removed = 0
    
    for xml_file in sorted(xml_dir.glob('*.xml')):
        removed = remove_crossrefs_safe(xml_file)
        total_files += 1
        if removed > 0:
            total_modified += 1
            total_removed += removed
            if total_modified <= 5:  # Show first 5 examples
                print(f"  ✓ {xml_file.name} - Removed {removed} cross-refs")
    
    print(f"\nSummary for {dir_name}:")
    print(f"  Files processed: {total_files}")
    print(f"  Files modified: {total_modified}")
    print(f"  Cross-refs removed: {total_removed}")


def main():
    # Process the 6 translations that don't have authoritative cross-references
    directories = [
        'xml_amp',
        'xml_asv',
        'xml_bsb',
        'xml_msg',
        'xml_nlt',
        'xml_web'
    ]
    
    print("Safe Cross-Reference Removal")
    print("=" * 80)
    print("This script will remove cross-references while preserving verse text")
    print("=" * 80)
    
    total_files = 0
    total_modified = 0
    total_removed = 0
    
    for dir_name in directories:
        dir_path = Path(dir_name)
        if dir_path.exists():
            print(f"\n📁 Processing {dir_name}...")
            files_processed = 0
            files_modified = 0
            crossrefs_removed = 0
            
            for xml_file in sorted(dir_path.glob('*.xml')):
                removed = remove_crossrefs_safe(xml_file)
                files_processed += 1
                if removed > 0:
                    files_modified += 1
                    crossrefs_removed += removed
            
            print(f"   Files: {files_processed}, Modified: {files_modified}, Removed: {crossrefs_removed}")
            total_files += files_processed
            total_modified += files_modified
            total_removed += crossrefs_removed
    
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Total files processed: {total_files}")
    print(f"Total files modified: {total_modified}")
    print(f"Total cross-refs removed: {total_removed}")
    print("=" * 80)


if __name__ == '__main__':
    main()
