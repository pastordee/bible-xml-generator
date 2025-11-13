#!/usr/bin/env python3
"""
Parse NKJV cross-references from the text file and convert to raw format.
Version 2 - Better handling of the actual format.
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
    
    content = Path(file_path).read_text(encoding='utf-8')
    lines = content.split('\n')
    
    crossrefs = defaultdict(list)
    current_verse = None
    current_letter = None
    current_ref = []
    
    # Commentary/footnote markers to skip
    skip_phrases = [
        'Words in italic', 'Lit.', 'Syr.', 'expanse', 'luminaries', 'souls',
        'wild animals', 'moves about', 'living soul', 'type have been added',
        'not found in', 'original Hebrew', 'evening was', 'a day, one'
    ]
    
    for line in lines:
        line = line.strip()
        if not line or line == 'Genesis' or line == 'CHAPTER 1':
            continue
        
        # Try to find all verse:letter combinations in this line
        # Pattern: verse_number space letter space (at start or after another verse)
        parts = re.split(r'(?=\d+\s+[a-z]\s+)', line)
        
        for part in parts:
            if not part.strip():
                continue
            
            part = part.strip()
            
            # Check if part starts with verse number
            verse_match = re.match(r'^(\d+)\s+([a-z])\s+(.+)$', part)
            if verse_match:
                # Save previous reference if any
                if current_verse and current_letter and current_ref:
                    ref_text = ' '.join(current_ref).strip()
                    if is_valid_reference(ref_text, skip_phrases):
                        crossrefs[current_verse].append((current_letter, ref_text))
                
                current_verse = int(verse_match.group(1))
                current_letter = verse_match.group(2)
                current_ref = [verse_match.group(3)]
            else:
                # Check if it's a letter within current verse
                letter_match = re.match(r'^([a-z])\s+(.+)$', part)
                if letter_match:
                    # Save previous reference
                    if current_verse and current_letter and current_ref:
                        ref_text = ' '.join(current_ref).strip()
                        if is_valid_reference(ref_text, skip_phrases):
                            crossrefs[current_verse].append((current_letter, ref_text))
                    
                    # Start new reference with same verse
                    current_letter = letter_match.group(1)
                    current_ref = [letter_match.group(2)]
                elif current_letter:
                    # Continuation of current reference
                    current_ref.append(part)
    
    # Save last reference
    if current_verse and current_letter and current_ref:
        ref_text = ' '.join(current_ref).strip()
        if is_valid_reference(ref_text, skip_phrases):
            crossrefs[current_verse].append((current_letter, ref_text))
    
    return crossrefs

def is_valid_reference(text, skip_phrases):
    """Check if text looks like a valid biblical reference."""
    
    # Remove footnote numbers
    text_clean = re.sub(r'\s+\d+\s+', ' ', text)
    
    # Skip if contains commentary phrases
    for phrase in skip_phrases:
        if phrase in text:
            return False
    
    # Must contain biblical reference markers
    if not (':' in text or '.' in text):
        return False
    
    # Must not be too short or too long
    if len(text_clean) < 5 or len(text_clean) > 300:
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
            # Clean up reference text
            ref_text = clean_reference(ref_text)
            
            lines.append(f"c {letter}")
            lines.append(f"i c{verse_id}.{seq}")
            lines.append(f"m {ref_text}")
    
    return '\n'.join(lines)

def clean_reference(text):
    """Clean up reference text."""
    
    # Remove footnote numbers (single digits surrounded by spaces)
    text = re.sub(r'\s+\d+\s+', ' ', text)
    
    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    
    # Remove trailing punctuation that's not part of references
    text = text.rstrip(',;')
    
    return text

def main():
    input_file = Path('raw/cross_refs_nkjv/nkjv.txt')
    output_dir = Path('raw/cross_refs_nkjv/genesis')
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print("Parsing NKJV Genesis 1...")
    print("=" * 80)
    
    crossrefs = parse_nkjv_crossrefs(input_file, 'genesis', 1)
    
    print(f"Found cross-references for {len(crossrefs)} verses")
    total_refs = sum(len(refs) for refs in crossrefs.values())
    print(f"Total cross-reference letters: {total_refs}")
    print()
    
    if crossrefs:
        print("Sample cross-references found:")
        count = 0
        for verse_num in sorted(crossrefs.keys()):
            for letter, ref_text in crossrefs[verse_num]:
                if count < 10:
                    preview = ref_text[:80] + '...' if len(ref_text) > 80 else ref_text
                    print(f"  {verse_num}:{letter} - {preview}")
                    count += 1
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
    preview_lines = raw_output.splitlines()[:30]
    for line in preview_lines:
        print(line)
    if len(raw_output.splitlines()) > 30:
        print("...")

if __name__ == '__main__':
    main()
