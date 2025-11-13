#!/usr/bin/env python3
"""
Batch process multiple chapters: add cross-references at correct word positions
using text files extracted from the ESV Study Bible PDF.

Usage:
1. Create text files: chapter_texts/genesis_1.txt, chapter_texts/john_3.txt, etc.
2. Copy the chapter text from PDF (with embedded cross-reference letters)
3. Run this script
"""

import re
import xml.etree.ElementTree as ET
from pathlib import Path
import json

# Book name to number mapping (for CID generation)
BOOK_NUMBERS = {
    'genesis': '01', 'exodus': '02', 'leviticus': '03', 'numbers': '04', 'deuteronomy': '05',
    'joshua': '06', 'judges': '07', 'ruth': '08', '1_samuel': '09', '2_samuel': '10',
    '1_kings': '11', '2_kings': '12', '1_chronicles': '13', '2_chronicles': '14', 'ezra': '15',
    'nehemiah': '16', 'esther': '17', 'job': '18', 'psalms': '19', 'proverbs': '20',
    'ecclesiastes': '21', 'song_of_solomon': '22', 'isaiah': '23', 'jeremiah': '24',
    'lamentations': '25', 'ezekiel': '26', 'daniel': '27', 'hosea': '28', 'joel': '29',
    'amos': '30', 'obadiah': '31', 'jonah': '32', 'micah': '33', 'nahum': '34',
    'habakkuk': '35', 'zephaniah': '36', 'haggai': '37', 'zechariah': '38', 'malachi': '39',
    'matthew': '40', 'mark': '41', 'luke': '42', 'john': '43', 'acts': '44',
    'romans': '45', '1_corinthians': '46', '2_corinthians': '47', 'galatians': '48',
    'ephesians': '49', 'philippians': '50', 'colossians': '51', '1_thessalonians': '52',
    '2_thessalonians': '53', '1_timothy': '54', '2_timothy': '55', 'titus': '56',
    'philemon': '57', 'hebrews': '58', 'james': '59', '1_peter': '60', '2_peter': '61',
    '1_john': '62', '2_john': '63', '3_john': '64', 'jude': '65', 'revelation': '66'
}

def parse_verse_with_letters(text, verse_num):
    """Extract verse and identify word positions for each cross-reference letter."""
    # Pattern to find the verse
    pattern = rf'{verse_num}\[†\](.+?)(?=\n?\d+\[†\]|\n?[A-Z]{{2,}}|$)'
    match = re.search(pattern, text, re.DOTALL)
    
    if not match:
        return None
    
    verse_text = match.group(1).strip()
    
    # Find all tokens
    tokens = re.findall(r'\S+', verse_text)
    letter_positions = {}
    
    for i, token in enumerate(tokens):
        # Look for standalone lowercase letters
        letter_match = re.search(r'\b([a-z])\b', token)
        
        if letter_match:
            letter = letter_match.group(1)
            # Find the previous actual word
            for j in range(i-1, -1, -1):
                prev_token = tokens[j]
                clean_word = re.sub(r'[^a-zA-Z]', '', prev_token)
                if len(clean_word) > 1 or clean_word.upper() == clean_word:
                    letter_positions[letter] = {
                        'word_before': clean_word,
                        'token': prev_token
                    }
                    break
    
    return letter_positions

def find_and_insert_crossref(verse_elem, word_to_find, letter, book_num, chapter, verse_num, sequence):
    """Find word in XML and insert cross-reference after it."""
    cid = f"c{book_num}{int(chapter):03d}{int(verse_num):03d}.{sequence}"
    
    def text_contains_word(text, word):
        if not text:
            return False
        pattern = rf'\b{re.escape(word)}\b'
        return re.search(pattern, text, re.IGNORECASE) is not None
    
    # Check verse text
    if verse_elem.text and text_contains_word(verse_elem.text, word_to_find):
        pattern = rf'(\b{re.escape(word_to_find)}\b)'
        match = re.search(pattern, verse_elem.text, re.IGNORECASE)
        if match:
            before = verse_elem.text[:match.end()]
            after = verse_elem.text[match.end():]
            
            crossref = ET.Element('crossref', attrib={'let': letter, 'cid': cid})
            crossref.tail = after
            
            verse_elem.text = before + '\n\t\t\t\t'
            verse_elem.insert(0, crossref)
            return True
    
    # Check children tails
    for i, child in enumerate(list(verse_elem)):
        if child.tail and text_contains_word(child.tail, word_to_find):
            pattern = rf'(\b{re.escape(word_to_find)}\b)'
            match = re.search(pattern, child.tail, re.IGNORECASE)
            if match:
                before = child.tail[:match.end()]
                after = child.tail[match.end():]
                
                crossref = ET.Element('crossref', attrib={'let': letter, 'cid': cid})
                crossref.tail = after
                
                child.tail = before + '\n\t\t\t\t'
                verse_elem.insert(i + 1, crossref)
                return True
    
    return False

def process_chapter(text_file, xml_file, book_name, chapter_num, missing_refs):
    """Process one chapter file."""
    print(f"\n{'='*80}")
    print(f"Processing {book_name.upper()} {chapter_num}")
    print('='*80)
    
    # Read text file
    if not text_file.exists():
        print(f"  ✗ Text file not found: {text_file}")
        return 0, 0
    
    text = text_file.read_text(encoding='utf-8')
    
    # Check XML file
    if not xml_file.exists():
        print(f"  ✗ XML file not found: {xml_file}")
        return 0, 0
    
    book_num = BOOK_NUMBERS.get(book_name)
    if not book_num:
        print(f"  ✗ Unknown book: {book_name}")
        return 0, 0
    
    total_added = 0
    total_failed = 0
    
    for verse_num, letters_to_add in sorted(missing_refs.items()):
        print(f"\n  Verse {verse_num}:")
        
        # Parse verse from text
        letter_positions = parse_verse_with_letters(text, verse_num)
        
        if not letter_positions:
            print(f"    ✗ Could not parse verse from text file")
            total_failed += len(letters_to_add)
            continue
        
        # Load XML
        tree = ET.parse(xml_file)
        root = tree.getroot()
        verse_elem = root.find(f".//v[@n='{verse_num}']")
        
        if verse_elem is None:
            print(f"    ✗ Verse not found in XML")
            total_failed += len(letters_to_add)
            continue
        
        # Get next sequence
        max_seq = 0
        for crossref in verse_elem.findall('.//crossref'):
            cid = crossref.get('cid', '')
            if cid and '.' in cid:
                try:
                    seq = int(cid.split('.')[-1])
                    max_seq = max(max_seq, seq)
                except ValueError:
                    pass
        
        next_seq = max_seq + 1
        
        # Add each letter
        for letter in letters_to_add:
            if letter not in letter_positions:
                print(f"    ✗ Letter '{letter}' not found in text")
                total_failed += 1
                continue
            
            word = letter_positions[letter]['word_before']
            
            if find_and_insert_crossref(verse_elem, word, letter, book_num, chapter_num, verse_num, next_seq):
                print(f"    ✓ '{letter}' inserted after '{word}'")
                total_added += 1
                next_seq += 1
            else:
                print(f"    ✗ '{letter}' - word '{word}' not found in XML")
                total_failed += 1
        
        # Save after each verse
        if total_added > 0:
            tree.write(xml_file, encoding='utf-8', xml_declaration=True)
    
    return total_added, total_failed

def main():
    print("="*80)
    print("BATCH CROSS-REFERENCE INSERTION")
    print("="*80)
    print()
    
    # Check both NT and OT directories
    text_dirs = [Path('chapter_texts'), Path('chapter_texts_ot')]
    xml_dir = Path('xml_esv')
    
    # Load missing cross-references
    json_file = Path('missing_crossrefs.json')
    if not json_file.exists():
        print(f"Error: {json_file} not found!")
        print("Run: python3 generate_missing_crossrefs_csv.py")
        return
    
    with open(json_file, 'r') as f:
        all_missing = json.load(f)
    
    # Find all available text files from both directories
    text_files = []
    for text_dir in text_dirs:
        if text_dir.exists():
            text_files.extend(list(text_dir.glob('*.txt')))
    
    if not text_files:
        print(f"No text files found in chapter_texts/ or chapter_texts_ot/")
        print()
        print("To use this tool:")
        print(f"1. Run split_text_into_chapters.py (New Testament)")
        print(f"2. Run split_ot_into_chapters.py (Old Testament)")
        return
    
    print(f"Found {len(text_files)} text file(s) total")
    print()
    
    grand_total_added = 0
    grand_total_failed = 0
    
    for text_file in sorted(text_files):
        # Parse filename: bookname_chapter.txt
        match = re.match(r'(.+)_(\d+)\.txt$', text_file.name)
        if not match:
            print(f"Skipping {text_file.name} (invalid format)")
            continue
        
        book_name = match.group(1)
        chapter_num = int(match.group(2))
        
        # Check if we have missing refs for this chapter
        book_upper = book_name.upper().replace('_', ' ')
        chapter_missing = all_missing.get(book_upper, {}).get(str(chapter_num), {})
        
        if not chapter_missing:
            print(f"\n{book_name} {chapter_num}: No missing cross-references")
            continue
        
        # Process
        xml_file = xml_dir / f"{book_name}_{chapter_num}.xml"
        added, failed = process_chapter(text_file, xml_file, book_name, chapter_num, chapter_missing)
        
        grand_total_added += added
        grand_total_failed += failed
    
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    print(f"Total added:  {grand_total_added}")
    print(f"Total failed: {grand_total_failed}")
    
    if grand_total_added > 0:
        print(f"\n✅ Successfully added {grand_total_added} cross-references!")
    
    print("="*80)

if __name__ == '__main__':
    main()
