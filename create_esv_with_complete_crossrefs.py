#!/usr/bin/env python3
"""
Enhanced ESV Chapter Generator with Complete Cross-Reference Integration
Downloads ESV content from API and merges with comprehensive cross-reference data.
"""

import os
import requests
import xml.etree.ElementTree as ET
import xml.dom.minidom as minidom
import time
import re
from pathlib import Path
from collections import defaultdict
import datetime


# ESV API Configuration
ESV_API_KEY = "635f6f76a32703e82f372ce2f26a99db76896e07"
ESV_API_URL = "https://api.esv.org/v3/passage/html/"


# Book information
BOOKS = [
    {"num": 1, "title": "Genesis", "abbr": "gen", "id": 1, "testament": "old", "chapters": 50},
    {"num": 2, "title": "Exodus", "abbr": "exo", "id": 2, "testament": "old", "chapters": 40},
    # ... (abbreviated for space - full list needed in production)
    {"num": 43, "title": "John", "abbr": "jhn", "id": 43, "testament": "new", "chapters": 21},
    # Add all 66 books here
]


def parse_crossref_data_file(file_path):
    """Parse a cross-reference data file and return structured data by verse."""
    crossrefs = defaultdict(list)
    
    if not file_path.exists():
        return crossrefs
    
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    current_verse = None
    current_ref = {}
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        if line.startswith('V '):
            if current_verse and current_ref:
                crossrefs[current_verse].append(current_ref)
            
            verse_id = line.split()[1]
            current_verse = verse_id
            current_ref = {}
        
        elif line.startswith('c '):
            if current_ref:
                crossrefs[current_verse].append(current_ref)
            current_ref = {'letter': line.split()[1]}
        
        elif line.startswith('i '):
            current_ref['cid'] = line.split()[1]
    
    if current_verse and current_ref:
        crossrefs[current_verse].append(current_ref)
    
    return crossrefs


def fetch_esv_chapter_html(book_abbr, chapter):
    """Fetch ESV chapter content from API."""
    headers = {"Authorization": f"Token {ESV_API_KEY}"}
    params = {
        "q": f"{book_abbr} {chapter}",
        "include-passage-references": "false",
        "include-verse-numbers": "true",
        "include-footnotes": "true",
        "include-footnote-body": "true",
        "include-headings": "true",
        "include-short-copyright": "false",
        "include-copyright": "false",
        "include-selahs": "true",
        "line-length": "0"
    }
    
    try:
        response = requests.get(ESV_API_URL, headers=headers, params=params)
        if response.status_code == 200:
            data = response.json()
            return data["passages"][0] if data["passages"] else None
        else:
            print(f"    ❌ API error {response.status_code}: {response.text}")
            return None
    except Exception as e:
        print(f"    ❌ Exception: {e}")
        return None


def create_chapter_xml_with_complete_crossrefs(book_info, chapter_num, html_content, crossref_data):
    """Create XML with complete cross-references from data file."""
    
    # Create root structure
    root = ET.Element("bible")
    
    # Add copyright
    copyright_elem = ET.SubElement(root, "copyright")
    copyright_elem.text = "Scripture quotations marked ESV are taken from The Holy Bible, English Standard Version. ESV® Text Edition: 2016. Copyright © 2001 by Crossway Bibles, a publishing ministry of Good News Publishers."
    
    # Add metadata
    metadata = ET.SubElement(root, "metadata")
    ET.SubElement(metadata, "name").text = "English Standard Version"
    ET.SubElement(metadata, "abbreviation").text = "ESV"
    ET.SubElement(metadata, "source_api").text = "Crossway ESV API"
    
    # Add generation info
    generation = ET.SubElement(root, "generation_info")
    ET.SubElement(generation, "generated_date").text = datetime.datetime.now().isoformat()
    ET.SubElement(generation, "api_compliance").text = "ESV API Terms - Content freshness requirement"
    ET.SubElement(generation, "next_refresh_due").text = (datetime.datetime.now() + datetime.timedelta(days=30)).isoformat()
    
    # Create book element
    book = ET.SubElement(root, "book", {
        "title": book_info["title"],
        "num": str(book_info["num"]),
        "testament": book_info["testament"],
        "bookAbbr": book_info["abbr"],
        "version": "ESV"
    })
    
    # Add initial verse marker
    first_verse_id = f"v{book_info['id']:02d}{chapter_num:03d}001"
    ET.SubElement(book, "marker", {"class": "begin-verse", "mid": first_verse_id}).text = "\n\t\t"
    
    # Create chapter
    chapter = ET.SubElement(book, "chapter", {"num": str(chapter_num)})
    
    # Parse HTML content to extract verses
    # Remove HTML tags but preserve structure
    text_content = re.sub(r'<[^>]+>', ' ', html_content)
    text_content = re.sub(r'\s+', ' ', text_content).strip()
    
    # Split by verse numbers [1], [2], etc.
    verse_pattern = r'\[(\d+)\]'
    parts = re.split(verse_pattern, text_content)
    
    # Add chapter heading
    ET.SubElement(chapter, "heading").text = f"\n\t\t\t\t{book_info['title']} {chapter_num}\n\t\t\t"
    ET.SubElement(chapter, "begin-paragraph").text = "\n\t\t\t"
    
    # Process verses
    for i in range(1, len(parts), 2):
        if i + 1 >= len(parts):
            break
        
        verse_num = parts[i]
        verse_text = parts[i + 1].strip()
        
        if not verse_text:
            continue
        
        # Create verse element
        verse_elem = ET.SubElement(chapter, "v", {"n": verse_num})
        
        # Get cross-references for this verse from data
        verse_id = f"{book_info['id']:02d}{chapter_num:03d}{int(verse_num):03d}"
        verse_crossrefs = crossref_data.get(verse_id, [])
        
        # Add verse content with cross-references
        # For now, insert crossrefs at regular intervals in the text
        words = verse_text.split()
        crossref_idx = 0
        words_per_crossref = max(1, len(words) // (len(verse_crossrefs) + 1)) if verse_crossrefs else len(words)
        
        current_text = ""
        for word_idx, word in enumerate(words):
            current_text += word + " "
            
            # Insert cross-reference at intervals
            if crossref_idx < len(verse_crossrefs) and (word_idx + 1) % words_per_crossref == 0:
                if not verse_elem.text:
                    verse_elem.text = current_text
                else:
                    # Add to tail of last child
                    if len(verse_elem):
                        verse_elem[-1].tail = (verse_elem[-1].tail or "") + current_text
                    else:
                        verse_elem.text += current_text
                
                # Add crossref element
                ref_data = verse_crossrefs[crossref_idx]
                crossref = ET.SubElement(verse_elem, "crossref", {
                    "let": ref_data['letter'],
                    "cid": ref_data['cid']
                })
                crossref.text = "\n\t\t\t\t"
                crossref.tail = "\n\t\t\t\t"
                
                current_text = ""
                crossref_idx += 1
        
        # Add remaining text
        if current_text:
            if not verse_elem.text and not len(verse_elem):
                verse_elem.text = current_text
            elif len(verse_elem):
                verse_elem[-1].tail = (verse_elem[-1].tail or "") + current_text
            else:
                verse_elem.text = (verse_elem.text or "") + current_text
        
        # Add marker for next verse
        next_verse_num = int(verse_num) + 1
        next_verse_id = f"v{book_info['id']:02d}{chapter_num:03d}{next_verse_num:03d}"
        ET.SubElement(chapter, "marker", {"class": "begin-verse", "mid": next_verse_id}).text = "\n\t\t\t"
    
    ET.SubElement(chapter, "end-paragraph").text = "\n\t\t\t"
    
    return ET.ElementTree(root)


def generate_chapter(book_info, chapter_num, output_dir, crossref_base_dir):
    """Generate a single chapter with complete cross-references."""
    
    book_name = book_info['title'].lower().replace(' ', '_')
    output_file = output_dir / f"{book_name}_{chapter_num}.xml"
    
    # Check if file exists
    if output_file.exists():
        print(f"  ⏭️  Skipping {book_name} {chapter_num} (already exists)")
        return True
    
    # Get cross-reference data
    crossref_file = crossref_base_dir / book_name / f"{chapter_num}.txt"
    crossref_data = parse_crossref_data_file(crossref_file)
    
    # Fetch from API
    print(f"  📥 Downloading {book_info['title']} {chapter_num}...")
    html_content = fetch_esv_chapter_html(book_info['abbr'], chapter_num)
    
    if not html_content:
        print(f"  ❌ Failed to download {book_info['title']} {chapter_num}")
        return False
    
    # Create XML with cross-references
    tree = create_chapter_xml_with_complete_crossrefs(book_info, chapter_num, html_content, crossref_data)
    
    # Pretty print and save
    xml_str = ET.tostring(tree.getroot(), encoding='utf-8')
    dom = minidom.parseString(xml_str)
    pretty_xml = dom.toprettyxml(indent="\t", encoding='utf-8')
    
    with open(output_file, 'wb') as f:
        f.write(pretty_xml)
    
    print(f"  ✅ Created {book_name}_{chapter_num}.xml with {sum(len(refs) for refs in crossref_data.values())} crossrefs")
    
    # Rate limiting
    time.sleep(0.5)
    return True


def main():
    """Main execution."""
    base_dir = Path(__file__).parent
    output_dir = base_dir / "xml_esv_complete"
    crossref_base_dir = base_dir / "raw" / "cross_refs"
    
    output_dir.mkdir(exist_ok=True)
    
    print("="*80)
    print("ESV BIBLE GENERATOR WITH COMPLETE CROSS-REFERENCES")
    print("="*80)
    print(f"\nOutput directory: {output_dir}")
    print(f"Cross-reference data: {crossref_base_dir}\n")
    
    # For testing, just do John chapter 3
    john_book = {"num": 43, "title": "John", "abbr": "jhn", "id": 43, "testament": "new", "chapters": 21}
    
    print("Generating John 3 as test...")
    generate_chapter(john_book, 3, output_dir, crossref_base_dir)
    
    print("\n" + "="*80)
    print("✅ GENERATION COMPLETE")
    print("="*80)


if __name__ == "__main__":
    main()
