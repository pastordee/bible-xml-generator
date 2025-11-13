#!/usr/bin/env python3
"""
Parse NKJV cross-references from formatted text file.
Each line format: "VERSE LETTER REFERENCES"
Example: "1 a Ps. 102:25; Is. 40:21; [John 1:1-3; Heb. 1:10]"
"""

import re
import os

# Book name to number mapping
BOOK_NUMBERS = {
    'genesis': '01', 'exodus': '02', 'leviticus': '03', 'numbers': '04', 'deuteronomy': '05',
    'joshua': '06', 'judges': '07', 'ruth': '08', '1 samuel': '09', '2 samuel': '10',
    '1 kings': '11', '2 kings': '12', '1 chronicles': '13', '2 chronicles': '14',
    'ezra': '15', 'nehemiah': '16', 'esther': '17', 'job': '18', 'psalms': '19',
    'proverbs': '20', 'ecclesiastes': '21', 'song of solomon': '22', 'isaiah': '23',
    'jeremiah': '24', 'lamentations': '25', 'ezekiel': '26', 'daniel': '27',
    'hosea': '28', 'joel': '29', 'amos': '30', 'obadiah': '31', 'jonah': '32',
    'micah': '33', 'nahum': '34', 'habakkuk': '35', 'zephaniah': '36', 'haggai': '37',
    'zechariah': '38', 'malachi': '39', 'matthew': '40', 'mark': '41', 'luke': '42',
    'john': '43', 'acts': '44', 'romans': '45', '1 corinthians': '46', '2 corinthians': '47',
    'galatians': '48', 'ephesians': '49', 'philippians': '50', 'colossians': '51',
    '1 thessalonians': '52', '2 thessalonians': '53', '1 timothy': '54', '2 timothy': '55',
    'titus': '56', 'philemon': '57', 'hebrews': '58', 'james': '59', '1 peter': '60',
    '2 peter': '61', '1 john': '62', '2 john': '63', '3 john': '64', 'jude': '65',
    'revelation': '66'
}


def parse_nkjv_crossrefs(file_path, book_name, chapter_num):
    """Parse NKJV cross-references from formatted text file."""
    
    crossrefs = []
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    lines = content.split('\n')
    
    # Skip header lines (Genesis, CHAPTER 1, blank lines)
    for line in lines:
        line = line.strip()
        
        # Skip empty lines and headers
        if not line or line.startswith('Genesis') or line.startswith('CHAPTER'):
            continue
        
        # Match pattern: "NUMBER LETTER REFERENCES"
        # Example: "1 a Ps. 102:25; Is. 40:21; [John 1:1-3; Heb. 1:10]"
        match = re.match(r'^(\d+)\s+([a-z])\s+(.+)$', line)
        
        if match:
            verse_num = match.group(1)
            letter = match.group(2)
            reference_text = match.group(3).strip()
            
            # Clean the reference text
            cleaned_ref = clean_reference(reference_text)
            
            if cleaned_ref and is_valid_reference(cleaned_ref):
                crossrefs.append({
                    'verse': verse_num,
                    'letter': letter,
                    'reference': cleaned_ref
                })
                print(f"✓ Verse {verse_num}:{letter} - {cleaned_ref[:60]}...")
            else:
                print(f"✗ Skipped verse {verse_num}:{letter} - invalid reference: {reference_text[:50]}")
    
    return crossrefs


def clean_reference(text):
    """Clean reference text by removing footnotes and extra whitespace."""
    # Remove trailing footnote numbers
    text = re.sub(r'\s+\d+\s*$', '', text)
    
    # Remove multiple spaces
    text = re.sub(r'\s+', ' ', text)
    
    return text.strip()


def is_valid_reference(text):
    """Check if text looks like a valid Bible reference."""
    # Must contain either a colon or period (for verse/chapter references)
    # and must contain a capital letter (for book names)
    return bool(re.search(r'[A-Z]', text)) and ((':' in text) or ('.' in text))


def convert_to_raw_format(crossrefs, book_name, chapter_num):
    """Convert parsed cross-references to raw format."""
    
    book_num = BOOK_NUMBERS.get(book_name.lower(), '01')
    chapter_str = str(chapter_num).zfill(3)
    
    output_lines = [f"C\tChapter {chapter_num}\n"]
    
    ref_counter = 1
    for ref in crossrefs:
        verse_num = ref['verse'].zfill(3)
        letter = ref['letter']
        verse_id = f"{book_num}{chapter_str}{verse_num}"
        ref_id = f"c{verse_id}.{ref_counter}"
        
        output_lines.append(f"V\t{verse_id}\n")
        output_lines.append(f"c\t{letter}\n")
        output_lines.append(f"i\t{ref_id}\n")
        output_lines.append(f"m\t{ref['reference']}\n")
        
        ref_counter += 1
    
    return ''.join(output_lines)


def main():
    # Configuration
    input_file = 'raw/cross_refs_nkjv/nkjv.txt'
    output_dir = 'raw/cross_refs_nkjv/genesis'
    book_name = 'genesis'
    chapter_num = 1
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"Parsing {input_file}...")
    print("=" * 70)
    
    # Parse cross-references
    crossrefs = parse_nkjv_crossrefs(input_file, book_name, chapter_num)
    
    print("=" * 70)
    print(f"\nTotal cross-references found: {len(crossrefs)}")
    
    # Convert to raw format
    raw_output = convert_to_raw_format(crossrefs, book_name, chapter_num)
    
    # Write output file
    output_file = os.path.join(output_dir, f"{chapter_num}.txt")
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(raw_output)
    
    print(f"\nOutput written to: {output_file}")
    print(f"Total lines: {len(raw_output.splitlines())}")
    
    # Show verse distribution
    verse_counts = {}
    for ref in crossrefs:
        verse = ref['verse']
        verse_counts[verse] = verse_counts.get(verse, 0) + 1
    
    print("\nReferences per verse:")
    for verse in sorted(verse_counts.keys(), key=int):
        print(f"  Verse {verse}: {verse_counts[verse]} reference(s)")


if __name__ == '__main__':
    main()
