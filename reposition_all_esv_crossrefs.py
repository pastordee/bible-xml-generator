#!/usr/bin/env python3
"""
Reposition ALL ESV cross-references to their correct inline positions
using the extracted chapter text files as a positioning guide.
"""

import re
from pathlib import Path
import xml.etree.ElementTree as ET
from collections import defaultdict

# Book name mapping
BOOK_NAME_MAP = {
    'genesis': 'genesis', 'exodus': 'exodus', 'leviticus': 'leviticus', 'numbers': 'numbers', 
    'deuteronomy': 'deuteronomy', 'joshua': 'joshua', 'judges': 'judges', 'ruth': 'ruth',
    '1_samuel': '1samuel', '2_samuel': '2samuel', '1_kings': '1kings', '2_kings': '2kings',
    '1_chronicles': '1chronicles', '2_chronicles': '2chronicles', 'ezra': 'ezra', 
    'nehemiah': 'nehemiah', 'esther': 'esther', 'job': 'job', 'psalms': 'psalms',
    'proverbs': 'proverbs', 'ecclesiastes': 'ecclesiastes', 'song_of_solomon': 'songofsolomon',
    'isaiah': 'isaiah', 'jeremiah': 'jeremiah', 'lamentations': 'lamentations',
    'ezekiel': 'ezekiel', 'daniel': 'daniel', 'hosea': 'hosea', 'joel': 'joel',
    'amos': 'amos', 'obadiah': 'obadiah', 'jonah': 'jonah', 'micah': 'micah',
    'nahum': 'nahum', 'habakkuk': 'habakkuk', 'zephaniah': 'zephaniah', 'haggai': 'haggai',
    'zechariah': 'zechariah', 'malachi': 'malachi',
    'matthew': 'matthew', 'mark': 'mark', 'luke': 'luke', 'john': 'john', 'acts': 'acts',
    'romans': 'romans', '1_corinthians': '1corinthians', '2_corinthians': '2corinthians',
    'galatians': 'galatians', 'ephesians': 'ephesians', 'philippians': 'philippians',
    'colossians': 'colossians', '1_thessalonians': '1thessalonians', 
    '2_thessalonians': '2thessalonians', '1_timothy': '1timothy', '2_timothy': '2timothy',
    'titus': 'titus', 'philemon': 'philemon', 'hebrews': 'hebrews', 'james': 'james',
    '1_peter': '1peter', '2_peter': '2peter', '1_john': '1john', '2_john': '2john',
    '3_john': '3john', 'jude': 'jude', 'revelation': 'revelation'
}

def extract_verse_positions_from_text(text_content):
    """
    Parse the chapter text to find word positions for each cross-reference letter.
    Handles both NT format (1[†]text) and OT format (verse numbers inline).
    Returns: {verse_num: {letter: word_before_letter}}
    """
    verse_positions = defaultdict(dict)
    
    # Replace newlines with spaces for easier parsing
    text = text_content.replace('\n', ' ')
    
    # Remove footnote markers [1], [2], etc. to avoid confusion with verse numbers
    text = re.sub(r'\s*\[\d+\]', '', text)
    
    # Remove the [†] markers as they're not consistent
    text = re.sub(r'\[†\]', '', text)
    
    # Split on verse numbers - any sequence of digits followed by a capital letter or space
    # This handles: "1 a Adam", "2 b Kenan", "3Enoch", "4Noah", "5 d The"
    verse_splits = re.split(r'\s(\d+)(?=[A-Z\s])', text)
    
    # verse_splits will be: ['header', '1', 'text1', '2', 'text2', '3', 'text3', ...]
    # Start from index 1 (first verse number)
    for i in range(1, len(verse_splits) - 1, 2):
        try:
            verse_num = int(verse_splits[i])
        except:
            continue
            
        verse_text = verse_splits[i + 1]
        
        # Find all cross-reference letters and their positions
        # Pattern: word (with optional punctuation) + space + lowercase_letter + space
        # Examples: "Noah, c Shem", "like g a", "suddenly h there"
        letter_pattern = r'(\w+[.,;:!?]?)\s+([a-z])\s+'
        
        for letter_match in re.finditer(letter_pattern, verse_text):
            word = letter_match.group(1).strip('.,;:!?()')
            letter = letter_match.group(2)
            verse_positions[verse_num][letter] = word
    
    return verse_positions

def insert_crossref_after_word(verse_elem, crossref, target_word):
    """
    Insert crossref element after a specific word in the verse.
    Returns True if successfully inserted.
    """
    # Make word search case-insensitive and handle punctuation
    word_pattern = rf'\b{re.escape(target_word)}\b'
    
    def search_in_element(elem):
        """Recursively search text and tail for the target word."""
        # Check element's text
        if elem.text:
            match = re.search(word_pattern, elem.text, re.IGNORECASE)
            if match:
                # Split text at word end
                before = elem.text[:match.end()]
                after = elem.text[match.end():]
                
                elem.text = before
                crossref.tail = after
                elem.insert(0, crossref)
                return True
        
        # Check children
        for i, child in enumerate(list(elem)):
            if search_in_element(child):
                return True
            
            # Check child's tail
            if child.tail:
                match = re.search(word_pattern, child.tail, re.IGNORECASE)
                if match:
                    before = child.tail[:match.end()]
                    after = child.tail[match.end():]
                    
                    child.tail = before
                    crossref.tail = after
                    elem.insert(i + 1, crossref)
                    return True
        
        return False
    
    return search_in_element(verse_elem)

def reposition_verse_crossrefs(verse_elem, letter_positions):
    """
    Move crossref elements from end of verse to correct inline positions.
    Returns number of crossrefs repositioned.
    """
    if not letter_positions:
        return 0
    
    # Collect all crossrefs with their letters
    crossrefs_to_move = []
    for crossref in list(verse_elem.findall('.//crossref')):
        letter = crossref.get('let', '')
        if letter in letter_positions:
            target_word = letter_positions[letter]
            crossrefs_to_move.append((letter, crossref, target_word))
    
    if not crossrefs_to_move:
        return 0
    
    # Remove all crossrefs first (preserving tail text)
    for letter, crossref, word in crossrefs_to_move:
        tail = crossref.tail or ''
        
        # Find parent
        for elem in verse_elem.iter():
            if crossref in list(elem):
                elem.remove(crossref)
                # Append tail to element's text or last child's tail
                children = list(elem)
                if children:
                    last_child = children[-1]
                    last_child.tail = (last_child.tail or '') + tail
                else:
                    elem.text = (elem.text or '') + tail
                break
    
    # Now insert at correct positions
    repositioned = 0
    for letter, crossref, target_word in crossrefs_to_move:
        if insert_crossref_after_word(verse_elem, crossref, target_word):
            repositioned += 1
        else:
            # Fallback: append at end
            verse_elem.append(crossref)
    
    return repositioned

def process_chapter_file(xml_file, text_file):
    """
    Reposition all crossrefs in a chapter XML using the text file positions.
    """
    if not text_file.exists():
        return 0, 0
    
    # Read the text file
    with open(text_file, 'r', encoding='utf-8') as f:
        text_content = f.read()
    
    # Extract verse positions
    verse_positions = extract_verse_positions_from_text(text_content)
    
    if not verse_positions:
        return 0, 0
    
    # Parse XML
    try:
        tree = ET.parse(xml_file)
        root = tree.getroot()
    except Exception as e:
        print(f"    ERROR parsing XML: {e}")
        return 0, 0
    
    total_verses = 0
    total_repositioned = 0
    
    # Process each verse
    for verse_num, letter_map in verse_positions.items():
        verse_elem = root.find(f'.//v[@n="{verse_num}"]')
        if verse_elem is None:
            continue
        
        # Check if verse has crossrefs
        if not verse_elem.findall('.//crossref'):
            continue
        
        total_verses += 1
        moved = reposition_verse_crossrefs(verse_elem, letter_map)
        total_repositioned += moved
    
    # Save if any changes
    if total_repositioned > 0:
        tree.write(xml_file, encoding='utf-8', xml_declaration=True)
    
    return total_verses, total_repositioned

def main():
    print("=" * 80)
    print("ESV CROSS-REFERENCE REPOSITIONING - ALL BOOKS")
    print("=" * 80)
    print()
    
    xml_dir = Path('xml_esv')
    nt_text_dir = Path('chapter_texts')
    ot_text_dir = Path('chapter_texts_ot')
    
    if not xml_dir.exists():
        print(f"ERROR: {xml_dir} not found")
        return
    
    total_files = 0
    total_verses_processed = 0
    total_crossrefs_moved = 0
    
    # Process all XML files
    for xml_file in sorted(xml_dir.glob('*.xml')):
        # Skip non-chapter files
        if xml_file.stem in ['esv', 'esv_old']:
            continue
        
        # Find corresponding text file
        text_file = nt_text_dir / f"{xml_file.stem}.txt"
        if not text_file.exists():
            text_file = ot_text_dir / f"{xml_file.stem}.txt"
        
        if not text_file.exists():
            continue
        
        total_files += 1
        print(f"Processing {xml_file.name}...", end=' ')
        
        verses, moved = process_chapter_file(xml_file, text_file)
        total_verses_processed += verses
        total_crossrefs_moved += moved
        
        if moved > 0:
            print(f"✓ {verses} verses, {moved} crossrefs repositioned")
        else:
            print(f"- No repositioning needed")
    
    print()
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Files processed: {total_files}")
    print(f"Verses with repositioned crossrefs: {total_verses_processed}")
    print(f"Total crossrefs repositioned: {total_crossrefs_moved}")
    print("=" * 80)

if __name__ == '__main__':
    main()
