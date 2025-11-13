#!/usr/bin/env python3
"""
Batch parse all 1,189 NKJV cross-reference files and convert to C/V/c/i/m format.
Processes all formatted files from raw/cross_refs_nkjv/raw_formatted/ directory.
Appends results to raw/cross_refs_nkjv/nkjv.txt master file.
"""

import re
import os
from pathlib import Path
from collections import defaultdict

# Book name to number mapping
BOOK_NUMBERS = {
    'genesis': '01', 'exodus': '02', 'leviticus': '03', 'numbers': '04', 'deuteronomy': '05',
    'joshua': '06', 'judges': '07', 'ruth': '08', '1samuel': '09', '2samuel': '10',
    '1kings': '11', '2kings': '12', '1chronicles': '13', '2chronicles': '14',
    'ezra': '15', 'nehemiah': '16', 'esther': '17', 'job': '18', 'psalms': '19',
    'proverbs': '20', 'ecclesiastes': '21', 'songofsolomon': '22', 'isaiah': '23',
    'jeremiah': '24', 'lamentations': '25', 'ezekiel': '26', 'daniel': '27',
    'hosea': '28', 'joel': '29', 'amos': '30', 'obadiah': '31', 'jonah': '32',
    'micah': '33', 'nahum': '34', 'habakkuk': '35', 'zephaniah': '36', 'haggai': '37',
    'zechariah': '38', 'malachi': '39', 'matthew': '40', 'mark': '41', 'luke': '42',
    'john': '43', 'acts': '44', 'romans': '45', '1corinthians': '46', '2corinthians': '47',
    'galatians': '48', 'ephesians': '49', 'philippians': '50', 'colossians': '51',
    '1thessalonians': '52', '2thessalonians': '53', '1timothy': '54', '2timothy': '55',
    'titus': '56', 'philemon': '57', 'hebrews': '58', 'james': '59', '1peter': '60',
    '2peter': '61', '1john': '62', '2john': '63', '3john': '64', 'jude': '65',
    'revelation': '66'
}

def parse_file_name(filename):
    """Extract book name and chapter number from filename.
    Example: genesis_ch1_raw_formatted.txt -> ('genesis', 1)
    Example: 1chronicles_ch10_raw_formatted.txt -> ('1chronicles', 10)
    """
    # Remove _raw_formatted.txt suffix
    base = filename.replace('_raw_formatted.txt', '')
    
    # Split on _ch
    parts = base.split('_ch')
    if len(parts) != 2:
        return None, None
    
    book_name = parts[0]
    try:
        chapter_num = int(parts[1])
        return book_name, chapter_num
    except ValueError:
        return None, None


def parse_crossref_file(file_path):
    """Parse a single cross-reference file.
    Returns list of crossref dictionaries with verse, letter, and reference text.
    """
    crossrefs = []
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    lines = content.split('\n')
    
    for line in lines:
        line = line.strip()
        
        # Skip empty lines and CHAPTER headers
        if not line or line.startswith('CHAPTER'):
            continue
        
        # Match pattern: "NUMBER LETTER REFERENCES"
        # Example: "1 a Ps. 102:25; Is. 40:21; [John 1:1-3; Heb. 1:10]"
        match = re.match(r'^(\d+)\s+([a-z])\s+(.+)$', line)
        
        if match:
            verse_num = match.group(1)
            letter = match.group(2)
            reference_text = match.group(3).strip()
            
            crossrefs.append({
                'verse': verse_num,
                'letter': letter,
                'reference': reference_text
            })
    
    return crossrefs


def convert_to_cvcim_format(crossrefs, book_name, chapter_num):
    """Convert parsed cross-references to C/V/c/i/m format.
    
    Format:
    C    Chapter {N}
    V    {book_num}{chapter}{verse}
    c    {letter}
    i    c{book_num}{chapter}{verse}.{counter}
    m    {reference text}
    """
    # Normalize book name (remove underscores for lookup)
    normalized_book = book_name.replace('_', '').lower()
    book_num = BOOK_NUMBERS.get(normalized_book, '01')
    
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


def process_all_files():
    """Process all formatted files and generate C/V/c/i/m output."""
    
    input_dir = Path('raw/cross_refs_nkjv/raw_formatted')
    output_base_dir = Path('raw/cross_refs_nkjv')
    
    if not input_dir.exists():
        print(f"ERROR: Input directory not found: {input_dir}")
        return
    
    # Get all formatted files
    files = sorted(input_dir.glob('*_raw_formatted.txt'))
    
    if not files:
        print(f"ERROR: No formatted files found in {input_dir}")
        return
    
    print(f"Found {len(files)} files to process")
    print("=" * 70)
    
    # Statistics
    stats = {
        'total_files': 0,
        'successful_files': 0,
        'failed_files': 0,
        'total_crossrefs': 0,
        'books_processed': defaultdict(int),
        'files_written': 0
    }
    
    failed_files = []
    
    for file_path in files:
        filename = file_path.name
        book_name, chapter_num = parse_file_name(filename)
        
        if not book_name or not chapter_num:
            print(f"✗ Could not parse filename: {filename}")
            stats['failed_files'] += 1
            failed_files.append(filename)
            continue
        
        stats['total_files'] += 1
        
        try:
            # Parse the file
            crossrefs = parse_crossref_file(file_path)
            
            if crossrefs:
                # Convert to C/V/c/i/m format
                output = convert_to_cvcim_format(crossrefs, book_name, chapter_num)
                
                # Create book folder if it doesn't exist
                book_folder = output_base_dir / book_name
                book_folder.mkdir(parents=True, exist_ok=True)
                
                # Write chapter file (e.g., genesis/1.txt, genesis/2.txt)
                chapter_file = book_folder / f"{chapter_num}.txt"
                with open(chapter_file, 'w', encoding='utf-8') as f:
                    f.write(output)
                
                stats['successful_files'] += 1
                stats['total_crossrefs'] += len(crossrefs)
                stats['books_processed'][book_name] += 1
                stats['files_written'] += 1
                
                print(f"✓ {book_name.ljust(20)} Ch {str(chapter_num).rjust(3)} - {len(crossrefs)} refs → {chapter_file}")
            else:
                print(f"⊘ {book_name.ljust(20)} Ch {str(chapter_num).rjust(3)} - no refs found")
                stats['successful_files'] += 1
                stats['books_processed'][book_name] += 1
                
        except Exception as e:
            print(f"✗ {book_name.ljust(20)} Ch {str(chapter_num).rjust(3)} - ERROR: {e}")
            stats['failed_files'] += 1
            failed_files.append(filename)
    
    print("=" * 70)
    print(f"\nProcessing complete!")
    print(f"  Total files: {stats['total_files']}")
    print(f"  Successful: {stats['successful_files']}")
    print(f"  Failed: {stats['failed_files']}")
    print(f"  Files written: {stats['files_written']}")
    print(f"  Total cross-references: {stats['total_crossrefs']:,}")
    
    if failed_files:
        print(f"\nFailed files ({len(failed_files)}):")
        for f in failed_files:
            print(f"  - {f}")
    
    print(f"\nBooks processed:")
    for book in sorted(stats['books_processed'].keys()):
        print(f"  {book.ljust(20)}: {stats['books_processed'][book]} chapters")
    
    print(f"\n✓ All files written to: {output_base_dir}/")
    print(f"  Book folders created: {len(stats['books_processed'])}")
    
    return stats, failed_files


def main():
    print("NKJV Cross-Reference Batch Parser")
    print("Converting all formatted files to C/V/c/i/m format")
    print("=" * 70)
    
    stats, failed = process_all_files()
    
    print("\n" + "=" * 70)
    print("BATCH PROCESSING COMPLETE")
    print("=" * 70)


if __name__ == '__main__':
    main()
