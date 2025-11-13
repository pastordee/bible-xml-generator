#!/usr/bin/env python3
"""
Split the large ESV text file into individual chapter files.
Automatically detects book/chapter boundaries and creates files like:
- chapter_texts/matthew_1.txt
- chapter_texts/john_7.txt
- etc.
"""

import re
from pathlib import Path

def split_into_chapters(input_file, output_dir):
    """Split text file into individual chapter files."""
    
    text = Path(input_file).read_text(encoding='utf-8')
    
    # Remove opening/closing braces if present
    text = text.strip()
    if text.startswith('{'):
        text = text[1:]
    if text.endswith('}'):
        text = text[:-1]
    text = text.strip()
    
    # Pattern to match book chapter markers: "MATTHEW 1 [†]", "JOHN 7 [†]", "1 CORINTHIANS 3 [†]", etc.
    # The book/chapter line comes after a section heading
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
        print(f"✓ Created: {filename}")
    
    return chapters_created

def main():
    print("="*80)
    print("SPLITTING ESV TEXT INTO CHAPTERS")
    print("="*80)
    print()
    
    input_file = 'esv.json'
    output_dir = 'chapter_texts'
    
    if not Path(input_file).exists():
        print(f"Error: {input_file} not found!")
        return
    
    print(f"Reading from: {input_file}")
    print(f"Writing to:   {output_dir}/")
    print()
    
    count = split_into_chapters(input_file, output_dir)
    
    print()
    print("="*80)
    print(f"✅ Created {count} chapter files!")
    print("="*80)
    print()
    print("Next step: Run batch_add_crossrefs.py to process all chapters")

if __name__ == '__main__':
    main()
