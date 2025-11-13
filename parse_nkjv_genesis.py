#!/usr/bin/env python3
"""
Parse NKJV cross-references from the text file and convert to raw format.
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
    """Parse NKJV cross-references from text file."""
    
    text = Path(file_path).read_text(encoding='utf-8')
    
    crossrefs = defaultdict(list)
    
    # Normalize whitespace - replace newlines with spaces
    text = ' '.join(text.split())
    
    # Find all verse numbers and letter markers
    # Pattern for verse numbers: digit(s) followed by space and letter
    # Pattern for just letters: space + single letter + space (within a verse)
    
    crossref_positions = []
    
    # Find verse:letter combinations (e.g., "1 a ", "2 c ")
    verse_pattern = r'(\d+)\s+([a-z])\s+'
    for match in re.finditer(verse_pattern, text):
        verse_num = int(match.group(1))
        letter = match.group(2)
        crossref_positions.append((match.start(), match.end(), verse_num, letter))
    
    # Find standalone letters within verses (e.g., " b ", " f ")
    # These appear after references and before the next set of references
    letter_pattern = r'\s([a-z])\s+'
    for match in re.finditer(letter_pattern, text):
        letter = match.group(1)
        start_pos = match.start()
        
        # Find the verse this letter belongs to (look backward for verse number)
        verse_num = None
        for pos, end, vnum, vletter in crossref_positions:
            if pos < start_pos:
                verse_num = vnum
        
        if verse_num:
            # Only add if not already captured as verse:letter combo
            if not any(p[0] == match.start() for p in crossref_positions):
                crossref_positions.append((match.start(), match.end(), verse_num, letter))
    
    # Sort by position
    crossref_positions.sort()
    
    if not crossref_positions:
        print("No cross-references found!")
        return crossrefs
    
    # Extract references between positions
    for i, (start, end, verse_num, letter) in enumerate(crossref_positions):
        # Find end position (next match or end of text)
        if i + 1 < len(crossref_positions):
            ref_end = crossref_positions[i + 1][0]
        else:
            ref_end = len(text)
        
        # Extract reference text
        ref_text = text[end:ref_end].strip()
        
        # Clean up: remove footnote markers and commentary
        # Stop at common footnote markers
        for marker in [' 1 ', ' 2 ', ' 3 ', ' 4 ', ' 5 ', ' 6 ', ' 7 ', ' 8 ', ' 9 ']:
            if marker in ref_text:
                ref_text = ref_text[:ref_text.index(marker)]
        
        # Remove commentary phrases
        for phrase in ['Words in italic', 'Lit.', 'Syr.', 'expanse', 'luminaries', 'souls', 'wild animals']:
            if phrase in ref_text:
                ref_text = ref_text[:ref_text.index(phrase)]
        
        # Clean up whitespace
        ref_text = re.sub(r'\s+', ' ', ref_text).strip()
        
        # Skip if too short or looks wrong
        if len(ref_text) < 3 or len(ref_text) > 200:
            continue
        
        # Must contain book references (has dots or colons)
        if ':' in ref_text or '.' in ref_text:
            crossrefs[verse_num].append((letter, ref_text))
    
    return crossrefs

def convert_to_raw_format(crossrefs, book_name='genesis', chapter_num=1):
    """Convert parsed cross-references to raw format."""
    
    book_num = BOOK_NUMBERS[book_name]
    lines = []
    
    lines.append(f"C Chapter {chapter_num}")
    
    for verse_num in sorted(crossrefs.keys()):
        verse_id = f"{book_num}{chapter_num:03d}{verse_num:03d}"
        lines.append(f"V {verse_id}")
        
        letter_data = sorted(crossrefs[verse_num], key=lambda x: x[0])
        
        for seq, (letter, ref_text) in enumerate(letter_data, 1):
            lines.append(f"c {letter}")
            lines.append(f"i c{verse_id}.{seq}")
            lines.append(f"m {ref_text}")
    
    return '\n'.join(lines) + '\n'

def main():
    print("Parsing NKJV Genesis 1...")
    print("=" * 80)
    
    input_file = 'raw/cross_refs_nkjv/nkjv.txt'
    
    # Parse the cross-references
    crossrefs = parse_nkjv_crossrefs(input_file, 'genesis', 1)
    
    print(f"Found cross-references for {len(crossrefs)} verses")
    
    # Show what was found
    total_refs = sum(len(refs) for refs in crossrefs.values())
    print(f"Total cross-reference letters: {total_refs}")
    print()
    
    # Show first few
    print("Sample cross-references found:")
    for verse in sorted(list(crossrefs.keys())[:5]):
        for letter, refs in crossrefs[verse]:
            print(f"  {verse}:{letter} - {refs[:80]}{'...' if len(refs) > 80 else ''}")
    
    print()
    
    # Convert to raw format
    raw_text = convert_to_raw_format(crossrefs, 'genesis', 1)
    
    # Save to file
    output_dir = Path('raw/cross_refs_nkjv/genesis')
    output_dir.mkdir(parents=True, exist_ok=True)
    
    output_file = output_dir / '1.txt'
    output_file.write_text(raw_text, encoding='utf-8')
    
    print(f"✓ Created: {output_file}")
    print(f"  {len(raw_text.split(chr(10)))} lines")
    
    # Display the output
    print()
    print("Output preview:")
    print("-" * 80)
    print('\n'.join(raw_text.split('\n')[:30]))
    print("...")

if __name__ == '__main__':
    main()
