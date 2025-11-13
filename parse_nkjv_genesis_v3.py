#!/usr/bin/env python3
"""
Parse NKJV cross-references - Version 3
Uses position-based extraction to handle complex inline formatting.
"""

import re
from pathlib import Path
from collections import defaultdict

BOOK_NUMBERS = {
    'genesis': '01', 'exodus': '02', 'leviticus': '03', 'numbers': '04',
    'deuteronomy': '05', 'joshua': '06', 'judges': '07', 'ruth': '08',
    '1_samuel': '09', '2_samuel': '10', '1_kings': '11', '2_kings': '12',
    '1_chronicles': '13', '2_chronicles': '14', 'ezra': '15', 'nehemiah': '16',
    'esther': '17', 'job': '18', 'psalms': '19', 'proverbs': '20',
    'ecclesiastes': '21', 'song_of_solomon': '22', 'isaiah': '23',
    'jeremiah': '24', 'lamentations': '25', 'ezekiel': '26', 'daniel': '27',
    'hosea': '28', 'joel': '29', 'amos': '30', 'obadiah': '31', 'jonah': '32',
    'micah': '33', 'nahum': '34', 'habakkuk': '35', 'zephaniah': '36',
    'haggai': '37', 'zechariah': '38', 'malachi': '39',
    'matthew': '40', 'mark': '41', 'luke': '42', 'john': '43', 'acts': '44',
    'romans': '45', '1_corinthians': '46', '2_corinthians': '47',
    'galatians': '48', 'ephesians': '49', 'philippians': '50',
    'colossians': '51', '1_thessalonians': '52', '2_thessalonians': '53',
    '1_timothy': '54', '2_timothy': '55', 'titus': '56', 'philemon': '57',
    'hebrews': '58', 'james': '59', '1_peter': '60', '2_peter': '61',
    '1_john': '62', '2_john': '63', '3_john': '64', 'jude': '65',
    'revelation': '66'
}

def parse_nkjv_crossrefs(file_path, book_name='genesis', chapter_num=1):
    """Parse NKJV cross-references using position-based extraction."""
    
    content = Path(file_path).read_text(encoding='utf-8')
    
    # Remove header lines
    lines = [l for l in content.split('\n') if l.strip() and l.strip() not in ['Genesis', 'CHAPTER 1']]
    text = '\n'.join(lines)
    
    crossrefs = defaultdict(list)
    
    # Find all verse:letter positions
    # Pattern: number followed by space and lowercase letter
    # Use word boundary or start of line to avoid matching inside references like "4:23"
    pattern = r'(?:^|\s)(\d+)\s+([a-z])\s+'
    matches = list(re.finditer(pattern, text, re.MULTILINE))
    
    print(f"Found {len(matches)} verse:letter markers")
    
    # Extract text between each marker
    for i, match in enumerate(matches):
        verse_num = int(match.group(1))
        letter = match.group(2)
        start_pos = match.end()
        
        # Find end position (next marker or end of text)
        if i + 1 < len(matches):
            end_pos = matches[i + 1].start()
        else:
            end_pos = len(text)
        
        # Extract reference text
        ref_text = text[start_pos:end_pos].strip()
        
        # Look for inline letter markers within this text (e.g., " b Gen. ", " d [Gen. ")
        # Split on pattern: space + single letter + space + (capital letter OR bracket)
        inline_pattern = r'\s+([a-z])\s+([A-Z\[])'
        inline_matches = list(re.finditer(inline_pattern, ref_text))
        
        if inline_matches:
            # Split the reference text at each inline letter marker
            current_pos = 0
            for inline_match in inline_matches:
                # Text before this inline marker belongs to current letter
                text_chunk = ref_text[current_pos:inline_match.start()].strip()
                if text_chunk:
                    text_chunk = clean_reference(text_chunk)
                    if is_valid_reference(text_chunk):
                        crossrefs[verse_num].append((letter, text_chunk))
                        print(f"  {verse_num}:{letter} - {text_chunk[:60]}...")
                
                # Update letter and position for next chunk
                letter = inline_match.group(1)
                current_pos = inline_match.start() + 1  # Skip the space before letter
            
            # Handle remaining text after last inline marker
            remaining_text = ref_text[current_pos:].strip()
            # Remove the letter marker itself from the start
            remaining_text = re.sub(r'^[a-z]\s+', '', remaining_text)
            if remaining_text:
                remaining_text = clean_reference(remaining_text)
                if is_valid_reference(remaining_text):
                    crossrefs[verse_num].append((letter, remaining_text))
                    print(f"  {verse_num}:{letter} - {remaining_text[:60]}...")
        else:
            # No inline markers, process as single reference
            ref_text = clean_reference(ref_text)
            if is_valid_reference(ref_text):
                crossrefs[verse_num].append((letter, ref_text))
                print(f"  {verse_num}:{letter} - {ref_text[:60]}...")
    
    return crossrefs

def clean_reference(text):
    """Clean up reference text."""
    
    # Remove footnote numbers at the end (like "1" or "2")
    text = re.sub(r'\s+\d+\s*$', '', text)
    
    # Remove commentary phrases
    skip_patterns = [
        r'Words in italic.*',
        r'Lit\..*',
        r'Syr\..*',
        r'original Hebrew.*',
        r'evening was.*',
        r'moves about.*',
        r'living soul.*',
        r'wild animals.*',
    ]
    
    for pattern in skip_patterns:
        text = re.sub(pattern, '', text, flags=re.IGNORECASE)
    
    # Remove single-word commentary that appears alone
    if text.lower() in ['expanse', 'luminaries', 'souls']:
        return ''
    
    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    text = text.strip(',;')
    
    return text

def is_valid_reference(text):
    """Check if text looks like a valid biblical reference."""
    
    if not text or len(text) < 5:
        return False
    
    if len(text) > 300:
        return False
    
    # Must contain biblical reference markers
    if not (':' in text or '.' in text):
        return False
    
    # Should contain at least one capital letter (book names)
    if not re.search(r'[A-Z]', text):
        return False
    
    return True

def convert_to_raw_format(crossrefs, book_name='genesis', chapter_num=1):
    """Convert parsed cross-references to raw format."""
    
    book_num = BOOK_NUMBERS[book_name]
    lines = []
    
    lines.append(f"C Chapter {chapter_num}")
    
    for verse_num in sorted(crossrefs.keys()):
        verse_id = f"{book_num}{chapter_num:03d}{verse_num:03d}"
        lines.append(f"V {verse_id}")
        
        for seq, (letter, ref_text) in enumerate(crossrefs[verse_num], 1):
            lines.append(f"c {letter}")
            lines.append(f"i c{verse_id}.{seq}")
            lines.append(f"m {ref_text}")
    
    return '\n'.join(lines)

def main():
    input_file = Path('raw/cross_refs_nkjv/nkjv.txt')
    output_dir = Path('raw/cross_refs_nkjv/genesis')
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print("Parsing NKJV Genesis 1...")
    print("=" * 80)
    
    crossrefs = parse_nkjv_crossrefs(input_file, 'genesis', 1)
    
    print()
    print(f"Found cross-references for {len(crossrefs)} verses")
    total_refs = sum(len(refs) for refs in crossrefs.values())
    print(f"Total cross-reference letters: {total_refs}")
    print()
    
    # Convert to raw format
    raw_output = convert_to_raw_format(crossrefs, 'genesis', 1)
    
    # Write output
    output_file = output_dir / '1.txt'
    output_file.write_text(raw_output, encoding='utf-8')
    
    print(f"✓ Created: {output_file}")
    print(f"  {len(raw_output.splitlines())} lines")
    print()
    print("Output preview:")
    print("-" * 80)
    preview_lines = raw_output.splitlines()[:40]
    for line in preview_lines:
        print(line)
    if len(raw_output.splitlines()) > 40:
        print("...")

if __name__ == '__main__':
    main()
