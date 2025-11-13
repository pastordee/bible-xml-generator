#!/usr/bin/env python3
"""
Final enhanced parser with advanced edge case handling.
Focuses on the hardest-to-parse verses.
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

def extract_verse_ultra(text, verse_num):
    """Ultra-aggressive verse extraction."""
    
    # Try to find verse marker
    verse_marker = rf'{verse_num}\[†\]'
    
    if not re.search(verse_marker, text):
        return None
    
    # Find all verse markers in text
    all_markers = list(re.finditer(r'(\d+)\[†\]', text))
    
    # Find our verse
    start_idx = None
    end_idx = len(text)
    
    for i, match in enumerate(all_markers):
        if int(match.group(1)) == verse_num:
            start_idx = match.end()
            # Next verse or end
            if i + 1 < len(all_markers):
                end_idx = all_markers[i + 1].start()
            break
    
    if start_idx is None:
        return None
    
    verse_text = text[start_idx:end_idx].strip()
    
    # Remove section headings (lines that are mostly caps)
    lines = []
    for line in verse_text.split('\n'):
        line = line.strip()
        if not line:
            continue
        # Skip if mostly uppercase and relatively short
        if len(line) < 100:
            upper_count = sum(1 for c in line if c.isupper())
            if upper_count / len(line) > 0.6:
                continue
        lines.append(line)
    
    verse_text = ' '.join(lines)
    
    # Look for cross-reference letters
    # Pattern: word followed by period/comma, then single letter, then space
    letter_positions = {}
    
    # Split into words
    words = re.findall(r"\b[A-Za-z]+(?:['-][A-Za-z]+)*\b|[^\s]+", verse_text)
    
    for i, token in enumerate(words):
        # Check if this token contains a standalone letter
        # Common patterns: "word. a ", "word, b ", "word; c "
        match = re.search(r'\b([a-z])\b', token)
        
        if match and len(token) <= 3:  # Single letter or letter with punctuation
            letter = match.group(1)
            
            # Find previous real word
            for j in range(i-1, max(0, i-10), -1):
                prev_word = re.sub(r'[^a-zA-Z\'-]', '', words[j])
                
                # Must be actual word (2+ chars or single uppercase)
                if len(prev_word) >= 2:
                    letter_positions[letter] = {
                        'word_before': prev_word,
                        'index': j
                    }
                    break
                elif len(prev_word) == 1 and prev_word.isupper():
                    letter_positions[letter] = {
                        'word_before': prev_word,
                        'index': j
                    }
                    break
    
    return letter_positions if letter_positions else None

def smart_word_match(verse_elem, word, letter, book_num, chapter, verse_num, sequence):
    """Smart word matching with multiple fallback strategies."""
    
    cid = f"c{book_num}{int(chapter):03d}{int(verse_num):03d}.{sequence}"
    
    # Collect all text from verse
    all_text = []
    if verse_elem.text:
        all_text.append(('text', verse_elem, verse_elem.text))
    
    for child in verse_elem:
        if child.tail:
            all_text.append(('tail', child, child.tail))
    
    # Generate word variations
    word_lower = word.lower()
    variations = [
        word,
        word_lower,
        word.capitalize(),
    ]
    
    # Add hyphenated versions
    if 'minded' in word_lower or 'hearted' in word_lower:
        variations.append(word_lower.replace('minded', '-minded'))
        variations.append(word_lower.replace('hearted', '-hearted'))
    
    # Try each text segment with each variation
    for variation in variations:
        for text_type, element, text_content in all_text:
            # Exact word boundary match
            pattern = rf'\b({re.escape(variation)})\b'
            match = re.search(pattern, text_content, re.IGNORECASE)
            
            if match:
                # Split and insert
                before = text_content[:match.end()]
                after = text_content[match.end():]
                
                crossref = ET.Element('crossref', attrib={'let': letter, 'cid': cid})
                crossref.tail = after
                
                if text_type == 'text':
                    verse_elem.text = before + '\n\t\t\t\t'
                    verse_elem.insert(0, crossref)
                else:
                    element.tail = before + '\n\t\t\t\t'
                    # Find position
                    for idx, child in enumerate(verse_elem):
                        if child == element:
                            verse_elem.insert(idx + 1, crossref)
                            break
                
                return True
    
    # Last resort: fuzzy match (word appears anywhere)
    for variation in variations:
        for text_type, element, text_content in all_text:
            if variation.lower() in text_content.lower():
                # Find it without word boundaries
                idx = text_content.lower().find(variation.lower())
                if idx >= 0:
                    # Insert after the found word
                    end_idx = idx + len(variation)
                    before = text_content[:end_idx]
                    after = text_content[end_idx:]
                    
                    crossref = ET.Element('crossref', attrib={'let': letter, 'cid': cid})
                    crossref.tail = after
                    
                    if text_type == 'text':
                        verse_elem.text = before + '\n\t\t\t\t'
                        verse_elem.insert(0, crossref)
                    else:
                        element.tail = before + '\n\t\t\t\t'
                        for idx2, child in enumerate(verse_elem):
                            if child == element:
                                verse_elem.insert(idx2 + 1, crossref)
                                break
                    
                    return True
    
    return False

def process_chapter_final(text_file, xml_file, book_name, chapter_num, missing_refs):
    """Final processing with ultra mode."""
    
    if not text_file.exists() or not xml_file.exists():
        return 0, 0
    
    text = text_file.read_text(encoding='utf-8')
    
    book_num = BOOK_NUMBERS.get(book_name)
    if not book_num:
        return 0, 0
    
    total_added = 0
    total_failed = 0
    
    for verse_num, letters_to_add in sorted(missing_refs.items()):
        letter_positions = extract_verse_ultra(text, verse_num)
        
        if not letter_positions:
            total_failed += len(letters_to_add)
            continue
        
        tree = ET.parse(xml_file)
        root = tree.getroot()
        verse_elem = root.find(f".//v[@n='{verse_num}']")
        
        if verse_elem is None:
            total_failed += len(letters_to_add)
            continue
        
        # Get next sequence
        max_seq = 0
        for crossref in verse_elem.findall('.//crossref'):
            cid = crossref.get('cid', '')
            if cid and '.' in cid:
                try:
                    max_seq = max(max_seq, int(cid.split('.')[-1]))
                except ValueError:
                    pass
        
        next_seq = max_seq + 1
        verse_modified = False
        
        for letter in letters_to_add:
            if letter not in letter_positions:
                total_failed += 1
                continue
            
            word = letter_positions[letter]['word_before']
            
            if smart_word_match(verse_elem, word, letter, book_num, chapter_num, verse_num, next_seq):
                total_added += 1
                next_seq += 1
                verse_modified = True
            else:
                total_failed += 1
        
        if verse_modified:
            tree.write(xml_file, encoding='utf-8', xml_declaration=True)
    
    return total_added, total_failed

def main():
    print("="*80)
    print("FINAL ENHANCED PARSER - ULTRA MODE")
    print("="*80)
    print()
    
    text_dirs = [Path('chapter_texts'), Path('chapter_texts_ot')]
    xml_dir = Path('xml_esv')
    
    json_file = Path('missing_crossrefs.json')
    if not json_file.exists():
        print("Error: missing_crossrefs.json not found!")
        return
    
    with open(json_file, 'r') as f:
        all_missing = json.load(f)
    
    text_files = []
    for text_dir in text_dirs:
        if text_dir.exists():
            text_files.extend(list(text_dir.glob('*.txt')))
    
    print(f"Processing {len(text_files)} chapter files...")
    print()
    
    grand_total_added = 0
    grand_total_failed = 0
    chapters_processed = 0
    
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
        added, failed = process_chapter_final(text_file, xml_file, book_name, chapter_num, chapter_missing)
        
        if added > 0:
            print(f"✓ {book_name} {chapter_num}: +{added}")
        
        grand_total_added += added
        grand_total_failed += failed
        chapters_processed += 1
    
    print()
    print("="*80)
    print(f"Processed {chapters_processed} chapters")
    print(f"Added: {grand_total_added}")
    print(f"Failed: {grand_total_failed}")
    print("="*80)

if __name__ == '__main__':
    main()
