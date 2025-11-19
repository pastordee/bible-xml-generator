#!/usr/bin/env python3
"""
Rebuild ESV XML files with proper Words of Christ markup by scraping Bible Gateway.
Uses the same approach as NKJV - parse HTML structure to get WOC spans, crossrefs, and text.
"""

import requests
from bs4 import BeautifulSoup, NavigableString
import xml.etree.ElementTree as ET
import re
import time
import copy
from pathlib import Path

# All Bible books with chapter counts and book numbers
ALL_BOOKS = [
    # Old Testament
    ('genesis', 'Genesis', 50, 1),
    ('exodus', 'Exodus', 40, 2),
    ('leviticus', 'Leviticus', 27, 3),
    ('numbers', 'Numbers', 36, 4),
    ('deuteronomy', 'Deuteronomy', 34, 5),
    ('joshua', 'Joshua', 24, 6),
    ('judges', 'Judges', 21, 7),
    ('ruth', 'Ruth', 4, 8),
    ('1_samuel', '1 Samuel', 31, 9),
    ('2_samuel', '2 Samuel', 24, 10),
    ('1_kings', '1 Kings', 22, 11),
    ('2_kings', '2 Kings', 25, 12),
    ('1_chronicles', '1 Chronicles', 29, 13),
    ('2_chronicles', '2 Chronicles', 36, 14),
    ('ezra', 'Ezra', 10, 15),
    ('nehemiah', 'Nehemiah', 13, 16),
    ('esther', 'Esther', 10, 17),
    ('job', 'Job', 42, 18),
    ('psalms', 'Psalms', 150, 19),
    ('proverbs', 'Proverbs', 31, 20),
    ('ecclesiastes', 'Ecclesiastes', 12, 21),
    ('song_of_solomon', 'Song of Solomon', 8, 22),
    ('isaiah', 'Isaiah', 66, 23),
    ('jeremiah', 'Jeremiah', 52, 24),
    ('lamentations', 'Lamentations', 5, 25),
    ('ezekiel', 'Ezekiel', 48, 26),
    ('daniel', 'Daniel', 12, 27),
    ('hosea', 'Hosea', 14, 28),
    ('joel', 'Joel', 3, 29),
    ('amos', 'Amos', 9, 30),
    ('obadiah', 'Obadiah', 1, 31),
    ('jonah', 'Jonah', 4, 32),
    ('micah', 'Micah', 7, 33),
    ('nahum', 'Nahum', 3, 34),
    ('habakkuk', 'Habakkuk', 3, 35),
    ('zephaniah', 'Zephaniah', 3, 36),
    ('haggai', 'Haggai', 2, 37),
    ('zechariah', 'Zechariah', 14, 38),
    ('malachi', 'Malachi', 4, 39),
    # New Testament
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
    ('revelation', 'Revelation', 22, 66),
]

def fetch_chapter_html(book_name, chapter_num):
    """Fetch chapter HTML from Bible Gateway."""
    url = f"https://www.biblegateway.com/passage/?search={book_name}+{chapter_num}&version=ESV&interface=print"
    
    try:
        response = requests.get(url, timeout=15, headers={'User-Agent': 'Mozilla/5.0'})
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        passage_div = soup.find('div', class_='passage-text')
        
        return passage_div
    except Exception as e:
        print(f"    Error fetching {book_name} {chapter_num}: {e}")
        return None

def rebuild_chapter_with_woc(book_file, chapter_num, book_name, book_num):
    """Rebuild a chapter with proper WOC markup from Bible Gateway HTML."""
    
    # Read original XML
    xml_file = Path('xml_esv') / f'{book_file}_{chapter_num}.xml'
    if not xml_file.exists():
        return False
    
    tree = ET.parse(xml_file)
    orig_root = tree.getroot()
    
    # Load crossref data to get CID mappings (from original location)
    crossref_file = Path('xml_esv') / 'cross_refs' / book_file / f'{chapter_num}.txt'
    verse_crossrefs = {}
    
    if crossref_file.exists():
        with open(crossref_file, 'r', encoding='utf-8') as f:
            current_verse = None
            current_letter = None
            
            for line in f:
                line = line.strip()
                if not line:
                    continue
                
                parts = line.split(None, 1)
                if len(parts) < 2:
                    continue
                
                field = parts[0]
                value = parts[1] if len(parts) > 1 else ''
                
                if field == 'V':
                    current_verse = value
                    if current_verse not in verse_crossrefs:
                        verse_crossrefs[current_verse] = {}
                elif field == 'c' and current_verse:
                    current_letter = value
                elif field == 'i' and current_verse:
                    verse_crossrefs[current_verse][current_letter] = value
    
    # Fetch HTML from Bible Gateway
    passage_html = fetch_chapter_html(book_name, chapter_num)
    if not passage_html:
        return False
    
    # Copy original XML structure
    new_root = copy.deepcopy(orig_root)
    
    # Find the chapter element
    chapter_elem = new_root.find('.//chapter')
    if not chapter_elem:
        return False
    
    # Build gateway-to-actual letter mapping for the ENTIRE CHAPTER
    # Gateway letters are sequential across the chapter: A, B, C, D... (or AB, AC, AD...)
    # Collect all crossref letters used across all verses
    all_chapter_letters = set()
    for verse_id, crossrefs in verse_crossrefs.items():
        all_chapter_letters.update(crossrefs.keys())
    
    actual_letters = sorted(all_chapter_letters)
    gateway_to_actual = {}
    for idx, actual_letter in enumerate(actual_letters):
        if idx < 26:
            # First 26: single letters A-Z
            single_letter = chr(ord('a') + idx)
            gateway_to_actual[single_letter] = actual_letter
        else:
            # After 26: two-letter codes AA, AB, AC... AZ, BA, BB...
            two_idx = idx - 26
            first = chr(ord('a') + (two_idx // 26))
            second = chr(ord('a') + (two_idx % 26))
            two_letter = first + second
            gateway_to_actual[two_letter] = actual_letter
    
    # Process each verse
    verses_updated = 0
    
    for verse_span in passage_html.find_all('span', class_=re.compile(r'text.*')):
        # Skip heading spans (parent is h1, h2, h3, etc.)
        if verse_span.parent and verse_span.parent.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
            continue
        
        # Get verse number from class
        verse_classes = verse_span.get('class', [])
        verse_num = None
        
        for cls in verse_classes:
            match = re.search(r'-(\d+)$', cls)
            if match:
                verse_num = int(match.group(1))
                break
        
        if not verse_num:
            continue
        
        # Build verse ID
        verse_id = f"{book_num:02d}{chapter_num:03d}{verse_num:03d}"
        
        # Get crossref map for this verse
        crossref_map = verse_crossrefs.get(verse_id, {})
        
        # Find corresponding verse element in XML
        verse_elem = chapter_elem.find(f".//v[@n='{verse_num}']")
        if verse_elem is None:
            continue
        
        # Clear existing content but keep attributes
        verse_elem.clear()
        verse_elem.set('n', str(verse_num))
        
        # Process verse content from HTML
        # We need to properly handle interleaved text and elements
        last_elem = None
        pending_text = []
        
        for child in verse_span.children:
            if isinstance(child, NavigableString):
                text = str(child).strip()
                if text:
                    pending_text.append(text)
            elif child.name == 'span' and 'woj' in child.get('class', []):
                # WOC span - flush pending text first
                if pending_text:
                    text_content = ' '.join(pending_text)
                    if last_elem is not None:
                        # Append to tail of last element
                        if last_elem.tail:
                            last_elem.tail += ' ' + text_content
                        else:
                            last_elem.tail = text_content
                    else:
                        # Set as verse text
                        if verse_elem.text:
                            verse_elem.text += ' ' + text_content
                        else:
                            verse_elem.text = text_content
                    pending_text = []
                
                # Process WOC content recursively (may have crossrefs inside)
                woc_last_elem = None
                woc_pending_text = []
                
                for woc_child in child.children:
                    if isinstance(woc_child, NavigableString):
                        text = str(woc_child).strip()
                        if text:
                            woc_pending_text.append(text)
                    elif woc_child.name == 'sup' and 'crossreference' in woc_child.get('class', []):
                        # Flush WOC text before crossref - ALWAYS create new WOC element
                        if woc_pending_text:
                            text_content = ' '.join(woc_pending_text)
                            woc_elem = ET.SubElement(verse_elem, 'woc')
                            woc_elem.text = text_content
                            woc_last_elem = woc_elem
                            woc_pending_text = []
                        
                        # Create crossref
                        link = woc_child.find('a')
                        if link:
                            gateway_letter = link.get_text(strip=True).strip('()').lower()
                            actual_letter = gateway_to_actual.get(gateway_letter)
                            if actual_letter and actual_letter in crossref_map:
                                crossref_elem = ET.SubElement(verse_elem, 'crossref')
                                crossref_elem.set('let', actual_letter)
                                crossref_elem.set('cid', crossref_map[actual_letter])
                                woc_last_elem = crossref_elem
                    elif woc_child.name == 'sup' and 'footnote' in woc_child.get('class', []):
                        # Skip footnotes
                        pass
                    elif woc_child.name == 'sup' and 'versenum' in woc_child.get('class', []):
                        # Skip verse numbers
                        pass
                    else:
                        text = woc_child.get_text(strip=True)
                        if text:
                            woc_pending_text.append(text)
                
                # Flush remaining WOC text - ALWAYS create new WOC element
                if woc_pending_text:
                    text_content = ' '.join(woc_pending_text)
                    woc_elem = ET.SubElement(verse_elem, 'woc')
                    woc_elem.text = text_content
                    woc_last_elem = woc_elem
                
                last_elem = woc_last_elem if woc_last_elem else last_elem
                
            elif child.name == 'sup':
                if 'crossreference' in child.get('class', []):
                    # Crossref - flush pending text first
                    if pending_text:
                        text_content = ' '.join(pending_text)
                        if last_elem is not None:
                            # Append to tail of last element
                            if last_elem.tail:
                                last_elem.tail += ' ' + text_content
                            else:
                                last_elem.tail = text_content
                        else:
                            # Set as verse text
                            if verse_elem.text:
                                verse_elem.text += ' ' + text_content
                            else:
                                verse_elem.text = text_content
                        pending_text = []
                    
                    # Create crossref element
                    # Extract letter from data-cr or link text
                    link = child.find('a')
                    if link:
                        gateway_letter = link.get_text(strip=True).strip('()').lower()
                        actual_letter = gateway_to_actual.get(gateway_letter)
                        if actual_letter and actual_letter in crossref_map:
                            crossref_elem = ET.SubElement(verse_elem, 'crossref')
                            crossref_elem.set('let', actual_letter)
                            crossref_elem.set('cid', crossref_map[actual_letter])
                            last_elem = crossref_elem
                # Skip verse numbers and footnotes
            elif child.name in ['i', 'b']:
                text = child.get_text(strip=True)
                if text:
                    pending_text.append(text)
            else:
                text = child.get_text(strip=True)
                if text:
                    pending_text.append(text)
        
        # Flush any remaining pending text
        if pending_text:
            text_content = ' '.join(pending_text)
            if last_elem is not None:
                # Append to tail of last element
                if last_elem.tail:
                    last_elem.tail += ' ' + text_content
                else:
                    last_elem.tail = text_content
            else:
                # Set as verse text (no elements, all text)
                verse_elem.text = text_content
        
        verses_updated += 1
    
    if verses_updated > 0:
        # Save to new directory (preserve originals)
        output_dir = Path('xml_esv_with_woc')
        output_dir.mkdir(exist_ok=True)
        output_file = output_dir / f'{book_file}_{chapter_num}.xml'
        
        # Pretty print
        indent_xml(new_root)
        
        tree = ET.ElementTree(new_root)
        tree.write(output_file, encoding='utf-8', xml_declaration=True)
        
        print(f"    Updated {verses_updated} verses")
        return True
    
    return False

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
    print("REBUILDING ESV WITH WORDS OF CHRIST")
    print("=" * 80)
    print()
    print("Output directory: xml_esv_with_woc/")
    print()
    
    # Copy crossref data
    print("Copying crossref data...")
    import shutil
    src_crossrefs = Path('xml_esv/cross_refs')
    dst_crossrefs = Path('xml_esv_with_woc/cross_refs')
    if src_crossrefs.exists():
        shutil.copytree(src_crossrefs, dst_crossrefs, dirs_exist_ok=True)
    print()
    
    # Process all books
    for book_file, book_name, num_chapters, book_num in ALL_BOOKS:
        print(f"Processing {book_name} ({num_chapters} chapters)...")
        
        for chapter_num in range(1, num_chapters + 1):
            success = rebuild_chapter_with_woc(book_file, chapter_num, book_name, book_num)
            
            if not success:
                print(f"    ⚠ Skipped chapter {chapter_num}")
            
            # Rate limiting - be nice to Bible Gateway
            time.sleep(0.6)
    
    print()
    print("=" * 80)
    print("✓ Processing complete!")
    print()
    print("Output saved to: xml_esv_with_woc/")
    print("=" * 80)

if __name__ == '__main__':
    main()
