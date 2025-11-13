#!/usr/bin/env python3
"""
Extract NKJV cross-references from the full NKJV Study Bible text file.
This script finds cross-reference markers and formats them properly.
"""

import re
import os

def extract_genesis_crossrefs(input_file):
    """Extract all Genesis cross-references from the NKJV Study Bible file."""
    
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find Genesis section - look for "CHAPTER 1" after "GENESIS" or similar patterns
    # The Genesis text starts around line 2140 based on our search
    lines = content.split('\n')
    
    # Find where Genesis chapters start - look for first CHAPTER 1
    genesis_start = None
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith('CHAPTER 1') and i < 10000:  # First one should be Genesis
            genesis_start = i
            print(f"Found Genesis Chapter 1 at line {i}")
            break
    
    if not genesis_start:
        print("Could not find Genesis Chapter 1")
        return {}
    
    # Find where Genesis ends (look for Exodus or another book)
    genesis_end = None
    for i in range(genesis_start + 100, len(lines)):
        if re.search(r'^(EXODUS|Exodus)', lines[i]) or 'The Second Book' in lines[i]:
            genesis_end = i
            break
    
    if not genesis_end:
        genesis_end = genesis_start + 10000  # Default large range
    
    print(f"Processing Genesis from line {genesis_start} to {genesis_end}")
    
    # Extract the Genesis section
    genesis_text = '\n'.join(lines[genesis_start:genesis_end])
    
    # Find all chapter markers
    chapter_pattern = r'CHAPTER (\d+)'
    chapter_matches = list(re.finditer(chapter_pattern, genesis_text))
    
    chapters = {}
    
    for idx, match in enumerate(chapter_matches):
        chapter_num = match.group(1)
        chapter_start_pos = match.start()
        
        # Find where this chapter ends (start of next chapter or end of text)
        if idx + 1 < len(chapter_matches):
            chapter_end_pos = chapter_matches[idx + 1].start()
        else:
            chapter_end_pos = len(genesis_text)
        
        chapter_text = genesis_text[chapter_start_pos:chapter_end_pos]
        
        print(f"\nProcessing Chapter {chapter_num}...")
        refs = extract_chapter_crossrefs(chapter_text, chapter_num)
        
        if refs:
            chapters[chapter_num] = refs
            print(f"  Found {len(refs)} cross-references")
    
    return chapters


def extract_chapter_crossrefs(chapter_text, chapter_num):
    """Extract cross-references from a single chapter."""
    
    crossrefs = []
    
    # Pattern to match: verse number followed by letter followed by Bible reference
    # Example: "1 a Ps. 102:25; Is."
    pattern = r'^(\d+)\s+([a-z])\s+(.+)$'
    
    lines = chapter_text.split('\n')
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        if not line or line.startswith('CHAPTER'):
            i += 1
            continue
        
        # Try to match the pattern
        match = re.match(pattern, line)
        if match:
            verse_num = match.group(1)
            letter = match.group(2)
            reference_start = match.group(3).strip()
            
            # The reference might continue on the next lines
            full_reference = reference_start
            
            # Look ahead to see if reference continues
            j = i + 1
            while j < len(lines):
                next_line = lines[j].strip()
                
                # Stop if we hit another verse reference
                if re.match(r'^\d+\s+[a-z]\s+', next_line):
                    break
                if next_line.startswith('CHAPTER'):
                    break
                if not next_line:  # Empty line might indicate end
                    break
                    
                # This line is a continuation - add it
                full_reference += ' ' + next_line
                j += 1
            
            # Clean up the reference
            cleaned_ref = clean_reference(full_reference)
            
            if cleaned_ref and is_valid_reference(cleaned_ref):
                crossrefs.append({
                    'verse': verse_num,
                    'letter': letter,
                    'reference': cleaned_ref
                })
                print(f"    {verse_num}:{letter} - {cleaned_ref[:60]}...")
            
            # Move to the next unprocessed line
            i = j
        else:
            i += 1
    
    return crossrefs


def clean_reference(text):
    """Clean up a cross-reference text."""
    
    # Remove footnote numbers (single digits at the end)
    text = re.sub(r'\s+\d+\s*$', '', text)
    
    # Remove explanatory notes in the reference
    # Common patterns: "1 Heb.", "2 Lit.", "3 Or", etc.
    text = re.sub(r'\s+\d+\s+(Heb\.|Lit\.|Or|Syr\.|M-Text|NU-Text|LXX|Sam\.).*$', '', text)
    
    # Remove multiple spaces
    text = re.sub(r'\s+', ' ', text)
    
    # Remove trailing punctuation except for periods in abbreviations
    text = text.strip()
    
    return text


def is_valid_reference(text):
    """Check if text looks like a valid Bible reference."""
    
    # Must contain a colon or period (for verse/chapter references)
    # and must contain a capital letter (for book names)
    if not re.search(r'[A-Z]', text):
        return False
    
    if not (':' in text or '.' in text):
        return False
    
    # Reject if it looks like commentary
    reject_patterns = [
        r'Words in italic',
        r'Lit\.',
        r'Heb\.',
        r'morning was',
        r'expanse',
        r'luminaries',
        r'souls',
        r'living soul',
        r'moves about',
        r'Syr\. all',
        r'^\d+\s*$',  # Just numbers
    ]
    
    for pattern in reject_patterns:
        if re.search(pattern, text):
            return False
    
    return True


def format_for_output(chapters):
    """Format extracted cross-references for output."""
    
    output = "Genesis\n"
    
    for chapter_num in sorted(chapters.keys(), key=int):
        output += f"CHAPTER {chapter_num}\n\n"
        
        refs = chapters[chapter_num]
        
        # Group by verse
        verse_groups = {}
        for ref in refs:
            verse = ref['verse']
            if verse not in verse_groups:
                verse_groups[verse] = []
            verse_groups[verse].append(ref)
        
        # Output in order
        for verse in sorted(verse_groups.keys(), key=int):
            for ref in verse_groups[verse]:
                output += f"{verse} {ref['letter']} {ref['reference']}\n"
            output += "\n"
    
    return output


def main():
    input_file = 'raw/cross_refs_nkjv/nkjv2.txt'
    output_file = 'raw/cross_refs_nkjv/genesis_extracted.txt'
    
    if not os.path.exists(input_file):
        print(f"Error: {input_file} not found!")
        return
    
    print("Extracting Genesis cross-references from NKJV Study Bible...")
    print("=" * 70)
    
    chapters = extract_genesis_crossrefs(input_file)
    
    if chapters:
        formatted_output = format_for_output(chapters)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(formatted_output)
        
        print("=" * 70)
        print(f"\nExtracted {len(chapters)} chapters")
        print(f"Output written to: {output_file}")
        
        # Show summary
        total_refs = sum(len(refs) for refs in chapters.values())
        print(f"Total cross-references: {total_refs}")
    else:
        print("No chapters found!")


if __name__ == '__main__':
    main()
