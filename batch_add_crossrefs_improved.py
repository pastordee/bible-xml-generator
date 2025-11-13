#!/usr/bin/env python3
"""
Improved batch processor with enhanced verse parsing.
Handles more edge cases and provides better debugging.
"""

import re
import xml.etree.ElementTree as ET
from pathlib import Path
import json

BOOK_NUMBERS = {
    'genesis': '01', 'exodus': '02', 'leviticus': '03', 'numbers': '04', 'deuteronomy': '05',
    'joshua': '06', 'judges': '07', 'ruth': '08', '1_samuel': '09', '2_samuel': '10',
    '1_kings': '11', '2_kings': '12', '1_chronicles': '13', '2_chronicles': '14', 'ezra': '15',
    'nehemiah': '16', 'esther': '17', 'job': '18', 'psalm': '19', 'psalms': '19', 'proverbs': '20',
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

def parse_verse_with_letters_improved(text, verse_num):
    """Improved verse extraction with multiple patterns."""
    
    # Try multiple patterns for verse boundaries
    patterns = [
        # Standard: verse number with [†] followed by text
        rf'{verse_num}\[†\](.+?)(?=\n?\d+\[†\]|$)',
        # Alternative: verse might be followed by heading or next chapter
        rf'{verse_num}\[†\](.+?)(?=\n[A-Z]{{3,}}|\n\d+\[†\]|$)',
        # Simple: just find verse number and grab everything to next verse
        rf'{verse_num}\s*\[†\](.+?)(?=\d+\s*\[†\]|$)',
    ]
    
    verse_text = None
    for pattern in patterns:
        match = re.search(pattern, text, re.DOTALL)
        if match:
            verse_text = match.group(1).strip()
            # Don't accept if too short (likely wrong match)
            if len(verse_text) > 10:
                break
    
    if not verse_text:
        return None
    
    # Remove section headings (all caps text before verse starts)
    lines = verse_text.split('\n')
    clean_lines = []
    for line in lines:
        # Skip heading lines (mostly uppercase and short)
        if len(line.strip()) > 0:
            uppercase_ratio = sum(1 for c in line if c.isupper()) / len(line)
            if uppercase_ratio < 0.7 or len(line) > 100:
                clean_lines.append(line)
    
    verse_text = ' '.join(clean_lines)
    
    # Find all tokens
    tokens = re.findall(r'\S+', verse_text)
    letter_positions = {}
    
    for i, token in enumerate(tokens):
        # Look for standalone lowercase letters (not inside words)
        # Must be surrounded by non-letter characters
        letter_match = re.search(r'(?<![a-zA-Z])([a-z])(?![a-zA-Z])', token)
        
        if letter_match:
            letter = letter_match.group(1)
            
            # Find the previous actual word (skip short words, footnotes, etc.)
            for j in range(i-1, -1, -1):
                prev_token = tokens[j]
                # Clean the token
                clean_word = re.sub(r'[^a-zA-Z]', '', prev_token)
                
                # Must be a real word (2+ chars) or single uppercase letter
                if len(clean_word) >= 2 or (len(clean_word) == 1 and clean_word.isupper()):
                    letter_positions[letter] = {
                        'word_before': clean_word,
                        'token': prev_token
                    }
                    break
    
    return letter_positions

def find_and_insert_crossref_improved(verse_elem, word_to_find, letter, book_num, chapter, verse_num, sequence):
    """Improved word matching with fuzzy search."""
    cid = f"c{book_num}{int(chapter):03d}{int(verse_num):03d}.{sequence}"
    
    def find_word_variations(word):
        """Generate variations of a word for matching."""
        variations = [word]
        # Try with hyphens
        if len(word) > 5:
            variations.append(word.replace('minded', '-minded'))
            variations.append(word.replace('hearted', '-hearted'))
        # Try lowercase
        variations.append(word.lower())
        # Try with common suffixes removed
        for suffix in ['s', 'ed', 'ing', 'ly']:
            if word.endswith(suffix):
                variations.append(word[:-len(suffix)])
        return variations
    
    def text_contains_word(text, word):
        if not text:
            return False
        # Try exact match first
        pattern = rf'\b{re.escape(word)}\b'
        if re.search(pattern, text, re.IGNORECASE):
            return True
        # Try variations
        for variation in find_word_variations(word):
            pattern = rf'\b{re.escape(variation)}\b'
            if re.search(pattern, text, re.IGNORECASE):
                return True
        return False
    
    def do_insert(text_container, attr_name):
        """Insert crossref into text or tail."""
        text = getattr(text_container, attr_name)
        
        # Try exact word first
        word_variations = [word_to_find] + find_word_variations(word_to_find)
        
        for word_var in word_variations:
            pattern = rf'(\b{re.escape(word_var)}\b)'
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                before = text[:match.end()]
                after = text[match.end():]
                
                crossref = ET.Element('crossref', attrib={'let': letter, 'cid': cid})
                crossref.tail = after
                
                setattr(text_container, attr_name, before + '\n\t\t\t\t')
                
                if attr_name == 'text':
                    verse_elem.insert(0, crossref)
                else:
                    # Find index of child
                    for idx, child in enumerate(verse_elem):
                        if child == text_container:
                            verse_elem.insert(idx + 1, crossref)
                            break
                
                return True
        return False
    
    # Check verse text
    if verse_elem.text and text_contains_word(verse_elem.text, word_to_find):
        if do_insert(verse_elem, 'text'):
            return True
    
    # Check children tails
    for child in list(verse_elem):
        if child.tail and text_contains_word(child.tail, word_to_find):
            if do_insert(child, 'tail'):
                return True
    
    return False

def process_chapter(text_file, xml_file, book_name, chapter_num, missing_refs):
    """Process one chapter file."""
    print(f"\n{'='*80}")
    print(f"Processing {book_name.upper()} {chapter_num}")
    print('='*80)
    
    if not text_file.exists():
        print(f"  ✗ Text file not found: {text_file}")
        return 0, 0
    
    text = text_file.read_text(encoding='utf-8')
    
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
        
        letter_positions = parse_verse_with_letters_improved(text, verse_num)
        
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
        
        for letter in letters_to_add:
            if letter not in letter_positions:
                print(f"    ✗ Letter '{letter}' not found in text")
                total_failed += 1
                continue
            
            word = letter_positions[letter]['word_before']
            
            if find_and_insert_crossref_improved(verse_elem, word, letter, book_num, chapter_num, verse_num, next_seq):
                print(f"    ✓ '{letter}' inserted after '{word}'")
                total_added += 1
                next_seq += 1
            else:
                print(f"    ✗ '{letter}' - word '{word}' not found in XML")
                total_failed += 1
        
        if total_added > 0:
            tree.write(xml_file, encoding='utf-8', xml_declaration=True)
    
    return total_added, total_failed

def main():
    print("="*80)
    print("IMPROVED BATCH CROSS-REFERENCE INSERTION")
    print("="*80)
    print()
    
    text_dirs = [Path('chapter_texts'), Path('chapter_texts_ot')]
    xml_dir = Path('xml_esv')
    
    json_file = Path('missing_crossrefs.json')
    if not json_file.exists():
        print(f"Error: {json_file} not found!")
        return
    
    with open(json_file, 'r') as f:
        all_missing = json.load(f)
    
    text_files = []
    for text_dir in text_dirs:
        if text_dir.exists():
            text_files.extend(list(text_dir.glob('*.txt')))
    
    if not text_files:
        print("No text files found!")
        return
    
    print(f"Found {len(text_files)} text file(s) total")
    print()
    
    grand_total_added = 0
    grand_total_failed = 0
    
    for text_file in sorted(text_files):
        match = re.match(r'(.+)_(\d+)\.txt$', text_file.name)
        if not match:
            continue
        
        book_name = match.group(1)
        chapter_num = int(match.group(2))
        
        book_upper = book_name.upper().replace('_', ' ')
        chapter_missing = all_missing.get(book_upper, {}).get(str(chapter_num), {})
        
        if not chapter_missing:
            continue
        
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
