#!/usr/bin/env python3
"""
Add Words of Christ markup to NKJV XML files by scraping Bible Gateway.
Wraps Christ's words in <woc> tags based on the 'woj' class from Bible Gateway.
"""

import requests
from bs4 import BeautifulSoup
import time
import re
import xml.etree.ElementTree as ET
from pathlib import Path

# Bible structure - New Testament only (Words of Christ are only in NT)
NT_BOOKS = [
    ('matthew', 'Matthew', 28, 40),
    ('mark', 'Mark', 16, 41),
    ('luke', 'Luke', 24, 42),
    ('john', 'John', 21, 43),
    ('acts', 'Acts', 28, 44),
    ('romans', 'Romans', 16, 45),
    ('1_corinthians', '1 Corinthians', 16, 46),
    ('2_corinthians', '2 Corinthians', 13, 47),
    ('galatians', 'Galatians', 6, 48),
    ('ephesians', 'Ephesians', 6, 49),
    ('philippians', 'Philippians', 4, 50),
    ('colossians', 'Colossians', 4, 51),
    ('1_thessalonians', '1 Thessalonians', 5, 52),
    ('2_thessalonians', '2 Thessalonians', 3, 53),
    ('1_timothy', '1 Timothy', 6, 54),
    ('2_timothy', '2 Timothy', 4, 55),
    ('titus', 'Titus', 3, 56),
    ('philemon', 'Philemon', 1, 57),
    ('hebrews', 'Hebrews', 13, 58),
    ('james', 'James', 5, 59),
    ('1_peter', '1 Peter', 5, 60),
    ('2_peter', '2 Peter', 3, 61),
    ('1_john', '1 John', 5, 62),
    ('2_john', '2 John', 1, 63),
    ('3_john', '3 John', 1, 64),
    ('jude', 'Jude', 1, 65),
    ('revelation', 'Revelation', 22, 66)
]

def fetch_words_of_christ_map(book_name, chapter_num):
    """
    Fetch Words of Christ data from Bible Gateway.
    Returns a dict mapping verse numbers to lists of WOC text segments.
    """
    url = f"https://www.biblegateway.com/passage/?search={book_name}+{chapter_num}&version=NKJV&interface=print"
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Find the passage text
        passage_div = soup.find('div', class_='passage-text')
        if not passage_div:
            return {}
        
        # Map verse numbers to WOC segments
        woc_map = {}
        
        # Find all verse spans
        for verse_span in passage_div.find_all('span', class_=re.compile(r'text.*')):
            span_id = verse_span.get('id', '')
            # Extract verse number from id like "en-NKJV-26137" 
            # We need to look at the class to get verse number
            verse_classes = verse_span.get('class', [])
            verse_num = None
            
            for cls in verse_classes:
                # Class format: "text John-3-16" -> verse 16
                match = re.search(r'-(\d+)$', cls)
                if match:
                    verse_num = int(match.group(1))
                    break
            
            if not verse_num:
                continue
            
            # Find all WOC spans within this verse
            woc_segments = []
            for woc_span in verse_span.find_all('span', class_='woj'):
                woc_text = woc_span.get_text()
                if woc_text.strip():
                    woc_segments.append(woc_text)
            
            if woc_segments:
                woc_map[verse_num] = woc_segments
        
        return woc_map
        
    except Exception as e:
        print(f"    Error fetching {book_name} {chapter_num}: {e}")
        return {}

def add_woc_to_verse(verse_elem, woc_segments):
    """
    Add <woc> tags to verse text based on WOC segments.
    This tries to find and wrap the WOC text within the verse.
    """
    if not woc_segments:
        return False
    
    # Get all text content from the verse
    full_text = ET.tostring(verse_elem, encoding='unicode', method='text')
    
    modified = False
    
    for woc_text in woc_segments:
        # Clean the WOC text for matching
        woc_clean = woc_text.strip()
        if not woc_clean:
            continue
        
        # Try to find this text in the verse
        # We need to recursively search through the verse element
        modified |= wrap_text_in_woc(verse_elem, woc_clean)
    
    return modified

def wrap_text_in_woc(elem, target_text):
    """
    Recursively search for target_text in element and wrap it in <woc> tag.
    Returns True if text was found and wrapped.
    """
    # Check element's text
    if elem.text and target_text in elem.text:
        index = elem.text.index(target_text)
        
        # Split the text
        before = elem.text[:index]
        woc_text = target_text
        after = elem.text[index + len(target_text):]
        
        # Create WOC element
        woc_elem = ET.Element('woc')
        woc_elem.text = woc_text
        woc_elem.tail = after
        
        elem.text = before
        elem.insert(0, woc_elem)
        
        return True
    
    # Check children
    for child in elem:
        if wrap_text_in_woc(child, target_text):
            return True
        
        # Check tail text
        if child.tail and target_text in child.tail:
            index = child.tail.index(target_text)
            
            before = child.tail[:index]
            woc_text = target_text
            after = child.tail[index + len(target_text):]
            
            # Create WOC element
            woc_elem = ET.Element('woc')
            woc_elem.text = woc_text
            woc_elem.tail = after
            
            child.tail = before
            
            # Insert after child
            parent = elem
            child_index = list(parent).index(child)
            parent.insert(child_index + 1, woc_elem)
            
            return True
    
    return False

def add_woc_to_chapter(book_file, chapter_num, book_name):
    """Add Words of Christ to a chapter XML file."""
    
    xml_file = f'xml_nkjv/{book_file}_{chapter_num}.xml'
    
    if not Path(xml_file).exists():
        print(f"  ✗ XML file not found: {xml_file}")
        return False
    
    # Fetch WOC data from Bible Gateway
    woc_map = fetch_words_of_christ_map(book_name, chapter_num)
    
    if not woc_map:
        # No WOC in this chapter
        return True
    
    # Parse XML
    tree = ET.parse(xml_file)
    root = tree.getroot()
    
    # Find all verse elements
    verses_modified = 0
    for verse_elem in root.findall('.//v'):
        verse_num = int(verse_elem.get('n', 0))
        
        if verse_num in woc_map:
            woc_segments = woc_map[verse_num]
            if add_woc_to_verse(verse_elem, woc_segments):
                verses_modified += 1
    
    if verses_modified > 0:
        # Save the modified XML
        tree.write(xml_file, encoding='utf-8', xml_declaration=True)
        print(f"    Added WOC to {verses_modified} verses")
        return True
    
    return True

def indent_xml(elem, level=0):
    """Add pretty-printing indentation to XML."""
    indent = "\n" + "\t" * level
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = indent + "\t"
        if not elem.tail or not elem.tail.strip():
            elem.tail = indent
        for child in elem:
            indent_xml(child, level + 1)
        if not child.tail or not child.tail.strip():
            child.tail = indent
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = indent

def main():
    print("=" * 80)
    print("ADDING WORDS OF CHRIST TO NKJV XML FILES")
    print("=" * 80)
    print()
    
    total_chapters = sum(num_chapters for _, _, num_chapters, _ in NT_BOOKS)
    processed = 0
    failed = []
    
    for book_file, book_name, num_chapters, book_num in NT_BOOKS:
        print(f"Processing {book_name} ({num_chapters} chapters)...")
        
        for chapter_num in range(1, num_chapters + 1):
            try:
                if add_woc_to_chapter(book_file, chapter_num, book_name):
                    processed += 1
                else:
                    failed.append(f"{book_name} {chapter_num}")
            except Exception as e:
                print(f"  ✗ Error: {e}")
                failed.append(f"{book_name} {chapter_num}")
            
            # Be nice to the server
            time.sleep(0.5)
    
    print()
    print("=" * 80)
    print(f"✓ Successfully processed {processed}/{total_chapters} chapters")
    
    if failed:
        print(f"✗ Failed: {len(failed)} chapters")
        for f in failed[:10]:
            print(f"  - {f}")
    
    print("=" * 80)

if __name__ == '__main__':
    main()
