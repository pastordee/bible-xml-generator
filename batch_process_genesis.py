#!/usr/bin/env python3
"""
Batch process remaining Genesis chapters (14-50)
Extracts, formats, and auto-fixes cross-references
"""

import subprocess
import re
from pathlib import Path

# Chapter boundaries in nkjv2_trimmed.txt (Genesis chapters only, first occurrence)
CHAPTER_BOUNDARIES = {
    14: 2760,
    15: 3056,
    16: 3320,
    17: 3495,
    18: 3915,
    19: 4135,
    20: 4462,
    21: 4683,
    22: 4969,
    23: 5143,
    24: 5310,
    25: 5672,
    26: 5903,
    27: 6157,
    28: 6417,
    29: 6629,
    30: 6862,
    31: 7145,
    32: 7450,
    33: 7670,
    34: 7860,
    35: 8083,
    36: 8316,
    37: 8632,
    38: 8877,
    39: 9062,
    40: 9300,
    41: 9478,
    42: 9788,
    43: 10092,
    44: 10359,
    45: 10641,
    46: 10879,
    47: 11161,
    48: 11461,
    49: 11675,
    50: 12092,
    # End marker (Chapter 1 of Exodus)
    51: 12357
}

def extract_crossrefs(chapter_num, start_line, end_line):
    """Extract cross-references for a chapter from nkjv2_trimmed.txt"""
    source_file = Path("raw/cross_refs_nkjv/nkjv2_trimmed.txt")
    
    print(f"Extracting Chapter {chapter_num} (lines {start_line}-{end_line})...")
    
    with open(source_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Extract the section
    section = lines[start_line-1:end_line-1]
    
    # Filter for cross-reference lines (contain letters a-z followed by scripture refs)
    crossref_lines = []
    in_crossrefs = False
    
    for line in section:
        line = line.strip()
        
        # Start of chapter
        if line.startswith(f"CHAPTER {chapter_num}"):
            crossref_lines.append(line)
            in_crossrefs = True
            continue
        
        # Skip if we hit next chapter
        if line.startswith("CHAPTER ") and not line.startswith(f"CHAPTER {chapter_num}"):
            break
            
        # Look for cross-reference pattern: verse number, letter, book reference
        if in_crossrefs and line:
            # Match patterns like "1 a Gen. 14:18" or "a Gen. 14:18"
            if re.match(r'^(\d+\s+)?[a-z]\s+[A-Z]', line) or \
               re.match(r'^\d+\s+[a-z]', line):
                crossref_lines.append(line)
    
    return crossref_lines

def create_raw_file(chapter_num, crossref_lines):
    """Create the raw chapter file"""
    output_file = Path(f"genesis_ch{chapter_num}_raw.txt")
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(crossref_lines))
    
    print(f"  Created {output_file}")
    return output_file

def format_chapter(chapter_num, raw_file):
    """Run format_crossrefs.py on the chapter"""
    print(f"  Formatting Chapter {chapter_num}...")
    
    cmd = f'echo "{chapter_num}" | python3 format_crossrefs.py {raw_file}'
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    
    if result.returncode == 0:
        formatted_file = raw_file.with_name(raw_file.stem + "_formatted.txt")
        print(f"  Formatted: {formatted_file}")
        return formatted_file
    else:
        print(f"  ERROR formatting: {result.stderr}")
        return None

def auto_fix_truncations(chapter_num, formatted_file, raw_file):
    """Auto-fix common truncation issues"""
    print(f"  Auto-fixing truncations in Chapter {chapter_num}...")
    
    with open(formatted_file, 'r', encoding='utf-8') as f:
        formatted_content = f.read()
    
    with open(raw_file, 'r', encoding='utf-8') as f:
        raw_content = f.read()
    
    # Find truncated references (lines ending with comma or incomplete)
    truncated_pattern = r'(\d+\s+[a-z]\s+[^;\n]+)[,;]\s*$'
    
    fixes = 0
    lines = formatted_content.split('\n')
    
    for i, line in enumerate(lines):
        # Look for trailing commas or incomplete references
        if re.search(r'[,;]\s*$', line) and not line.startswith('CHAPTER'):
            # Try to find the complete reference in raw file
            # Extract verse and letter
            match = re.match(r'^(\d+)\s+([a-z])\s+(.+)[,;]\s*$', line)
            if match:
                verse, letter, partial_ref = match.groups()
                
                # Search in raw content for complete reference
                raw_pattern = rf'{verse}\s+{letter}\s+([^\n]+)'
                raw_match = re.search(raw_pattern, raw_content)
                
                if raw_match:
                    complete_ref = raw_match.group(1).replace('\n', ' ').strip()
                    # Clean up extra spaces
                    complete_ref = re.sub(r'\s+', ' ', complete_ref)
                    lines[i] = f"{verse} {letter} {complete_ref}"
                    fixes += 1
    
    if fixes > 0:
        with open(formatted_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
        print(f"  Fixed {fixes} truncations")
    else:
        print(f"  No truncations to fix")
    
    return fixes

def process_chapter(chapter_num):
    """Process a single chapter: extract, format, auto-fix"""
    start_line = CHAPTER_BOUNDARIES[chapter_num]
    end_line = CHAPTER_BOUNDARIES[chapter_num + 1]
    
    # Extract cross-references
    crossref_lines = extract_crossrefs(chapter_num, start_line, end_line)
    
    if not crossref_lines:
        print(f"  WARNING: No cross-references found for Chapter {chapter_num}")
        return False
    
    # Create raw file
    raw_file = create_raw_file(chapter_num, crossref_lines)
    
    # Format
    formatted_file = format_chapter(chapter_num, raw_file)
    
    if not formatted_file:
        return False
    
    # Auto-fix
    auto_fix_truncations(chapter_num, formatted_file, raw_file)
    
    print(f"✓ Chapter {chapter_num} complete\n")
    return True

def main():
    print("=" * 70)
    print("GENESIS BATCH PROCESSOR - Chapters 14-50")
    print("=" * 70)
    print()
    
    success_count = 0
    failed_chapters = []
    
    for chapter in range(14, 51):
        try:
            if process_chapter(chapter):
                success_count += 1
            else:
                failed_chapters.append(chapter)
        except Exception as e:
            print(f"ERROR processing Chapter {chapter}: {e}")
            failed_chapters.append(chapter)
    
    print("=" * 70)
    print(f"COMPLETED: {success_count}/37 chapters processed successfully")
    
    if failed_chapters:
        print(f"FAILED: Chapters {failed_chapters}")
    else:
        print("All chapters processed successfully!")
    
    print("=" * 70)

if __name__ == "__main__":
    main()
