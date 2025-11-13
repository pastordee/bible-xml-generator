#!/usr/bin/env python3
"""
Restore reference (r) parameters to ESV cross-reference files.
Parse the message text to extract book, chapter, and verse references.
"""

import re
import os
from pathlib import Path

# Book name to number mapping (based on standard Bible book order)
BOOK_MAPPING = {
    'Gen.': '01', 'Exod.': '02', 'Lev.': '03', 'Num.': '04', 'Deut.': '05',
    'Josh.': '06', 'Judg.': '07', 'Ruth': '08', '1 Sam.': '09', '2 Sam.': '10',
    '1 Kgs.': '11', '2 Kgs.': '12', '1 Chr.': '13', '2 Chr.': '14', 'Ezra': '15',
    'Neh.': '16', 'Esth.': '17', 'Job': '18', 'Ps.': '19', 'Prov.': '20',
    'Eccles.': '21', 'Song': '22', 'Isa.': '23', 'Jer.': '24', 'Lam.': '25',
    'Ezek.': '26', 'Dan.': '27', 'Hos.': '28', 'Joel': '29', 'Amos': '30',
    'Obad.': '31', 'Jon.': '32', 'Mic.': '33', 'Nah.': '34', 'Hab.': '35',
    'Zeph.': '36', 'Hag.': '37', 'Zech.': '38', 'Mal.': '39',
    'Matt.': '40', 'Mark': '41', 'Luke': '42', 'John': '43', 'Acts': '44',
    'Rom.': '45', '1 Cor.': '46', '2 Cor.': '47', 'Gal.': '48', 'Eph.': '49',
    'Phil.': '50', 'Col.': '51', '1 Thess.': '52', '2 Thess.': '53', '1 Tim.': '54',
    '2 Tim.': '55', 'Titus': '56', 'Philem.': '57', 'Heb.': '58', 'James': '59',
    '1 Pet.': '60', '2 Pet.': '61', '1 John': '62', '2 John': '63', '3 John': '64',
    'Jude': '65', 'Rev.': '66'
}

# Alternative book names
BOOK_ALIASES = {
    'Genesis': 'Gen.', 'Exodus': 'Exod.', 'Leviticus': 'Lev.', 'Numbers': 'Num.',
    'Deuteronomy': 'Deut.', 'Joshua': 'Josh.', 'Judges': 'Judg.',
    '1 Samuel': '1 Sam.', '2 Samuel': '2 Sam.', '1 Kings': '1 Kgs.', '2 Kings': '2 Kgs.',
    '1 Chronicles': '1 Chr.', '2 Chronicles': '2 Chr.',
    'Nehemiah': 'Neh.', 'Esther': 'Esth.', 'Psalm': 'Ps.', 'Psalms': 'Ps.',
    'Proverbs': 'Prov.', 'Ecclesiastes': 'Eccles.', 'Song of Solomon': 'Song',
    'Isaiah': 'Isa.', 'Jeremiah': 'Jer.', 'Lamentations': 'Lam.', 'Ezekiel': 'Ezek.',
    'Daniel': 'Dan.', 'Hosea': 'Hos.', 'Obadiah': 'Obad.', 'Jonah': 'Jon.',
    'Micah': 'Mic.', 'Nahum': 'Nah.', 'Habakkuk': 'Hab.', 'Zephaniah': 'Zeph.',
    'Haggai': 'Hag.', 'Zechariah': 'Zech.', 'Malachi': 'Mal.',
    'Matthew': 'Matt.', 'Philippians': 'Phil.', 'Colossians': 'Col.',
    '1 Thessalonians': '1 Thess.', '2 Thessalonians': '2 Thess.',
    '1 Timothy': '1 Tim.', '2 Timothy': '2 Tim.', 'Philemon': 'Philem.',
    'Hebrews': 'Heb.', '1 Peter': '1 Pet.', '2 Peter': '2 Pet.',
    'Revelation': 'Rev.'
}

def parse_verse_reference(ref_text):
    """
    Parse a verse reference like '4:25, 26' or '5:9-32' into verse codes.
    Returns list of verse codes like '01004025-01004026' or '01005009-01005032'
    """
    # Handle chapter:verse format
    match = re.match(r'(\d+):(\d+(?:-\d+)?(?:,\s*\d+(?:-\d+)?)*)', ref_text.strip())
    if not match:
        return None
    
    chapter = match.group(1)
    verses = match.group(2)
    
    # Split by comma for multiple verse references
    verse_parts = [v.strip() for v in verses.split(',')]
    
    # Detect if comma-separated verses are consecutive (should be a range)
    verse_nums = []
    for part in verse_parts:
        if '-' in part:
            # Already a range
            verse_nums.append(part)
        else:
            verse_nums.append(int(part))
    
    # Check if we have consecutive integers that should be a range
    if len(verse_nums) == 2 and isinstance(verse_nums[0], int) and isinstance(verse_nums[1], int):
        if verse_nums[1] == verse_nums[0] + 1:
            # Consecutive verses like "25, 26" should become "25-26"
            return chapter, [f"{verse_nums[0]}-{verse_nums[1]}"]
    
    # Otherwise return as-is
    verse_codes = []
    for part in verse_parts:
        if '-' in part or isinstance(part, str):
            verse_codes.append(str(part))
        else:
            verse_codes.append(str(part))
    
    return chapter, verse_codes

def create_verse_id(book_num, chapter, verse):
    """Create verse ID like 01004025 (book 01, chapter 004, verse 025)"""
    return f"{book_num}{int(chapter):03d}{int(verse):03d}"

def parse_reference_text(text):
    """
    Parse a reference text and create r parameter entries.
    Example: "Gen. 4:25, 26; 5:3, 6" -> multiple r and m entries
    """
    entries = []
    
    # Split by semicolons first (separate book references)
    parts = text.split(';')
    
    current_book = None
    current_book_num = None
    
    for i, part in enumerate(parts):
        part = part.strip()
        if not part:
            continue
        
        # Check if this part has a book name
        book_found = False
        for book_name, book_code in BOOK_MAPPING.items():
            if part.startswith(book_name):
                current_book = book_name
                current_book_num = book_code
                # Remove book name from part
                part = part[len(book_name):].strip()
                book_found = True
                break
        
        if not book_found:
            # Check aliases
            for alias, canonical in BOOK_ALIASES.items():
                if part.startswith(alias):
                    current_book = canonical
                    current_book_num = BOOK_MAPPING[canonical]
                    part = part[len(alias):].strip()
                    book_found = True
                    break
        
        # Now part should be chapter:verse reference
        if current_book_num and part:
            result = parse_verse_reference(part)
            if result:
                chapter, verse_codes = result
                
                # Create the reference code
                ref_codes = []
                for verse_code in verse_codes:
                    if '-' in verse_code:
                        start, end = verse_code.split('-')
                        ref_codes.append(f"{create_verse_id(current_book_num, chapter, start)}-{create_verse_id(current_book_num, chapter, end)}")
                    else:
                        ref_codes.append(create_verse_id(current_book_num, chapter, verse_code))
                
                # Add r parameter with proper range format
                ref_id = ref_codes[0] if len(ref_codes) == 1 else ' '.join(ref_codes)
                entries.append(('r', f"{ref_id} {current_book} {part}"))
                
                # Add separator if not last part
                if i < len(parts) - 1:
                    entries.append(('m', '; '))
            else:
                # If we can't parse, keep as message
                if book_found:
                    entries.append(('m', f"{current_book} {part}"))
                else:
                    entries.append(('m', part))
                if i < len(parts) - 1:
                    entries.append(('m', '; '))
        else:
            # Keep as message text
            entries.append(('m', part))
            if i < len(parts) - 1:
                entries.append(('m', '; '))
    
    return entries

def process_file(file_path):
    """Process a single cross-reference file to add r parameters."""
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    new_lines = []
    i = 0
    changes = 0
    
    while i < len(lines):
        line = lines[i].rstrip('\n')
        
        # Check if this is a message line
        if line.startswith('m '):
            message_text = line[2:]  # Remove "m " prefix
            
            # Try to parse references from the message
            try:
                entries = parse_reference_text(message_text)
                
                if entries and len(entries) > 1:  # If we found parseable references
                    # Add parsed entries
                    for entry_type, entry_text in entries:
                        new_lines.append(f"{entry_type} {entry_text}\n")
                    changes += 1
                else:
                    # Keep original line
                    new_lines.append(line + '\n')
            except:
                # If parsing fails, keep original
                new_lines.append(line + '\n')
        else:
            # Keep other lines as-is
            new_lines.append(line + '\n')
        
        i += 1
    
    # Write back to file
    with open(file_path, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)
    
    return changes

def main():
    base_dir = Path('xml_esv/cross_refs')
    
    print("=" * 80)
    print("RESTORING ESV CROSS-REFERENCE PARAMETERS")
    print(f"Processing: {base_dir}")
    print("=" * 80)
    print()
    
    total_files = 0
    total_changes = 0
    
    # Process all .txt files in subdirectories
    for book_dir in sorted(base_dir.iterdir()):
        if not book_dir.is_dir():
            continue
        
        for txt_file in sorted(book_dir.glob('*.txt')):
            print(f"Processing {txt_file.relative_to(base_dir)}...", end=' ')
            changes = process_file(txt_file)
            total_files += 1
            total_changes += changes
            
            if changes > 0:
                print(f"✓ {changes} entries updated")
            else:
                print("- no changes")
    
    print()
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Files processed: {total_files}")
    print(f"Entries updated: {total_changes}")
    print("=" * 80)

if __name__ == '__main__':
    main()
