#!/usr/bin/env python3
"""
Fix ESV cross-reference files to use hyphenated ranges instead of space-separated verse IDs.
Example: "01004025 01004026" -> "01004025-01004026"
"""

import re
from pathlib import Path

def fix_ranges_in_line(line):
    """Fix space-separated verse IDs to use hyphens."""
    # Pattern: r followed by multiple verse IDs (8 digits each) separated by spaces
    # Example: r 01004025 01004026 Gen. 4:25, 26
    # Should become: r 01004025-01004026 Gen. 4:25, 26
    
    pattern = r'^r ((?:\d{8}(?: \d{8})+)) (.+)$'
    match = re.match(pattern, line)
    
    if match:
        ids_str = match.group(1).strip()
        rest = match.group(2)
        ids = ids_str.split()
        
        # Join all IDs with hyphens
        joined_ids = '-'.join(ids)
        return f"r {joined_ids} {rest}\n"
    
    return line

def process_file(file_path):
    """Process a single file to fix ranges."""
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    new_lines = []
    changes = 0
    
    for line in lines:
        new_line = fix_ranges_in_line(line)
        if new_line != line:
            changes += 1
        new_lines.append(new_line)
    
    if changes > 0:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)
    
    return changes

def main():
    base_dir = Path('xml_esv/cross_refs')
    
    print("=" * 80)
    print("FIXING ESV CROSS-REFERENCE RANGES")
    print("=" * 80)
    print()
    
    total_files = 0
    total_changes = 0
    
    for book_dir in sorted(base_dir.iterdir()):
        if not book_dir.is_dir():
            continue
        
        for txt_file in sorted(book_dir.glob('*.txt')):
            changes = process_file(txt_file)
            total_files += 1
            
            if changes > 0:
                print(f"{txt_file.relative_to(base_dir)}: {changes} ranges fixed")
                total_changes += changes
    
    print()
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Files processed: {total_files}")
    print(f"Ranges fixed: {total_changes}")
    print("=" * 80)

if __name__ == '__main__':
    main()
