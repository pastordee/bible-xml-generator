#!/usr/bin/env python3
"""
Format NKJV chapter files to match the clean manual format.
Simple approach: ensure verses, footnotes, and cross-references are properly line-separated.
"""

import re
from pathlib import Path


def format_chapter_file(input_file):
    """Format a chapter file in-place"""
    
    with open(input_file, 'r') as f:
        content = f.read().strip()
    
    # Split into three sections FIRST before any formatting
    footnotes_match = re.search(r'\bFootnotes\b', content)
    crossrefs_match = re.search(r'\bCross references\b', content)
    
    if footnotes_match and crossrefs_match:
        verses_text = content[:footnotes_match.start()].strip()
        footnotes_text = content[footnotes_match.end():crossrefs_match.start()].strip()
        crossrefs_text = content[crossrefs_match.end():].strip()
    elif footnotes_match:
        verses_text = content[:footnotes_match.start()].strip()
        footnotes_text = content[footnotes_match.end():].strip()
        crossrefs_text = ""
    elif crossrefs_match:
        verses_text = content[:crossrefs_match.start()].strip()
        footnotes_text = ""
        crossrefs_text = content[crossrefs_match.end():].strip()
    else:
        verses_text = content
        footnotes_text = ""
        crossrefs_text = ""
    
    # Format ONLY the verses section
    formatted_verses = format_verses_simple(verses_text)
    
    # Format footnotes and cross references
    formatted_footnotes = format_references_simple(footnotes_text)
    formatted_crossrefs = format_crossrefs_with_letters(crossrefs_text, verses_text)
    
    # Build output
    output = formatted_verses + '\n\n\nFootnotes \n' + formatted_footnotes + '\n\nCross references \n' + formatted_crossrefs
    
    # Write back
    with open(input_file, 'w', encoding='utf-8') as f:
        f.write(output)


def format_verses_simple(text):
    """Put each verse on its own line, handling section headings"""
    if not text:
        return ""
    
    # Insert newline before each verse number (pattern: space + digit + space)
    # But preserve section headings
    result = text
    
    # Add newline before verse numbers, but handle first verse specially
    result = re.sub(r'\s+(\d+)\s+', r'\n\1 ', result)
    
    # Clean up: remove multiple consecutive newlines, strip
    result = re.sub(r'\n\n+', '\n', result)
    result = result.strip()
    
    return result


def get_verse_letters(verses_text, verse_num):
    """Extract the crossref letters that appear in a specific verse"""
    # Find the verse in the text
    verse_pattern = rf'\b{verse_num}\s+.*?(?=\n\d+\s+|\n\n|$)'
    verse_match = re.search(verse_pattern, verses_text, re.DOTALL)
    
    if not verse_match:
        return []
    
    verse_content = verse_match.group(0)
    
    # Find crossref letter markers - these are 1-2 lowercase letters that stand alone
    # Use word boundary \b to ensure they're not part of a longer word
    # Pattern: word boundary + 1-2 lowercase letters + space
    letter_groups = re.findall(r'\b([a-z]{1,2})\s', verse_content)
    
    # Filter out common English words to avoid false matches
    common_words = {'a', 'i', 'am', 'an', 'as', 'at', 'be', 'by', 'do', 'go', 'he', 'if', 'in', 'is', 'it', 'me', 'my', 'no', 'of', 'on', 'or', 'so', 'to', 'up', 'us', 'we'}
    letter_groups = [g for g in letter_groups if g not in common_words]
    
    # For two-letter markers (like ab, ac, ad), we only want the second letter
    # Single letters stay as-is
    letters = []
    for group in letter_groups:
        if len(group) == 2:
            letters.append(group[1])  # Take only the second letter
        else:
            letters.append(group)  # Keep single letters as-is
    
    return letters


def format_crossrefs_with_letters(text, verses_text):
    """Format cross references with verse number and lettered references matching verse text"""
    if not text:
        return ""
    
    # Check if already in "Verse X:" format
    if re.search(r'^Verse \d+:', text.strip(), re.MULTILINE):
        # Already formatted - need to reformat with correct letters
        return reformat_existing_crossrefs(text, verses_text)
    
    # Pattern to match verse references
    verse_ref_pattern = r'((?:\d\s+)?[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s+(\d+):(\d+)'
    
    # Find the FIRST match to determine the book name
    first_match = re.search(verse_ref_pattern, text)
    if not first_match:
        return text
    
    # Get the book name and chapter from first match
    book_name = first_match.group(1)
    chapter_num = first_match.group(2)
    
    # Pattern that ONLY matches this book and chapter
    specific_pattern = re.escape(book_name) + r'\s+' + re.escape(chapter_num) + r':(\d+)\s*:\s*'
    
    # Find all matches for this specific book/chapter
    matches = list(re.finditer(specific_pattern, text))
    
    if not matches:
        return text
    
    result_lines = []
    current_verse_num = None
    verse_refs = []
    
    for i, match in enumerate(matches):
        verse_num = match.group(1)
        
        # Is this a different verse number?
        if current_verse_num and verse_num != current_verse_num:
            # Format the previous verse with letters from the verse text
            if verse_refs:
                letters = get_verse_letters(verses_text, current_verse_num)
                formatted = format_verse_refs_with_actual_letters(current_verse_num, verse_refs, letters)
                result_lines.append(formatted)
            
            # Start new verse
            current_verse_num = verse_num
            verse_refs = []
            
            # Get content after this match until next match or end
            if i + 1 < len(matches):
                content = text[match.end():matches[i+1].start()].strip()
            else:
                content = text[match.end():].strip()
            verse_refs.append(content)
            
        elif not current_verse_num:
            # First verse
            current_verse_num = verse_num
            
            # Get content after this match until next match or end
            if i + 1 < len(matches):
                content = text[match.end():matches[i+1].start()].strip()
            else:
                content = text[match.end():].strip()
            verse_refs.append(content)
        else:
            # Same verse - add another reference
            if i + 1 < len(matches):
                content = text[match.end():matches[i+1].start()].strip()
            else:
                content = text[match.end():].strip()
            verse_refs.append(content)
    
    # Format the last verse
    if current_verse_num and verse_refs:
        letters = get_verse_letters(verses_text, current_verse_num)
        formatted = format_verse_refs_with_actual_letters(current_verse_num, verse_refs, letters)
        result_lines.append(formatted)
    
    return '\n'.join(result_lines) if result_lines else text


def reformat_existing_crossrefs(text, verses_text):
    """Reformat already-formatted crossrefs to use correct letters from verse text"""
    result_lines = []
    
    # Split by "Verse X:" pattern
    verse_blocks = re.split(r'(Verse \d+:)', text)
    
    current_verse_num = None
    current_refs = []
    
    for block in verse_blocks:
        block = block.strip()
        if not block:
            continue
            
        # Check if this is a verse header
        verse_match = re.match(r'Verse (\d+):', block)
        if verse_match:
            # Save previous verse if any
            if current_verse_num and current_refs:
                letters = get_verse_letters(verses_text, current_verse_num)
                formatted = format_verse_refs_with_actual_letters(current_verse_num, current_refs, letters)
                result_lines.append(formatted)
            
            # Start new verse
            current_verse_num = verse_match.group(1)
            current_refs = []
        else:
            # This is the content after "Verse X:"
            # Extract references (lines starting with letter:)
            ref_lines = re.findall(r'[a-z]:\s*(.+)', block)
            current_refs.extend(ref_lines)
    
    # Save last verse
    if current_verse_num and current_refs:
        letters = get_verse_letters(verses_text, current_verse_num)
        formatted = format_verse_refs_with_actual_letters(current_verse_num, current_refs, letters)
        result_lines.append(formatted)
    
    return '\n'.join(result_lines) if result_lines else text


def format_verse_refs_with_actual_letters(verse_num, refs, letters):
    """Format a single verse's references with the actual letters from the verse text"""
    lines = [f"Verse {verse_num}:"]
    
    # If we have letters from the verse, use them
    if letters:
        for i, ref in enumerate(refs):
            if ref and i < len(letters):
                lines.append(f"  {letters[i]}: {ref}")
    else:
        # Fallback to a, b, c if no letters found
        for i, ref in enumerate(refs):
            if ref:
                letter = chr(ord('a') + i)
                lines.append(f"  {letter}: {ref}")
    
    return '\n'.join(lines)


def format_references_simple(text):
    """Separate references by verse - each verse's references on its own line"""
    if not text:
        return ""
    
    # Pattern to match verse references
    # Must have optional number, book name (1-2 words), space, chapter:verse
    verse_ref_pattern = r'((?:\d\s+)?[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s+(\d+):(\d+)'
    
    # Find the FIRST match to determine the book name
    first_match = re.search(verse_ref_pattern, text)
    if not first_match:
        return text
    
    # Get the book name and chapter from first match
    book_name = first_match.group(1)
    chapter_num = first_match.group(2)
    
    # Now create a more specific pattern that ONLY matches this book and chapter
    # This prevents matching reference targets like "Acts 18:4"
    specific_pattern = re.escape(book_name) + r'\s+' + re.escape(chapter_num) + r':(\d+)'
    
    # Find all matches for this specific book/chapter
    matches = list(re.finditer(specific_pattern, text))
    
    if not matches:
        return text
    
    result_lines = []
    current_verse_num = None
    current_start = 0
    
    for i, match in enumerate(matches):
        verse_num = match.group(1)  # Just the verse number
        
        # Is this a different verse number than the current one?
        if current_verse_num and verse_num != current_verse_num:
            # Save the previous verse's content
            end_pos = match.start()
            content = text[current_start:end_pos].strip()
            result_lines.append(content)
            
            # Start new verse
            current_verse_num = verse_num
            current_start = match.start()
        elif not current_verse_num:
            # First verse
            current_verse_num = verse_num
            current_start = match.start()
        # else: same verse number, continue accumulating
    
    # Add the last verse
    if current_verse_num:
        content = text[current_start:].strip()
        result_lines.append(content)
    
    return '\n'.join(result_lines) if result_lines else text


def process_all_folders():
    """Process all files in nkjv_crossrefs_* folders"""
    
    input_ot_dir = Path('raw/nkjv_crossrefs_ot')
    input_nt_dir = Path('raw/nkjv_crossrefs_nt')
    
    total_files = 0
    
    print("Formatting NKJV chapter files...")
    print()
    
    # Process OT files
    if input_ot_dir.exists():
        for input_file in sorted(input_ot_dir.glob('*.txt')):
            format_chapter_file(input_file)
            total_files += 1
            if total_files % 100 == 0:
                print(f"  Processed {total_files} files...")
    
    # Process NT files
    if input_nt_dir.exists():
        for input_file in sorted(input_nt_dir.glob('*.txt')):
            # Skip already formatted files
            if input_file.name in ['1_corinthians_1.txt', '1_corinthians_2.txt']:
                print(f"  Skipping {input_file.name} (already formatted)")
                total_files += 1
                continue
            
            format_chapter_file(input_file)
            total_files += 1
            if total_files % 100 == 0:
                print(f"  Processed {total_files} files...")
    
    print(f"\n✓ Formatted {total_files} chapter files in place")


if __name__ == '__main__':
    process_all_folders()
