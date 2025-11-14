#!/usr/bin/env python3
"""
Reformat NKJV chapter files to match the cleaner manual format:
- Each verse on its own line (fix number splitting)
- Footnotes section (if available)
- Cross references all together at bottom (not grouped by verse)
"""

import os
import re
from pathlib import Path


def reformat_chapter_file(input_file, output_file):
    """Reformat a chapter file to the cleaner format"""
    
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Split into verse section and crossref section
    if '=' * 80 in content:
        parts = content.split('=' * 80)
        verse_text = parts[0].strip()
        # Crossrefs are in the part after "CROSS REFERENCES" header
        crossref_section = ""
        for part in parts[1:]:
            if 'Verse' in part:  # This is the actual crossref data
                crossref_section = part
                break
    else:
        verse_text = content.strip()
        crossref_section = ""
    
    # Parse verses - need to handle line breaks in the middle of verse numbers
    # The downloaded format has verse numbers split across lines (e.g., "1\n0" for verse 10)
    # First, fix split verse numbers: digit + newline + digit -> digit + digit
    verse_text_fixed = re.sub(r'(\d)\n(\d)', r'\1\2', verse_text)
    
    # Now join all lines and normalize whitespace
    verse_text_cleaned = verse_text_fixed.replace('\n', ' ')
    verse_text_cleaned = re.sub(r'\s+', ' ', verse_text_cleaned).strip()
    
    # Split by verse numbers - handle verse 1 at start
    # Pattern: number followed by space (including at start of string)
    verse_parts = re.split(r'(?:^|(?<=\s))(\d+)\s+', verse_text_cleaned)
    
    formatted_verses = []
    # verse_parts will be: ['', '1', 'verse 1 text', '2', 'verse 2 text', ...]
    # OR if verse 1 at start: ['', '1', 'verse 1 text', '2', 'verse 2 text', ...]
    for i in range(1, len(verse_parts), 2):
        if i + 1 < len(verse_parts):
            verse_num = verse_parts[i]
            verse_content = verse_parts[i + 1].strip()
            if verse_content:  # Skip empty verses
                formatted_verses.append(f"{verse_num} {verse_content}")
    
    # Parse crossrefs from grouped format
    crossrefs = []
    if crossref_section:
        current_verse = None
        
        for line in crossref_section.split('\n'):
            line = line.strip()
            if not line or line == 'CROSS REFERENCES':
                continue
            
            # Check for verse header: "Verse 1:"
            verse_match = re.match(r'^Verse (\d+):$', line)
            if verse_match:
                current_verse = verse_match.group(1)
                continue
            
            # Check for crossref data: "  a: Rom. 1:1"
            ref_match = re.match(r'^\s*([a-z]+):\s*(.+)$', line)
            if ref_match and current_verse:
                letter = ref_match.group(1)
                refs = ref_match.group(2)
                crossrefs.append((current_verse, letter, refs))
    
    # Build output content
    output_lines = []
    
    # Add verses
    for verse in formatted_verses:
        output_lines.append(verse)
    
    output_lines.append('')
    output_lines.append('')
    
    # Add footnotes section (empty for now - not in scraped data)
    output_lines.append('Footnotes')
    output_lines.append('')
    
    # Add cross references section (flat format like manual)
    output_lines.append('Cross references')
    
    # Get book/chapter info from filename
    filename = os.path.basename(input_file)
    book_chapter = filename.replace('.txt', '').replace('_', ' ').title()
    
    # Output all crossrefs in flat format: "Book Chapter:Verse : References"
    for verse_num, letter, refs in crossrefs:
        output_lines.append(f"{book_chapter}:{verse_num} : {refs}")
    
    # Write output
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(output_lines))


def reformat_all_chapters():
    """Reformat all chapter files from nkjv_with_crossrefs_* to cleaned format"""
    
    input_ot_dir = Path('raw/nkjv_with_crossrefs_ot')
    input_nt_dir = Path('raw/nkjv_with_crossrefs_nt')
    output_ot_dir = Path('raw/nkjv_cleaned_ot')
    output_nt_dir = Path('raw/nkjv_cleaned_nt')
    
    # Create output directories
    output_ot_dir.mkdir(parents=True, exist_ok=True)
    output_nt_dir.mkdir(parents=True, exist_ok=True)
    
    total_files = 0
    
    # Process OT files
    if input_ot_dir.exists():
        for input_file in sorted(input_ot_dir.glob('*.txt')):
            output_file = output_ot_dir / input_file.name
            reformat_chapter_file(input_file, output_file)
            total_files += 1
            if total_files % 100 == 0:
                print(f"  Processed {total_files} files...")
    
    # Process NT files
    if input_nt_dir.exists():
        for input_file in sorted(input_nt_dir.glob('*.txt')):
            output_file = output_nt_dir / input_file.name
            reformat_chapter_file(input_file, output_file)
            total_files += 1
            if total_files % 100 == 0:
                print(f"  Processed {total_files} files...")
    
    print(f"\n✓ Reformatted {total_files} chapter files")
    print(f"  Output: raw/nkjv_cleaned_ot/ and raw/nkjv_cleaned_nt/")


if __name__ == '__main__':
    print("Reformatting NKJV chapter files...")
    print()
    reformat_all_chapters()
