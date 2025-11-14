#!/usr/bin/env python3
"""
Format NKJV chapter files to match the clean manual format:
- Section headings on their own lines
- Each verse on its own line
- Footnotes section with each footnote on separate line
- Cross references section with each reference on separate line
"""

import os
import re
from pathlib import Path


def format_chapter_file(input_file, output_file):
    """Format a chapter file to match the manual clean format"""
    
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read().strip()
    
    # Split into three sections: verses, footnotes, cross references
    # Pattern: look for "Footnotes" and "Cross references" markers
    footnotes_match = re.search(r'\bFootnotes\b', content)
    crossrefs_match = re.search(r'\bCross references\b', content)
    
    if footnotes_match and crossrefs_match:
        verses_text = content[:footnotes_match.start()].strip()
        footnotes_text = content[footnotes_match.end():crossrefs_match.start()].strip()
        crossrefs_text = content[crossrefs_match.end():].strip()
    else:
        # Fallback: entire content is verses
        verses_text = content
        footnotes_text = ""
        crossrefs_text = ""
    
    # Process verses section
    formatted_verses = format_verses(verses_text)
    
    # Process footnotes section
    formatted_footnotes = format_footnotes(footnotes_text)
    
    # Process cross references section
    formatted_crossrefs = format_crossrefs(crossrefs_text)
    
    # Combine all sections
    output_lines = []
    output_lines.extend(formatted_verses)
    output_lines.append('')
    output_lines.append('')
    output_lines.append('Footnotes')
    output_lines.extend(formatted_footnotes)
    output_lines.append('')
    output_lines.append('Cross references')
    output_lines.extend(formatted_crossrefs)
    
    # Write output
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(output_lines))


def format_verses(text):
    """Format verses - extract section headings and put each verse on its own line"""
    formatted = []
    
    # Strategy: Split by verse numbers while preserving them
    # Pattern: \d+ followed by space at start or after punctuation/heading
    # Use regex to split but keep the numbers
    
    # Find all verses with their positions
    verse_pattern = r'(\d+)\s+'
    parts = re.split(verse_pattern, text)
    
    # parts will be: [text_before_1, '1', text_of_verse_1, '2', text_of_verse_2, ...]
    i = 0
    while i < len(parts):
        part = parts[i].strip()
        
        if not part:
            i += 1
            continue
        
        # Check if this looks like a section heading
        # Section headings are Title Case words (each word starts with capital)
        if part and not part[0].isdigit():
            # This might be a section heading or leftover text
            # Section headings: all words start with capital or are short words
            words = part.split()
            if words and all(w[0].isupper() or w.lower() in ['of', 'the', 'a', 'an', 'in', 'on', 'at', 'to', 'for', 'is', 'and', 'or'] for w in words if w):
                # This is likely a section heading
                formatted.append(part)
        
        # Check if next part is a verse number
        if i + 1 < len(parts) and re.match(r'^\d+$', parts[i + 1].strip()):
            verse_num = parts[i + 1].strip()
            if i + 2 < len(parts):
                verse_text = parts[i + 2].strip()
                
                # Check if verse_text starts with a section heading
                # Look for sequences of Title Case words followed by lowercase text
                heading_match = re.match(r'^([A-Z][a-zA-Z\s]+?)\s+([a-z].+)$', verse_text)
                if heading_match and len(heading_match.group(1).split()) >= 2:
                    # Extract heading
                    heading = heading_match.group(1).strip()
                    remaining = heading_match.group(2).strip()
                    # Check if heading words are all Title Case
                    heading_words = heading.split()
                    if all(w[0].isupper() for w in heading_words):
                        formatted.append(heading)
                        formatted.append(f"{verse_num} {remaining}")
                    else:
                        formatted.append(f"{verse_num} {verse_text}")
                else:
                    formatted.append(f"{verse_num} {verse_text}")
                
                i += 3
                continue
        
        i += 1
    
    return formatted


def format_footnotes(text):
    """Format footnotes - each footnote on its own line"""
    if not text:
        return []
    
    formatted = []
    
    # Pattern: "Book Chapter:Verse description"
    # Split by book references (pattern like "1 Corinthians 2:1")
    parts = re.split(r'(\d?\s*[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?\s+\d+:\d+)', text)
    
    current_ref = None
    for part in parts:
        part = part.strip()
        if not part:
            continue
        
        # Check if this is a reference
        if re.match(r'^\d?\s*[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?\s+\d+:\d+$', part):
            current_ref = part
        elif current_ref:
            formatted.append(f"{current_ref} {part}")
            current_ref = None
    
    return formatted


def format_crossrefs(text):
    """Format cross references - each reference on its own line"""
    if not text:
        return []
    
    formatted = []
    
    # Pattern: "Book Chapter:Verse : Reference"
    # Split by book references (pattern like "1 Corinthians 2:1 :")
    parts = re.split(r'(\d?\s*[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?\s+\d+:\d+\s*:)', text)
    
    current_ref = None
    for part in parts:
        part = part.strip()
        if not part:
            continue
        
        # Check if this is a reference
        if re.match(r'^\d?\s*[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?\s+\d+:\d+\s*:$', part):
            current_ref = part
        elif current_ref:
            formatted.append(f"{current_ref} {part}")
            current_ref = None
    
    return formatted


def process_all_folders():
    """Process all files in the nkjv_crossrefs_* folders"""
    
    input_ot_dir = Path('raw/nkjv_crossrefs_ot')
    input_nt_dir = Path('raw/nkjv_crossrefs_nt')
    
    total_files = 0
    
    print("Formatting NKJV chapter files to match manual format...")
    print()
    
    # Process OT files
    if input_ot_dir.exists():
        for input_file in sorted(input_ot_dir.glob('*.txt')):
            format_chapter_file(input_file, input_file)
            total_files += 1
            if total_files % 100 == 0:
                print(f"  Processed {total_files} files...")
    
    # Process NT files
    if input_nt_dir.exists():
        for input_file in sorted(input_nt_dir.glob('*.txt')):
            # Skip 1_corinthians_1.txt and 1_corinthians_2.txt as they're already formatted
            if input_file.name in ['1_corinthians_1.txt', '1_corinthians_2.txt']:
                print(f"  Skipping {input_file.name} (already formatted)")
                total_files += 1
                continue
            
            format_chapter_file(input_file, input_file)
            total_files += 1
            if total_files % 100 == 0:
                print(f"  Processed {total_files} files...")
    
    print(f"\n✓ Formatted {total_files} chapter files")
    print(f"  Updated files in: raw/nkjv_crossrefs_ot/ and raw/nkjv_crossrefs_nt/")


if __name__ == '__main__':
    process_all_folders()
