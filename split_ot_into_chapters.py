#!/usr/bin/env python3
"""
Split the Old Testament ESV text file into individual chapter files.
"""

import re
from pathlib import Path

def split_into_chapters(input_file, output_dir, start_line=0):
    """Split text file into individual chapter files."""
    
    text = Path(input_file).read_text(encoding='utf-8')
    
    # If there's introductory content, skip to the actual Bible text
    # Genesis should be around line 2890 based on the grep result
    lines = text.split('\n')
    if start_line > 0:
        text = '\n'.join(lines[start_line:])
    
    # Pattern to match book chapter markers
    chapter_pattern = r'^([A-Z\d\s]+?)\s+(\d+)\s+\[†\]'
    
    # Find all chapter markers
    matches = list(re.finditer(chapter_pattern, text, re.MULTILINE))
    
    if not matches:
        print("No chapter markers found!")
        return 0
    
    output_dir = Path(output_dir)
    output_dir.mkdir(exist_ok=True)
    
    chapters_created = 0
    
    for i, match in enumerate(matches):
        book_raw = match.group(1).strip()
        chapter_num = match.group(2)
        
        # Normalize book name for filename
        book_name = book_raw.lower().replace(' ', '_')
        
        # Extract chapter content
        start_pos = match.start()
        
        # Find where this chapter ends (start of next chapter or end of file)
        if i + 1 < len(matches):
            end_pos = matches[i + 1].start()
        else:
            end_pos = len(text)
        
        chapter_text = text[start_pos:end_pos].strip()
        
        # Create output file
        filename = f"{book_name}_{chapter_num}.txt"
        output_path = output_dir / filename
        
        # Write chapter text
        output_path.write_text(chapter_text, encoding='utf-8')
        
        chapters_created += 1
        if chapters_created <= 10 or chapters_created % 50 == 0:
            print(f"✓ Created: {filename}")
    
    return chapters_created

def main():
    print("="*80)
    print("SPLITTING OLD TESTAMENT (GENESIS - MALACHI) INTO CHAPTERS")
    print("="*80)
    print()
    
    input_file = 'esv2.json'
    output_dir = 'chapter_texts_ot'
    
    if not Path(input_file).exists():
        print(f"Error: {input_file} not found!")
        return
    
    print(f"Reading from: {input_file}")
    print(f"Writing to:   {output_dir}/")
    print()
    
    # Start from line 2890 where Genesis begins
    count = split_into_chapters(input_file, output_dir, start_line=2889)
    
    print()
    print("="*80)
    print(f"✅ Created {count} Old Testament chapter files!")
    print("="*80)
    print()
    print("Next step: Update batch_add_crossrefs.py to also check chapter_texts_ot/")

if __name__ == '__main__':
    main()
