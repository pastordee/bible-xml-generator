#!/usr/bin/env python3
"""
Use the john_7.txt file (with embedded letters) to add missing cross-references
at the exact correct word positions in the XML.
"""

import re
import xml.etree.ElementTree as ET
from pathlib import Path

def parse_verse_with_letters(text, verse_num):
    """
    Extract a verse from the text file and identify word positions for each letter.
    Returns: {letter: (word_before, word_index)}
    """
    # Find the verse
    pattern = rf'{verse_num}\[†\](.+?)(?={verse_num+1}[\s\[]|$)'
    match = re.search(pattern, text, re.DOTALL)
    
    if not match:
        return None
    
    verse_text = match.group(1).strip()
    
    # Find all words and cross-reference letters
    # Letter pattern: space + single lowercase letter + space/punctuation
    words = []
    current_pos = 0
    
    # Split into tokens (words and letters)
    tokens = re.findall(r'\S+', verse_text)
    
    letter_positions = {}
    
    for i, token in enumerate(tokens):
        # Check if this token contains a single letter marker
        # Pattern: ends with or contains a standalone lowercase letter
        letter_match = re.search(r'\b([a-z])\b', token)
        
        if letter_match:
            letter = letter_match.group(1)
            # Get the previous actual word (not a letter)
            for j in range(i-1, -1, -1):
                prev_token = tokens[j]
                # Clean punctuation and check if it's a real word
                clean_word = re.sub(r'[^a-zA-Z]', '', prev_token)
                if len(clean_word) > 1 or clean_word.upper() == clean_word:
                    letter_positions[letter] = {
                        'word_before': clean_word,
                        'full_token': prev_token,
                        'position': j
                    }
                    break
    
    return letter_positions

def get_xml_verse_element(xml_file, verse_num):
    """Get the verse element from XML."""
    tree = ET.parse(xml_file)
    root = tree.getroot()
    verse_elem = root.find(f".//v[@n='{verse_num}']")
    return tree, root, verse_elem

def find_and_insert_crossref(verse_elem, word_to_find, letter, book_num, chapter, verse_num, sequence):
    """
    Find a specific word in the verse XML and insert cross-reference after it.
    """
    cid = f"c{book_num}{int(chapter):03d}{int(verse_num):03d}.{sequence}"
    
    # Helper to check if word is in text
    def text_contains_word(text, word):
        if not text:
            return False
        # Case insensitive match
        pattern = rf'\b{re.escape(word)}\b'
        return re.search(pattern, text, re.IGNORECASE) is not None
    
    # Try to insert after the word in verse text or child tails
    # First, check verse's own text
    if verse_elem.text and text_contains_word(verse_elem.text, word_to_find):
        # Find position and split
        pattern = rf'(\b{re.escape(word_to_find)}\b)'
        match = re.search(pattern, verse_elem.text, re.IGNORECASE)
        if match:
            before = verse_elem.text[:match.end()]
            after = verse_elem.text[match.end():]
            
            # Create crossref
            crossref = ET.Element('crossref', attrib={'let': letter, 'cid': cid})
            crossref.tail = after
            
            verse_elem.text = before + '\n\t\t\t\t'
            verse_elem.insert(0, crossref)
            return True
    
    # Check in children's text and tails
    for i, child in enumerate(list(verse_elem)):
        # Check child's tail (text after the element)
        if child.tail and text_contains_word(child.tail, word_to_find):
            pattern = rf'(\b{re.escape(word_to_find)}\b)'
            match = re.search(pattern, child.tail, re.IGNORECASE)
            if match:
                before = child.tail[:match.end()]
                after = child.tail[match.end():]
                
                # Create crossref
                crossref = ET.Element('crossref', attrib={'let': letter, 'cid': cid})
                crossref.tail = after
                
                child.tail = before + '\n\t\t\t\t'
                # Insert after current child
                verse_elem.insert(i + 1, crossref)
                return True
    
    return False

def main():
    print("="*80)
    print("POSITION-AWARE CROSS-REFERENCE INSERTION FROM john_7.txt")
    print("="*80)
    print()
    
    # Read the text file
    text_file = Path('john_7.txt')
    if not text_file.exists():
        print(f"Error: {text_file} not found!")
        return
    
    text = text_file.read_text(encoding='utf-8')
    
    # XML file
    xml_file = Path('xml_esv/john_7.xml')
    if not xml_file.exists():
        print(f"Error: {xml_file} not found!")
        return
    
    # Missing cross-references for John 7
    missing = {
        28: ['f', 'g'],
        29: ['j'],
        35: ['w'],
        37: ['a']
    }
    
    print("Missing cross-references to add:")
    for verse, letters in sorted(missing.items()):
        print(f"  Verse {verse}: {', '.join(letters)}")
    print()
    
    response = input("Proceed? (yes/no): ")
    if response.lower() != 'yes':
        print("Cancelled.")
        return
    
    book_num = '43'  # John
    chapter = '7'
    total_added = 0
    
    for verse_num, letters_to_add in sorted(missing.items()):
        print(f"\nProcessing verse {verse_num}...")
        
        # Parse verse from text file
        letter_positions = parse_verse_with_letters(text, verse_num)
        
        if not letter_positions:
            print(f"  Warning: Could not parse verse {verse_num} from text file")
            continue
        
        # Load XML
        tree, root, verse_elem = get_xml_verse_element(xml_file, verse_num)
        
        if verse_elem is None:
            print(f"  Warning: Verse {verse_num} not found in XML")
            continue
        
        # Get next sequence number
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
        
        # Add each missing letter
        for letter in letters_to_add:
            if letter not in letter_positions:
                print(f"  Warning: Letter '{letter}' not found in text file")
                continue
            
            word_info = letter_positions[letter]
            word = word_info['word_before']
            
            print(f"  Letter '{letter}' -> after word '{word}'")
            
            if find_and_insert_crossref(verse_elem, word, letter, book_num, chapter, verse_num, next_seq):
                print(f"    ✓ Inserted after '{word}'")
                total_added += 1
                next_seq += 1
            else:
                print(f"    ✗ Could not find '{word}' in XML")
        
        # Save after each verse
        tree.write(xml_file, encoding='utf-8', xml_declaration=True)
    
    print()
    print("="*80)
    print(f"✅ Added {total_added} cross-references with correct positioning!")
    print("="*80)
    print()
    print("Verify with: python3 compare_with_study_bible.py")

if __name__ == '__main__':
    main()
