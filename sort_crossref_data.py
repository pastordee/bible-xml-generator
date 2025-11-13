#!/usr/bin/env python3
"""
Sort cross-reference data files by verse order.
This makes the data files easier to read and verify.
"""

import os
from pathlib import Path
from collections import defaultdict


def parse_and_sort_crossref_file(file_path):
    """Parse a crossref file and return sorted verse blocks."""
    
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Store the chapter line
    chapter_line = None
    if lines and lines[0].startswith('C '):
        chapter_line = lines[0]
        lines = lines[1:]
    
    # Parse into verse blocks
    verse_blocks = defaultdict(list)
    current_verse = None
    current_block = []
    
    for line in lines:
        stripped = line.strip()
        
        if stripped.startswith('V '):
            # Save previous verse block
            if current_verse and current_block:
                verse_blocks[current_verse] = current_block
            
            # Start new verse block
            verse_id = stripped.split()[1]
            current_verse = int(verse_id)  # Convert to int for proper sorting
            current_block = [line]  # Include the V line
        
        elif current_verse is not None:
            current_block.append(line)
    
    # Save last verse block
    if current_verse and current_block:
        verse_blocks[current_verse] = current_block
    
    return chapter_line, verse_blocks


def write_sorted_crossref_file(file_path, chapter_line, verse_blocks):
    """Write sorted verse blocks back to file."""
    
    with open(file_path, 'w', encoding='utf-8') as f:
        # Write chapter line
        if chapter_line:
            f.write(chapter_line)
        
        # Write verse blocks in sorted order
        for verse_id in sorted(verse_blocks.keys()):
            for line in verse_blocks[verse_id]:
                f.write(line)


def sort_all_crossref_files(base_dir):
    """Sort all crossref data files in the directory."""
    
    crossref_dir = Path(base_dir) / "raw" / "cross_refs"
    
    if not crossref_dir.exists():
        print(f"❌ Directory not found: {crossref_dir}")
        return
    
    # Get all book directories
    book_dirs = sorted([d for d in crossref_dir.iterdir() if d.is_dir()])
    
    total_files = 0
    sorted_files = 0
    
    print("="*80)
    print("SORTING CROSS-REFERENCE DATA FILES")
    print("="*80)
    print(f"\nFound {len(book_dirs)} book directories\n")
    
    for book_dir in book_dirs:
        book_name = book_dir.name
        txt_files = sorted(book_dir.glob("*.txt"))
        
        if not txt_files:
            continue
        
        print(f"📖 {book_name}: ", end="", flush=True)
        
        for txt_file in txt_files:
            total_files += 1
            
            try:
                chapter_line, verse_blocks = parse_and_sort_crossref_file(txt_file)
                write_sorted_crossref_file(txt_file, chapter_line, verse_blocks)
                sorted_files += 1
                print("✓", end="", flush=True)
            
            except Exception as e:
                print(f"\n  ❌ Error in {txt_file.name}: {e}")
        
        print()  # New line after each book
    
    print("\n" + "="*80)
    print("✅ SORTING COMPLETE")
    print("="*80)
    print(f"Total files processed: {total_files}")
    print(f"Successfully sorted: {sorted_files}")
    print(f"Success rate: {(sorted_files/total_files*100):.1f}%")


if __name__ == "__main__":
    base_dir = Path(__file__).parent
    sort_all_crossref_files(base_dir)
