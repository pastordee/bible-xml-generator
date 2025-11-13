#!/usr/bin/env python3
"""
Semi-automatic formatter for NKJV cross-references.
This tool helps clean up pasted PDF text and format it properly.

Usage:
1. Copy cross-reference text from PDF
2. Paste it into a file (e.g., raw_paste.txt)
3. Run: python3 format_crossrefs.py raw_paste.txt
4. Review and edit the output
"""

import re
import sys

def clean_and_format(text):
    """Clean and format pasted cross-reference text."""
    
    lines = text.split('\n')
    formatted = []
    
    current_verse = None
    current_letter = None
    current_ref = []
    
    for line in lines:
        line = line.strip()
        
        # Skip empty lines
        if not line:
            continue
        
        # Skip obvious commentary lines
        if any(keyword in line.lower() for keyword in [
            'words in italic', 'lit.', 'literally', 'hebrew', 'aramaic',
            'or tigris', 'expanse', 'luminaries', 'souls', 'living soul',
            'moves about on', 'syr. all', 'evening was', 'morning was'
        ]):
            continue
        
        # Skip if it starts with a chapter marker
        if line.startswith('CHAPTER'):
            continue
        
        # Check if this is a new verse:letter reference
        # Pattern: "1 a Ps. 102:25..." or "2 b Ex. 20:9..."
        match = re.match(r'^(\d+)\s+([a-z])\s+(.+)$', line)
        
        if match:
            verse_num = match.group(1)
            letter = match.group(2)
            ref_text = match.group(3).strip()
            
            # Check if this looks like a Bible reference (has book abbreviation + chapter:verse)
            # A valid cross-ref should have a book name pattern followed by numbers
            has_book_ref = re.search(r'[A-Z][a-z]+\.?\s+\d+', ref_text) or re.search(r'\d+\s+[A-Z]', ref_text)
            
            if has_book_ref:
                # Save previous reference if exists
                if current_verse and current_letter and current_ref:
                    final_ref = ' '.join(current_ref)
                    final_ref = clean_reference(final_ref)
                    if final_ref:
                        formatted.append(f"{current_verse} {current_letter} {final_ref}\n")
                
                # Check if there's another verse:letter pattern embedded in this line
                # Example: "1 a Ps. 102:25; b Gen. 2:4;"
                remaining = ref_text
                embedded_pattern = r'\s+([a-z])\s+([A-Z][a-z]+\.?\s+\d+)'
                embedded_match = re.search(embedded_pattern, remaining)
                
                if embedded_match:
                    # Split at the embedded marker
                    pos = embedded_match.start()
                    first_ref = remaining[:pos].strip()
                    
                    # Start new reference with the first part
                    current_verse = verse_num
                    current_letter = letter
                    current_ref = [first_ref]
                    
                    # Save it immediately
                    final_ref = clean_reference(first_ref)
                    if final_ref:
                        formatted.append(f"{current_verse} {current_letter} {final_ref}\n")
                    
                    # Start the embedded reference
                    current_verse = verse_num
                    current_letter = embedded_match.group(1)
                    current_ref = [embedded_match.group(2) + remaining[embedded_match.end():]]
                else:
                    # No embedded pattern, just start new reference
                    current_verse = verse_num
                    current_letter = letter
                    current_ref = [ref_text]
            else:
                # This looks like Bible text, not a cross-reference
                continue
        
        else:
            # This might be a continuation of the previous reference
            # OR it could be a new letter for the same verse
            
            # Check if this is just a letter followed by a reference (same verse, new letter)
            # Pattern: "b Gen. 2:16" (no verse number)
            new_letter_match = re.match(r'^([a-z])\s+([A-Z][a-z]+\.?\s+\d+.*)$', line)
            
            if new_letter_match and current_verse:
                # This is a new letter for the current verse
                # Save previous reference first
                if current_letter and current_ref:
                    final_ref = ' '.join(current_ref)
                    final_ref = clean_reference(final_ref)
                    if final_ref:
                        formatted.append(f"{current_verse} {current_letter} {final_ref}\n")
                
                # Start new reference with same verse number
                current_letter = new_letter_match.group(1)
                current_ref = [new_letter_match.group(2)]
            
            elif current_ref:
                # This is a continuation line
                # Only add it if we're currently building a reference AND it contains biblical reference patterns
                has_ref_pattern = (
                    re.search(r'[A-Z][a-z]+\.?\s+\d+', line) or  # "Gen. 1" or "Ps 23"
                    re.search(r'\d+:\d+', line) or  # "1:1"
                    re.search(r'^\d+,', line) or  # Starts with verse number
                    re.search(r'[;\[\]]', line)  # Has reference separators
                )
                
                if has_ref_pattern:
                    current_ref.append(line)
    
    # Don't forget the last reference
    if current_verse and current_letter and current_ref:
        final_ref = ' '.join(current_ref)
        final_ref = clean_reference(final_ref)
        if final_ref:
            formatted.append(f"{current_verse} {current_letter} {final_ref}\n")
    
    return formatted


def clean_reference(text):
    """Clean up a reference text."""
    
    # Remove footnote markers (numbers at specific positions)
    # Pattern: space + single digit + space + explanation word
    text = re.sub(r'\s+\d+\s+(Heb\.|Lit\.|Or|Syr\.|M-Text|NU-Text|LXX|Sam\.).*$', '', text, flags=re.IGNORECASE)
    
    # Remove trailing single digits that are footnote numbers
    text = re.sub(r'\s+\d+\s*$', '', text)
    
    # Remove specific footnote patterns
    text = re.sub(r'\s+\d+\s+(Lit\.|Or|Heb\.)[^.]*\.', '', text)
    
    # Fix common OCR/PDF issues
    text = text.replace('  ', ' ')
    text = text.replace(' ,', ',')
    text = text.replace(' ;', ';')
    text = text.replace(' .', '.')
    
    # Remove page breaks or weird characters
    text = re.sub(r'[^\x20-\x7E\[\];:,.\-–—]', '', text)
    
    # Clean up extra spaces
    text = re.sub(r'\s+', ' ', text)
    
    return text.strip()


def format_chapter(formatted_refs, chapter_num):
    """Format the cleaned references with chapter header."""
    
    output = [f"CHAPTER {chapter_num}\n\n"]
    
    # Group by verse
    verse_groups = {}
    for ref in formatted_refs:
        parts = ref.split(None, 2)  # Split into verse, letter, reference
        if len(parts) >= 3:
            verse = parts[0]
            if verse not in verse_groups:
                verse_groups[verse] = []
            verse_groups[verse].append(ref)
    
    # Output in order
    for verse in sorted(verse_groups.keys(), key=int):
        for ref in verse_groups[verse]:
            output.append(ref)
        output.append('\n')
    
    return ''.join(output)


def interactive_mode():
    """Interactive mode to format pasted text."""
    
    print("=" * 70)
    print("NKJV Cross-Reference Formatter")
    print("=" * 70)
    print()
    print("Instructions:")
    print("1. Paste your cross-reference text below")
    print("2. Press Ctrl+D (Mac/Linux) or Ctrl+Z+Enter (Windows) when done")
    print("3. Enter chapter number when prompted")
    print()
    print("Paste text now:")
    print("-" * 70)
    
    # Read multiline input
    lines = []
    try:
        while True:
            line = input()
            lines.append(line)
    except EOFError:
        pass
    
    text = '\n'.join(lines)
    
    if not text.strip():
        print("\nNo text provided!")
        return
    
    print("\n" + "=" * 70)
    print("Processing...")
    
    # Clean and format
    formatted_refs = clean_and_format(text)
    
    if not formatted_refs:
        print("\nNo valid cross-references found!")
        print("Make sure your text is in the format: '1 a Ps. 102:25...'")
        return
    
    # Get chapter number
    print(f"\nFound {len(formatted_refs)} cross-references")
    chapter = input("Enter chapter number: ").strip()
    
    if not chapter.isdigit():
        print("Invalid chapter number!")
        return
    
    # Format output
    output = format_chapter(formatted_refs, chapter)
    
    # Display result
    print("\n" + "=" * 70)
    print("FORMATTED OUTPUT:")
    print("=" * 70)
    print(output)
    
    # Save option
    save = input("\nSave to file? (y/n): ").strip().lower()
    if save == 'y':
        book = input("Enter book name (e.g., genesis): ").strip().lower()
        filename = f"raw/cross_refs_nkjv/{book}_ch{chapter}_formatted.txt"
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(output)
        
        print(f"\nSaved to: {filename}")
        print("Review the output and copy to your main nkjv.txt file when ready!")


def file_mode(input_file):
    """Process a file containing pasted text."""
    
    print(f"Reading from: {input_file}")
    
    with open(input_file, 'r', encoding='utf-8') as f:
        text = f.read()
    
    # Clean and format
    formatted_refs = clean_and_format(text)
    
    if not formatted_refs:
        print("No valid cross-references found!")
        return
    
    print(f"Found {len(formatted_refs)} cross-references")
    
    # Get chapter number
    chapter = input("Enter chapter number: ").strip()
    
    if not chapter.isdigit():
        print("Invalid chapter number!")
        return
    
    # Format output
    output = format_chapter(formatted_refs, chapter)
    
    # Save to output file
    output_file = input_file.replace('.txt', '_formatted.txt')
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(output)
    
    print(f"\nFormatted output saved to: {output_file}")
    print(f"Total cross-references: {len(formatted_refs)}")
    
    # Show preview
    print("\n" + "=" * 70)
    print("PREVIEW (first 10 lines):")
    print("=" * 70)
    for line in output.split('\n')[:10]:
        print(line)


def main():
    print("NKJV Cross-Reference Formatter")
    print("=" * 70)
    
    if len(sys.argv) > 1:
        # File mode
        input_file = sys.argv[1]
        file_mode(input_file)
    else:
        # Interactive mode
        interactive_mode()


if __name__ == '__main__':
    main()
