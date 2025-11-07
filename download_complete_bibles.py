#!/usr/bin/env python3
"""
Download complete Bibles from API.Bible using the passages endpoint.
Creates a single consolidated XML file per version (e.g., kjv.xml, nkjv.xml).
Format: <bible><b n="BookName"><c n="chapter"><v n="verse">text</v></c></b></bible>
"""

import os
import requests
import xml.etree.ElementTree as ET
import re
from html import unescape
import time

API_KEY = "pyExkJPN1XXpoJ39Xa8Xi"

# Bible IDs for each version
BIBLE_IDS = {
    "KJV": "de4e12af7f28f599-02",
    "NKJV": "63097d2a0a2f7db3-01",
    "AMP": "a81b73293d3080c9-01",
    "NLT": "d6e14a625393b4da-01",
    "MSG": "65eec8e0b60e656b-01",
    "WEB": "9879dbb7cfe39e4d-01",
    "ASV": "06125adad2d5898a-01",
    "BSB": "bba9f40183526463-01",
    "CEV": "555fef9a6cb31151-01",
    "BBE": "965abad449929a23-01",  # Bible in Basic English
}

# All Bible books in order
BOOKS = [
    {"id": "GEN", "name": "Genesis"},
    {"id": "EXO", "name": "Exodus"},
    {"id": "LEV", "name": "Leviticus"},
    {"id": "NUM", "name": "Numbers"},
    {"id": "DEU", "name": "Deuteronomy"},
    {"id": "JOS", "name": "Joshua"},
    {"id": "JDG", "name": "Judges"},
    {"id": "RUT", "name": "Ruth"},
    {"id": "1SA", "name": "1 Samuel"},
    {"id": "2SA", "name": "2 Samuel"},
    {"id": "1KI", "name": "1 Kings"},
    {"id": "2KI", "name": "2 Kings"},
    {"id": "1CH", "name": "1 Chronicles"},
    {"id": "2CH", "name": "2 Chronicles"},
    {"id": "EZR", "name": "Ezra"},
    {"id": "NEH", "name": "Nehemiah"},
    {"id": "EST", "name": "Esther"},
    {"id": "JOB", "name": "Job"},
    {"id": "PSA", "name": "Psalms"},
    {"id": "PRO", "name": "Proverbs"},
    {"id": "ECC", "name": "Ecclesiastes"},
    {"id": "SNG", "name": "Song of Solomon"},
    {"id": "ISA", "name": "Isaiah"},
    {"id": "JER", "name": "Jeremiah"},
    {"id": "LAM", "name": "Lamentations"},
    {"id": "EZK", "name": "Ezekiel"},
    {"id": "DAN", "name": "Daniel"},
    {"id": "HOS", "name": "Hosea"},
    {"id": "JOL", "name": "Joel"},
    {"id": "AMO", "name": "Amos"},
    {"id": "OBA", "name": "Obadiah"},
    {"id": "JON", "name": "Jonah"},
    {"id": "MIC", "name": "Micah"},
    {"id": "NAH", "name": "Nahum"},
    {"id": "HAB", "name": "Habakkuk"},
    {"id": "ZEP", "name": "Zephaniah"},
    {"id": "HAG", "name": "Haggai"},
    {"id": "ZEC", "name": "Zechariah"},
    {"id": "MAL", "name": "Malachi"},
    {"id": "MAT", "name": "Matthew"},
    {"id": "MRK", "name": "Mark"},
    {"id": "LUK", "name": "Luke"},
    {"id": "JHN", "name": "John"},
    {"id": "ACT", "name": "Acts"},
    {"id": "ROM", "name": "Romans"},
    {"id": "1CO", "name": "1 Corinthians"},
    {"id": "2CO", "name": "2 Corinthians"},
    {"id": "GAL", "name": "Galatians"},
    {"id": "EPH", "name": "Ephesians"},
    {"id": "PHP", "name": "Philippians"},
    {"id": "COL", "name": "Colossians"},
    {"id": "1TH", "name": "1 Thessalonians"},
    {"id": "2TH", "name": "2 Thessalonians"},
    {"id": "1TI", "name": "1 Timothy"},
    {"id": "2TI", "name": "2 Timothy"},
    {"id": "TIT", "name": "Titus"},
    {"id": "PHM", "name": "Philemon"},
    {"id": "HEB", "name": "Hebrews"},
    {"id": "JAS", "name": "James"},
    {"id": "1PE", "name": "1 Peter"},
    {"id": "2PE", "name": "2 Peter"},
    {"id": "1JN", "name": "1 John"},
    {"id": "2JN", "name": "2 John"},
    {"id": "3JN", "name": "3 John"},
    {"id": "JUD", "name": "Jude"},
    {"id": "REV", "name": "Revelation"},
]


def fetch_book_content(bible_id, book_id):
    """Fetch entire book content from API.Bible using passages endpoint."""
    url = f"https://rest.api.bible/v1/bibles/{bible_id}/passages/{book_id}"
    headers = {"api-key": API_KEY}
    
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        data = response.json()
        return data["data"]["content"]
    else:
        return None


def parse_html_to_structured_xml(html_content, book_name):
    """Parse HTML content from API into structured XML."""
    # Remove HTML tags but preserve verse markers
    # Verse markers look like: <span data-number="1" data-sid="GEN 1:1" class="v">1</span>
    
    book_elem = ET.Element("b", {"n": book_name})
    
    # Split by chapter markers or paragraphs
    # The content has verse markers with data-sid like "GEN 1:1" (book chapter:verse)
    
    # Extract verses with their chapter and verse numbers
    verse_pattern = r'<span[^>]*data-number="(\d+)"[^>]*data-sid="[A-Z0-9]+ (\d+):(\d+)"[^>]*class="v"[^>]*>\d+</span>(.*?)(?=<span[^>]*data-number=|$)'
    
    verses = re.findall(verse_pattern, html_content, re.DOTALL)
    
    if not verses:
        # Try alternative pattern without data-sid
        verse_pattern = r'<span[^>]*data-number="(\d+)"[^>]*class="v"[^>]*>\d+</span>(.*?)(?=<span[^>]*data-number=|$)'
        verses_alt = re.findall(verse_pattern, html_content, re.DOTALL)
        
        if verses_alt:
            # Need to figure out chapters from context
            current_chapter = 1
            chapter_elem = ET.SubElement(book_elem, "c", {"n": str(current_chapter)})
            
            for verse_num, verse_text in verses_alt:
                # Clean text
                text = re.sub(r'<[^>]+>', '', verse_text)
                text = unescape(text).strip()
                
                if text:
                    v_elem = ET.SubElement(chapter_elem, "v", {"n": verse_num})
                    v_elem.text = text
        
        return book_elem
    
    # Group verses by chapter
    current_chapter = None
    chapter_elem = None
    
    for verse_data in verses:
        if len(verse_data) == 4:
            verse_num, chapter_num, verse_num2, verse_text = verse_data
            chapter_num = chapter_num
        else:
            continue
        
        # Create new chapter element if needed
        if chapter_num != current_chapter:
            current_chapter = chapter_num
            chapter_elem = ET.SubElement(book_elem, "c", {"n": chapter_num})
        
        # Clean verse text
        text = re.sub(r'<[^>]+>', '', verse_text)
        text = unescape(text).strip()
        
        if text and chapter_elem is not None:
            v_elem = ET.SubElement(chapter_elem, "v", {"n": verse_num})
            v_elem.text = text
    
    return book_elem


def download_complete_bible(version, bible_id, output_dir):
    """Download complete Bible for a version and save as single XML file."""
    
    print(f"\n{'='*60}")
    print(f"📖 Downloading {version}")
    print(f"{'='*60}")
    
    # Create root element
    root = ET.Element("bible")
    
    books_downloaded = 0
    books_failed = []
    
    for book in BOOKS:
        print(f"  📥 {book['name']}...", end='', flush=True)
        
        content = fetch_book_content(bible_id, book['id'])
        
        if content:
            # Parse HTML content to structured XML
            book_elem = parse_html_to_structured_xml(content, book['name'])
            
            # Count chapters and verses
            chapters = book_elem.findall('.//c')
            verses = book_elem.findall('.//v')
            
            if len(verses) > 0:
                root.append(book_elem)
                print(f" ✅ ({len(chapters)} ch, {len(verses)} v)")
                books_downloaded += 1
            else:
                print(f" ⚠️  No verses extracted")
                books_failed.append(book['name'])
        else:
            print(f" ❌ Failed to fetch")
            books_failed.append(book['name'])
        
        # Be nice to the API
        time.sleep(0.5)
    
    # Save to file
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, f"{version.lower()}.xml")
    
    tree = ET.ElementTree(root)
    ET.indent(tree, space="\t", level=0)
    
    with open(output_file, 'wb') as f:
        f.write(b'<?xml version="1.0" encoding="ISO-8859-1"?>\n')
        tree.write(f, encoding='ISO-8859-1', xml_declaration=False)
    
    print(f"\n✅ Saved to: {output_file}")
    print(f"   📚 Books: {books_downloaded}/66")
    
    if books_failed:
        print(f"   ⚠️  Failed: {', '.join(books_failed)}")
    
    return books_downloaded == 66


def main():
    print("="*60)
    print("DOWNLOAD COMPLETE BIBLES FROM API.BIBLE")
    print("="*60)
    
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Ask which versions to download
    print("\nAvailable versions:")
    for i, (version, bible_id) in enumerate(BIBLE_IDS.items(), 1):
        print(f"  {i}. {version}")
    
    choice = input("\nEnter versions to download (comma-separated, or 'all'): ").strip()
    
    if choice.lower() == 'all':
        versions_to_download = list(BIBLE_IDS.keys())
    else:
        versions_to_download = [v.strip().upper() for v in choice.split(',')]
        versions_to_download = [v for v in versions_to_download if v in BIBLE_IDS]
    
    if not versions_to_download:
        print("No valid versions selected!")
        return
    
    print(f"\nWill download: {', '.join(versions_to_download)}")
    
    # Download each version
    success_count = 0
    for version in versions_to_download:
        bible_id = BIBLE_IDS[version]
        output_dir = os.path.join(base_dir, f"xml_{version.lower()}")
        
        if download_complete_bible(version, bible_id, output_dir):
            success_count += 1
    
    print("\n" + "="*60)
    print(f"🎉 COMPLETE! {success_count}/{len(versions_to_download)} versions downloaded successfully")
    print("="*60)


if __name__ == "__main__":
    main()
