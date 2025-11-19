#!/usr/bin/env python3
"""
Rebuild NKJV New Testament XML files with proper Words of Christ markup.
This script scrapes Bible Gateway and reconstructs verses with both crossrefs and WOC tags.
Output goes to xml_nkjv_with_woc/ to preserve the original files.
"""

import requests
from bs4 import BeautifulSoup, NavigableString
import time
import re
import xml.etree.ElementTree as ET
from pathlib import Path
import copy

# New Testament books only
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

def fetch_chapter_html(book_name, chapter_num):
    """Fetch chapter HTML from Bible Gateway."""
    url = f"https://www.biblegateway.com/passage/?search={book_name}+{chapter_num}&version=NKJV&interface=print"
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        passage_div = soup.find('div', class_='passage-text')
        
        return passage_div
        
    except Exception as e:
        print(f"    Error fetching: {e}")
        return None

def process_verse_content(verse_span, verse_num, chapter_num, book_num):
    """
    Process a verse span from Bible Gateway HTML and build XML structure.
    Returns a list of elements/text that should be added to the verse.
    """
    elements = []
    
    # Get the crossref map for this verse from the original XML
    original_crossrefs = {}
    
    def process_node(node, in_woc=False):
        """Recursively process HTML nodes and build XML elements."""
        if isinstance(node, NavigableString):
            text = str(node).strip()
            if text:
                return ('text', text, in_woc)
            return None
        
        # Handle WOC spans
        if node.name == 'span' and 'woj' in node.get('class', []):
            # Start WOC section
            results = []
            for child in node.children:
                result = process_node(child, in_woc=True)
                if result:
                    results.append(result)
            return ('woc_section', results)
        
        # Handle crossref markers
        if node.name == 'sup' and 'crossreference' in node.get('class', []):
            # Extract letter from the crossref
            letter_text = node.get_text(strip=True)
            letter = letter_text.strip('()').lower()
            return ('crossref', letter, in_woc)
        
        # Handle verse number
        if node.name == 'sup' and 'versenum' in node.get('class', []):
            # Skip verse numbers
            return None
        
        # Handle footnotes
        if node.name == 'sup' and 'footnote' in node.get('class', []):
            # Skip footnotes
            return None
        
        # Handle italics
        if node.name == 'i':
            text = node.get_text(strip=True)
            if text:
                return ('text', text, in_woc)
            return None
        
        # Recursively process children
        results = []
        for child in node.children:
            result = process_node(child, in_woc)
            if result:
                results.append(result)
        
        if results:
            return ('group', results)
        return None
    
    # Process the verse span
    result = process_node(verse_span)
    return result

def build_verse_xml(verse_structure, crossref_map, verse_num):
    """Build XML elements from processed verse structure."""
    elements = []
    
    def add_elements(struct, inside_woc=False):
        if not struct:
            return
        
        if isinstance(struct, tuple):
            if struct[0] == 'text':
                text = struct[1]
                in_woc = struct[2] if len(struct) > 2 else inside_woc
                if in_woc and not inside_woc:
                    # Start new WOC element
                    woc = ET.Element('woc')
                    woc.text = text
                    elements.append(woc)
                elif in_woc and inside_woc:
                    # Continue WOC text
                    if elements and elements[-1].tag == 'woc':
                        if elements[-1].tail:
                            elements[-1].tail += ' ' + text
                        else:
                            elements[-1].tail = text
                    else:
                        elements.append(('text', text))
                else:
                    # Regular text
                    elements.append(('text', text))
            
            elif struct[0] == 'crossref':
                letter = struct[1]
                in_woc = struct[2] if len(struct) > 2 else inside_woc
                
                # Look up CID from crossref_map
                if letter in crossref_map:
                    cid = crossref_map[letter]
                    crossref = ET.Element('crossref')
                    crossref.set('let', letter)
                    crossref.set('cid', cid)
                    elements.append(crossref)
            
            elif struct[0] == 'woc_section':
                # Create WOC element with contents
                woc = ET.Element('woc')
                woc_contents = struct[1]
                
                # Process WOC contents
                woc_text = []
                for item in woc_contents:
                    if isinstance(item, tuple) and item[0] == 'text':
                        woc_text.append(item[1])
                
                if woc_text:
                    woc.text = ' '.join(woc_text)
                    elements.append(woc)
            
            elif struct[0] == 'group':
                for item in struct[1]:
                    add_elements(item, inside_woc)
        
        elif isinstance(struct, list):
            for item in struct:
                add_elements(item, inside_woc)
    
    add_elements(verse_structure)
    return elements

def rebuild_chapter_with_woc(book_file, chapter_num, book_name, book_num):
    """Rebuild a chapter XML file with proper WOC markup."""
    
    # Read original XML
    original_xml = f'xml_nkjv/{book_file}_{chapter_num}.xml'
    if not Path(original_xml).exists():
        print(f"  ✗ Original XML not found: {original_xml}")
        return False
    
    # Parse original XML to get crossref mappings
    orig_tree = ET.parse(original_xml)
    orig_root = orig_tree.getroot()
    
    # Get crossref CIDs from crossref data files
    crossref_file = f'xml_nkjv/cross_refs/{book_file}/{chapter_num}.txt'
    verse_crossrefs = {}
    
    if Path(crossref_file).exists():
        with open(crossref_file, 'r') as f:
            current_verse = None
            for line in f:
                parts = line.strip().split(None, 1)
                if len(parts) < 2:
                    continue
                
                field, value = parts[0], parts[1]
                
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
    
    # Process each verse
    verses_updated = 0
    
    for verse_span in passage_html.find_all('span', class_=re.compile(r'text.*')):
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
                
                # Create WOC element
                woc_elem = ET.SubElement(verse_elem, 'woc')
                woc_text = child.get_text(strip=False)
                # Clean up extra whitespace
                woc_text = re.sub(r'\s+', ' ', woc_text).strip()
                woc_elem.text = woc_text
                last_elem = woc_elem
                
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
                    letter = child.get_text(strip=True).strip('()').lower()
                    if letter in crossref_map:
                        crossref_elem = ET.SubElement(verse_elem, 'crossref')
                        crossref_elem.set('let', letter)
                        crossref_elem.set('cid', crossref_map[letter])
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
        # Save to new directory
        output_dir = Path('xml_nkjv_with_woc')
        output_dir.mkdir(exist_ok=True)
        output_file = output_dir / f'{book_file}_{chapter_num}.xml'
        
        # Pretty print
        indent_xml(new_root)
        
        new_tree = ET.ElementTree(new_root)
        new_tree.write(output_file, encoding='utf-8', xml_declaration=True)
        
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
    print("REBUILDING NKJV NEW TESTAMENT WITH WORDS OF CHRIST")
    print("=" * 80)
    print()
    print("Output directory: xml_nkjv_with_woc/")
    print()
    
    # Create output directory
    Path('xml_nkjv_with_woc').mkdir(exist_ok=True)
    Path('xml_nkjv_with_woc/cross_refs').mkdir(exist_ok=True)
    
    # Copy crossref data to new directory
    print("Copying crossref data...")
    import shutil
    for book_file, _, _, _ in NT_BOOKS:
        src_dir = Path(f'xml_nkjv/cross_refs/{book_file}')
        if src_dir.exists():
            dst_dir = Path(f'xml_nkjv_with_woc/cross_refs/{book_file}')
            dst_dir.mkdir(parents=True, exist_ok=True)
            for file in src_dir.glob('*.txt'):
                shutil.copy(file, dst_dir / file.name)
    
    print()
    
    total_chapters = sum(num_chapters for _, _, num_chapters, _ in NT_BOOKS)
    processed = 0
    failed = []
    
    for book_file, book_name, num_chapters, book_num in NT_BOOKS:
        print(f"Processing {book_name} ({num_chapters} chapters)...")
        
        for chapter_num in range(1, num_chapters + 1):
            try:
                if rebuild_chapter_with_woc(book_file, chapter_num, book_name, book_num):
                    processed += 1
                else:
                    failed.append(f"{book_name} {chapter_num}")
            except Exception as e:
                print(f"  ✗ Error: {e}")
                failed.append(f"{book_name} {chapter_num}")
            
            # Be nice to the server
            time.sleep(0.6)
    
    print()
    print("=" * 80)
    print(f"✓ Successfully processed {processed}/{total_chapters} chapters")
    
    if failed:
        print(f"✗ Failed: {len(failed)} chapters")
        for f in failed[:10]:
            print(f"  - {f}")
        if len(failed) > 10:
            print(f"  ... and {len(failed) - 10} more")
    
    print()
    print("Output saved to: xml_nkjv_with_woc/")
    print("=" * 80)

if __name__ == '__main__':
    main()
