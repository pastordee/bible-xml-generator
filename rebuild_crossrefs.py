#!/usr/bin/env python3
"""
Rebuild ESV crossrefs from scratch using cross_refs data files as source of truth.

Process:
1. Remove all existing crossref elements from XML
2. Read cross_refs text file to get all letter/cid mappings for each verse
3. Read raw chapter text to find exact position of each letter marker
4. Create new crossref elements and insert at correct positions in XML
"""

import re
from pathlib import Path
import xml.etree.ElementTree as ET

def get_verse_crossrefs_from_text_file(text_file):
    """
    Extract all crossref data from cross_refs text file.
    Returns: dict mapping verse_id (BBCCCVVV) to list of {letter, cid}
    """
    verse_crossrefs = {}
    
    with open(text_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    current_verse = None
    current_letter = None
    
    for line in lines:
        line = line.strip()
        if line.startswith('V '):
            # Verse line: "V 44001002"
            current_verse = line[2:].strip()
            if current_verse not in verse_crossrefs:
                verse_crossrefs[current_verse] = []
        elif line.startswith('c '):
            # Letter line: "c a"
            current_letter = line[2:].strip()
        elif line.startswith('i ') and current_letter and current_verse:
            # ID line: "i c44001002.1"
            cid = line[2:].strip()
            verse_crossrefs[current_verse].append({
                'letter': current_letter,
                'cid': cid
            })
            current_letter = None
    
    return verse_crossrefs

def extract_verse_letter_positions(raw_text_file, verse_num, needed_letters):
    """
    Extract positions of specific letter markers from raw chapter text.
    Returns: dict of {letter: word_before_letter}
    """
    with open(raw_text_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Special handling for verse 1 - starts after chapter title
    if verse_num == "1":
        verse_pattern = r'[A-Z\s\d]+\[†\](.*?)(?=2\[†\]|2And|2[A-Z]|$)'
        match = re.search(verse_pattern, content, re.DOTALL)
    else:
        # Regular verses: N[†]text or NAnd/NThen/etc. until next verse
        # Try with [†] marker first
        next_verse = str(int(verse_num) + 1)
        verse_pattern = rf'{verse_num}\[†\](.*?)(?={next_verse}\[†\]|{next_verse}And|{next_verse}Then|{next_verse}[A-Z]|$)'
        match = re.search(verse_pattern, content, re.DOTALL)
        
        # If not found, try without [†] marker (e.g., "13And")
        if not match:
            verse_pattern = rf'{verse_num}([A-Z][a-z]+.*?)(?={next_verse}\[†\]|{next_verse}And|{next_verse}Then|{next_verse}[A-Z]|$)'
            match = re.search(verse_pattern, content, re.DOTALL)
    
    if not match:
        return {}
    
    verse_text = match.group(1).strip()
    
    # Find letter markers and words before them
    # Only include letters in needed_letters set
    positions = {}
    
    # Pattern 1: letter at start of verse (after optional whitespace): "^ *letter word"
    # Pattern 2: word + space + letter + space: "word letter "
    
    # Try pattern 1 first: letter at start
    start_pattern = r'^\s*([a-z])\s+(\w+)'
    match = re.search(start_pattern, verse_text)
    if match:
        letter = match.group(1)
        word_after = match.group(2)
        if letter in needed_letters:
            # For letters at start, we'll position before the first word
            positions[letter] = None  # Special marker for "at start"
    
    # Pattern 2: word + space + letter + space
    word_pattern = r'(\w+(?:[.,;:!?])?)\s+([a-z])\s'
    
    for match in re.finditer(word_pattern, verse_text):
        word = match.group(1).strip('.,;:!?()')
        letter = match.group(2)
        
        if letter in needed_letters:
            # Only take first occurrence of each letter
            if letter not in positions:
                positions[letter] = word
    
    return positions

def insert_crossref_after_word(verse_elem, crossref, target_word):
    """
    Insert crossref element after a specific word in the verse.
    Recursively searches through text and tail of all elements.
    """
    word_pattern = rf'\b{re.escape(target_word)}\b'
    
    def search_in_element(elem):
        # Check element's text
        if elem.text:
            match = re.search(word_pattern, elem.text, re.IGNORECASE)
            if match:
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

def rebuild_verse_crossrefs(verse_elem, crossref_data, letter_positions):
    """
    Add crossrefs to verse based on crossref_data and letter_positions.
    Assumes all existing crossrefs have already been removed.
    """
    inserted_count = 0
    
    for cr in crossref_data:
        letter = cr['letter']
        cid = cr['cid']
        
        if letter not in letter_positions:
            print(f"          ⚠ Warning: Letter '{letter}' (cid {cid}) not found in raw text")
            continue
        
        target_word = letter_positions[letter]
        
        # Create new crossref element
        crossref_elem = ET.Element('crossref')
        crossref_elem.set('let', letter)
        crossref_elem.set('cid', cid)
        
        # Insert at correct position
        if target_word is None:
            # Letter at start of verse - insert as first element
            if verse_elem.text:
                crossref_elem.tail = verse_elem.text
                verse_elem.text = '\n\t\t\t\t'
            verse_elem.insert(0, crossref_elem)
            inserted_count += 1
        elif insert_crossref_after_word(verse_elem, crossref_elem, target_word):
            inserted_count += 1
        else:
            print(f"          ⚠ Warning: Couldn't find word '{target_word}' for letter '{letter}'")
            # Fallback: append at end
            verse_elem.append(crossref_elem)
            inserted_count += 1
    
    return inserted_count

def process_xml_file(xml_file, text_file, raw_file):
    """
    Rebuild all crossrefs in an XML file.
    """
    # Get all crossref data from text file
    verse_crossrefs = get_verse_crossrefs_from_text_file(text_file)
    
    # Parse XML
    tree = ET.parse(xml_file)
    root = tree.getroot()
    
    # FIRST: Remove ALL existing crossrefs from ALL verses
    for verse_elem in root.findall('.//v'):
        for crossref in list(verse_elem.findall('.//crossref')):
            tail = crossref.tail or ''
            parent = None
            
            for elem in verse_elem.iter():
                if crossref in list(elem):
                    parent = elem
                    break
            
            if parent is not None:
                parent.remove(crossref)
                if parent.text:
                    parent.text += tail
                else:
                    parent.text = tail
    
    total_inserted = 0
    verses_processed = 0
    
    # NOW: Process each verse and add crossrefs from cross_refs data
    for verse_elem in root.findall('.//v'):
        verse_num = verse_elem.get('n')
        if not verse_num:
            continue
        
        # Build verse ID to look up in verse_crossrefs
        # Extract book and chapter numbers from first marker or book element
        book_elem = root.find('.//book')
        chapter_elem = root.find('.//chapter')
        
        if not book_elem or not chapter_elem:
            continue
        
        book_num = book_elem.get('num')
        chapter_num = chapter_elem.get('num')
        verse_id = f"{int(book_num):02d}{int(chapter_num):03d}{int(verse_num):03d}"
        
        # Get crossref data for this verse
        if verse_id not in verse_crossrefs:
            continue
        
        crossref_data = verse_crossrefs[verse_id]
        if not crossref_data:
            continue
        
        # Get needed letters
        needed_letters = {cr['letter'] for cr in crossref_data}
        
        # Get letter positions from raw text
        letter_positions = extract_verse_letter_positions(raw_file, verse_num, needed_letters)
        
        if not letter_positions:
            print(f"        Verse {verse_num}: No positions found for letters {sorted(needed_letters)}")
            continue
        
        # Rebuild crossrefs
        inserted = rebuild_verse_crossrefs(verse_elem, crossref_data, letter_positions)
        
        if inserted > 0:
            verses_processed += 1
            total_inserted += inserted
    
    # Save changes
    if total_inserted > 0:
        tree.write(xml_file, encoding='utf-8', xml_declaration=True)
    
    return verses_processed, total_inserted

def get_book_chapter_from_filename(xml_filename):
    """Convert XML filename to book/chapter format."""
    filename = xml_filename.stem
    parts = filename.rsplit('_', 1)
    if len(parts) == 2:
        return parts[0], parts[1]
    return None, None

def main():
    xml_dir = Path('xml_esv')
    crossrefs_dir = Path('xml_esv/cross_refs')
    raw_texts_nt = Path('raw/chapter_texts')
    raw_texts_ot = Path('raw/chapter_texts_ot')
    
    print("=" * 80)
    print("REBUILDING ESV CROSSREFS FROM CROSS_REFS DATA")
    print("=" * 80)
    print()
    
    xml_files = sorted(xml_dir.glob('*.xml'))
    
    total_files = 0
    total_verses = 0
    total_crossrefs = 0
    files_with_issues = []
    
    for xml_file in xml_files:
        book, chapter = get_book_chapter_from_filename(xml_file)
        if not book or not chapter:
            continue
        
        text_file = crossrefs_dir / book / f"{chapter}.txt"
        
        # Try NT directory first, then OT
        raw_file = raw_texts_nt / f"{book}_{chapter}.txt"
        if not raw_file.exists():
            raw_file = raw_texts_ot / f"{book}_{chapter}.txt"
        
        if not text_file.exists() or not raw_file.exists():
            continue
        
        verses, crossrefs = process_xml_file(xml_file, text_file, raw_file)
        
        total_files += 1
        total_verses += verses
        total_crossrefs += crossrefs
        
        # Show progress every 50 files
        if total_files % 50 == 0:
            print(f"  Progress: {total_files} files, {total_verses} verses, {total_crossrefs} crossrefs")
    
    print()
    print("=" * 80)
    print(f"SUMMARY")
    print(f"Files processed: {total_files}")
    print(f"Verses with crossrefs: {total_verses}")
    print(f"Total crossrefs inserted: {total_crossrefs}")
    print("=" * 80)

if __name__ == '__main__':
    main()
