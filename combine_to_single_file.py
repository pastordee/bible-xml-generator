#!/usr/bin/env python3
"""
Combine all individual chapter XML files for each version into a single
consolidated XML file (e.g., kjv.xml, nkjv.xml, etc.) for easy searching.
Uses the simple format: <bible><b n="BookName"><c n="chapter"><v n="verse">text</v></c></b></bible>
"""

import os
import xml.etree.ElementTree as ET
from pathlib import Path
import re

# Complete Bible book list with chapter counts
BOOKS = [
    # Old Testament
    {"title": "Genesis", "abbr": "gen", "chapters": 50},
    {"title": "Exodus", "abbr": "exo", "chapters": 40},
    {"title": "Leviticus", "abbr": "lev", "chapters": 27},
    {"title": "Numbers", "abbr": "num", "chapters": 36},
    {"title": "Deuteronomy", "abbr": "deu", "chapters": 34},
    {"title": "Joshua", "abbr": "jos", "chapters": 24},
    {"title": "Judges", "abbr": "jdg", "chapters": 21},
    {"title": "Ruth", "abbr": "rut", "chapters": 4},
    {"title": "1 Samuel", "abbr": "1sa", "chapters": 31},
    {"title": "2 Samuel", "abbr": "2sa", "chapters": 24},
    {"title": "1 Kings", "abbr": "1ki", "chapters": 22},
    {"title": "2 Kings", "abbr": "2ki", "chapters": 25},
    {"title": "1 Chronicles", "abbr": "1ch", "chapters": 29},
    {"title": "2 Chronicles", "abbr": "2ch", "chapters": 36},
    {"title": "Ezra", "abbr": "ezr", "chapters": 10},
    {"title": "Nehemiah", "abbr": "neh", "chapters": 13},
    {"title": "Esther", "abbr": "est", "chapters": 10},
    {"title": "Job", "abbr": "job", "chapters": 42},
    {"title": "Psalms", "abbr": "psa", "chapters": 150},
    {"title": "Proverbs", "abbr": "pro", "chapters": 31},
    {"title": "Ecclesiastes", "abbr": "ecc", "chapters": 12},
    {"title": "Song of Solomon", "abbr": "sng", "chapters": 8},
    {"title": "Isaiah", "abbr": "isa", "chapters": 66},
    {"title": "Jeremiah", "abbr": "jer", "chapters": 52},
    {"title": "Lamentations", "abbr": "lam", "chapters": 5},
    {"title": "Ezekiel", "abbr": "ezk", "chapters": 48},
    {"title": "Daniel", "abbr": "dan", "chapters": 12},
    {"title": "Hosea", "abbr": "hos", "chapters": 14},
    {"title": "Joel", "abbr": "jol", "chapters": 3},
    {"title": "Amos", "abbr": "amo", "chapters": 9},
    {"title": "Obadiah", "abbr": "oba", "chapters": 1},
    {"title": "Jonah", "abbr": "jon", "chapters": 4},
    {"title": "Micah", "abbr": "mic", "chapters": 7},
    {"title": "Nahum", "abbr": "nah", "chapters": 3},
    {"title": "Habakkuk", "abbr": "hab", "chapters": 3},
    {"title": "Zephaniah", "abbr": "zep", "chapters": 3},
    {"title": "Haggai", "abbr": "hag", "chapters": 2},
    {"title": "Zechariah", "abbr": "zec", "chapters": 14},
    {"title": "Malachi", "abbr": "mal", "chapters": 4},
    # New Testament
    {"title": "Matthew", "abbr": "mat", "chapters": 28},
    {"title": "Mark", "abbr": "mrk", "chapters": 16},
    {"title": "Luke", "abbr": "luk", "chapters": 24},
    {"title": "John", "abbr": "jhn", "chapters": 21},
    {"title": "Acts", "abbr": "act", "chapters": 28},
    {"title": "Romans", "abbr": "rom", "chapters": 16},
    {"title": "1 Corinthians", "abbr": "1co", "chapters": 16},
    {"title": "2 Corinthians", "abbr": "2co", "chapters": 13},
    {"title": "Galatians", "abbr": "gal", "chapters": 6},
    {"title": "Ephesians", "abbr": "eph", "chapters": 6},
    {"title": "Philippians", "abbr": "php", "chapters": 4},
    {"title": "Colossians", "abbr": "col", "chapters": 4},
    {"title": "1 Thessalonians", "abbr": "1th", "chapters": 5},
    {"title": "2 Thessalonians", "abbr": "2th", "chapters": 3},
    {"title": "1 Timothy", "abbr": "1ti", "chapters": 6},
    {"title": "2 Timothy", "abbr": "2ti", "chapters": 4},
    {"title": "Titus", "abbr": "tit", "chapters": 3},
    {"title": "Philemon", "abbr": "phm", "chapters": 1},
    {"title": "Hebrews", "abbr": "heb", "chapters": 13},
    {"title": "James", "abbr": "jas", "chapters": 5},
    {"title": "1 Peter", "abbr": "1pe", "chapters": 5},
    {"title": "2 Peter", "abbr": "2pe", "chapters": 3},
    {"title": "1 John", "abbr": "1jn", "chapters": 5},
    {"title": "2 John", "abbr": "2jn", "chapters": 1},
    {"title": "3 John", "abbr": "3jn", "chapters": 1},
    {"title": "Jude", "abbr": "jud", "chapters": 1},
    {"title": "Revelation", "abbr": "rev", "chapters": 22}
]


def get_verse_text(v_element):
    """Extract all text content from a verse element, including text in child elements."""
    if v_element.text:
        text = v_element.text
    else:
        text = ""
    
    # Get text from all children (like crossref elements)
    for child in v_element:
        if child.tail:
            text += child.tail
    
    # Clean up whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def combine_version(version_dir, output_filename):
    """Combine all chapter XML files from a version directory into one file."""
    
    version_path = Path(version_dir)
    if not version_path.exists():
        print(f"⚠️  Directory not found: {version_dir}")
        return False
    
    version_name = version_path.name.replace('xml_', '').upper()
    print(f"\n📖 Processing {version_name}...")
    
    # Create root bible element
    root = ET.Element("bible")
    
    books_processed = 0
    chapters_processed = 0
    verses_processed = 0
    missing_chapters = []
    
    for book in BOOKS:
        safe_title = book['title'].lower().replace(' ', '_')
        
        # Create book element
        book_elem = ET.SubElement(root, "b", {"n": book['title']})
        book_has_chapters = False
        
        for chapter_num in range(1, book['chapters'] + 1):
            chapter_file = version_path / f"{safe_title}_{chapter_num}.xml"
            
            if not chapter_file.exists():
                missing_chapters.append(f"{book['title']} {chapter_num}")
                continue
            
            try:
                # Parse the individual chapter file
                tree = ET.parse(chapter_file)
                source_root = tree.getroot()
                
                # Find the chapter element in the source
                # The structure is: <bible><book><chapter>...</chapter></book></bible>
                chapter_source = source_root.find(".//chapter[@num='{}']".format(chapter_num))
                
                if chapter_source is None:
                    print(f"  ⚠️  Could not find chapter element in {chapter_file.name}")
                    continue
                
                # Create chapter element in output
                chapter_elem = ET.SubElement(book_elem, "c", {"n": str(chapter_num)})
                
                # Extract all verses
                verses = chapter_source.findall(".//v[@n]")
                
                for verse in verses:
                    verse_num = verse.get('n')
                    verse_text = get_verse_text(verse)
                    
                    if verse_text:
                        v_elem = ET.SubElement(chapter_elem, "v", {"n": verse_num})
                        v_elem.text = verse_text
                        verses_processed += 1
                
                book_has_chapters = True
                chapters_processed += 1
                
            except Exception as e:
                print(f"  ⚠️  Error processing {chapter_file.name}: {e}")
                continue
        
        if book_has_chapters:
            books_processed += 1
    
    # Write the combined XML file
    output_path = version_path / output_filename
    
    # Create tree and write with proper formatting
    tree = ET.ElementTree(root)
    ET.indent(tree, space="\t", level=0)
    
    with open(output_path, 'wb') as f:
        f.write(b'<?xml version="1.0" encoding="ISO-8859-1"?>\n')
        tree.write(f, encoding='ISO-8859-1', xml_declaration=False)
    
    print(f"✅ Created {output_path}")
    print(f"   📚 Books: {books_processed}/66")
    print(f"   📄 Chapters: {chapters_processed}")
    print(f"   📝 Verses: {verses_processed}")
    
    if missing_chapters:
        print(f"   ⚠️  Missing {len(missing_chapters)} chapters:")
        # Show first 5 missing chapters
        for missing in missing_chapters[:5]:
            print(f"      - {missing}")
        if len(missing_chapters) > 5:
            print(f"      ... and {len(missing_chapters) - 5} more")
    
    return True


def main():
    base_dir = Path(__file__).parent
    
    # Find all xml_* directories
    version_dirs = [d for d in base_dir.iterdir() if d.is_dir() and d.name.startswith('xml_')]
    
    if not version_dirs:
        print("❌ No xml_* directories found!")
        return
    
    print("="*60)
    print("COMBINE CHAPTERS TO SINGLE FILE PER VERSION")
    print("="*60)
    print(f"\nFound {len(version_dirs)} version directories:")
    for d in sorted(version_dirs):
        version_abbr = d.name.replace('xml_', '')
        print(f"  - {version_abbr.upper()}")
    
    print("\n" + "="*60)
    
    # Process each version
    success_count = 0
    for version_dir in sorted(version_dirs):
        version_abbr = version_dir.name.replace('xml_', '')
        output_filename = f"{version_abbr}.xml"
        
        if combine_version(version_dir, output_filename):
            success_count += 1
    
    print("\n" + "="*60)
    print(f"🎉 COMPLETE! Processed {success_count}/{len(version_dirs)} versions")
    print("="*60)


if __name__ == "__main__":
    main()
