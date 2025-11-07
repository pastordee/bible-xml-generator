#!/usr/bin/env python3
"""
ESV Bible Generator with Rate Limiting and Resume Functionality
Handles API rate limits gracefully and can resume from where it left off
"""

import os
import requests
import xml.etree.ElementTree as ET
import xml.dom.minidom as minidom
import time
import re
import json
from datetime import datetime

def get_missing_esv_chapters():
    """
    Identify which ESV chapters are missing and need to be generated.
    Returns a list of (book, chapter) tuples that need to be generated.
    """
    
    # All Bible books with their chapter counts
    all_books = {
        "gen": 50, "exo": 40, "lev": 27, "num": 36, "deu": 34, "jos": 24, "jdg": 21,
        "rut": 4, "1sa": 31, "2sa": 24, "1ki": 22, "2ki": 25, "1ch": 29, "2ch": 36,
        "ezr": 10, "neh": 13, "est": 10, "job": 42, "psa": 150, "pro": 31, "ecc": 12,
        "sng": 8, "isa": 66, "jer": 52, "lam": 5, "ezk": 48, "dan": 12, "hos": 14,
        "jol": 3, "amo": 9, "oba": 1, "jon": 4, "mic": 7, "nah": 3, "hab": 3,
        "zep": 3, "hag": 2, "zec": 14, "mal": 4, "mat": 28, "mrk": 16, "luk": 24,
        "jhn": 21, "act": 28, "rom": 16, "1co": 16, "2co": 13, "gal": 6, "eph": 6,
        "php": 4, "col": 4, "1th": 5, "2th": 3, "1ti": 6, "2ti": 4, "tit": 3,
        "phm": 1, "heb": 13, "jas": 5, "1pe": 5, "2pe": 3, "1jn": 5, "2jn": 1,
        "3jn": 1, "jud": 1, "rev": 22
    }
    
    book_titles = {
        "gen": "Genesis", "exo": "Exodus", "lev": "Leviticus", "num": "Numbers", 
        "deu": "Deuteronomy", "jos": "Joshua", "jdg": "Judges", "rut": "Ruth", 
        "1sa": "1 Samuel", "2sa": "2 Samuel", "1ki": "1 Kings", "2ki": "2 Kings", 
        "1ch": "1 Chronicles", "2ch": "2 Chronicles", "ezr": "Ezra", "neh": "Nehemiah", 
        "est": "Esther", "job": "Job", "psa": "Psalms", "pro": "Proverbs", 
        "ecc": "Ecclesiastes", "sng": "Song of Solomon", "isa": "Isaiah", 
        "jer": "Jeremiah", "lam": "Lamentations", "ezk": "Ezekiel", "dan": "Daniel", 
        "hos": "Hosea", "jol": "Joel", "amo": "Amos", "oba": "Obadiah", "jon": "Jonah", 
        "mic": "Micah", "nah": "Nahum", "hab": "Habakkuk", "zep": "Zephaniah", 
        "hag": "Haggai", "zec": "Zechariah", "mal": "Malachi", "mat": "Matthew", 
        "mrk": "Mark", "luk": "Luke", "jhn": "John", "act": "Acts", "rom": "Romans", 
        "1co": "1 Corinthians", "2co": "2 Corinthians", "gal": "Galatians", 
        "eph": "Ephesians", "php": "Philippians", "col": "Colossians", 
        "1th": "1 Thessalonians", "2th": "2 Thessalonians", "1ti": "1 Timothy", 
        "2ti": "2 Timothy", "tit": "Titus", "phm": "Philemon", "heb": "Hebrews", 
        "jas": "James", "1pe": "1 Peter", "2pe": "2 Peter", "1jn": "1 John", 
        "2jn": "2 John", "3jn": "3 John", "jud": "Jude", "rev": "Revelation"
    }
    
    esv_dir = "esv"
    missing_chapters = []
    
    # Check what's already generated
    existing_files = set()
    if os.path.exists(esv_dir):
        for filename in os.listdir(esv_dir):
            if filename.endswith('.xml'):
                existing_files.add(filename)
    
    # Find missing chapters
    for book_abbr, max_chapters in all_books.items():
        book_title = book_titles[book_abbr]
        
        for chapter in range(1, max_chapters + 1):
            # Convert book title to filename format
            safe_title = book_title.lower().replace(' ', '_')
            expected_filename = f"{safe_title}_{chapter}.xml"
            
            if expected_filename not in existing_files:
                missing_chapters.append((book_abbr, book_title, chapter))
    
    return missing_chapters

def fetch_esv_chapter_with_retry(book_abbr, chapter, api_key, max_retries=3, delay=60):
    """
    Fetch ESV chapter content with retry logic for rate limiting.
    """
    url = f"https://api.esv.org/v3/passage/text/"
    headers = {"Authorization": f"Token {api_key}"}
    params = {
        "q": f"{book_abbr} {chapter}",
        "include-passage-references": "true",
        "include-verse-numbers": "true", 
        "include-footnotes": "true",
        "include-headings": "true",
        "include-subheadings": "true",
        "include-selahs": "true"
    }
    
    for attempt in range(max_retries):
        response = requests.get(url, headers=headers, params=params)
        
        if response.status_code == 200:
            data = response.json()
            return data["passages"][0] if data["passages"] else None
        elif response.status_code == 429:
            if attempt < max_retries - 1:
                print(f"    Rate limited. Waiting {delay} seconds before retry {attempt + 1}/{max_retries}...")
                time.sleep(delay)
                delay *= 2  # Exponential backoff
            else:
                print(f"    Max retries exceeded for {book_abbr} {chapter}")
                return None
        else:
            print(f"    Error: ESV API returned status code {response.status_code}")
            return None
    
    return None

def resume_esv_generation():
    """
    Resume ESV Bible generation from where it left off.
    """
    esv_api_key = "d5b0b4e15b83a9e66c723e6a4bd9f0ab36c30f8c"
    
    # Find missing chapters
    missing_chapters = get_missing_esv_chapters()
    
    if not missing_chapters:
        print("✅ ESV Bible generation is already complete!")
        return
    
    print(f"📚 Found {len(missing_chapters)} chapters to complete ESV Bible generation")
    print(f"Missing chapters span from {missing_chapters[0][1]} {missing_chapters[0][2]} to {missing_chapters[-1][1]} {missing_chapters[-1][2]}")
    
    # Create ESV directory if it doesn't exist
    esv_dir = "esv"
    os.makedirs(esv_dir, exist_ok=True)
    
    # Process missing chapters
    successful = 0
    failed = 0
    
    for i, (book_abbr, book_title, chapter) in enumerate(missing_chapters):
        print(f"\n[{i+1}/{len(missing_chapters)}] Fetching {book_title} chapter {chapter}...")
        
        # Fetch content with retry logic
        content = fetch_esv_chapter_with_retry(book_abbr, chapter, esv_api_key)
        
        if content:
            # Create the XML (reusing existing function structure)
            book_info = {"title": book_title, "abbr": book_abbr}
            
            try:
                # Import the existing XML creation function
                import sys
                sys.path.append('.')
                from create_esv_version_chapters import create_detailed_chapter_xml, save_xml_file
                
                xml_tree = create_detailed_chapter_xml(book_info, chapter, content)
                
                # Save file
                safe_title = book_title.lower().replace(' ', '_')
                output_file = os.path.join(esv_dir, f"{safe_title}_{chapter}.xml")
                save_xml_file(xml_tree, output_file)
                
                print(f"    ✅ Saved: {safe_title}_{chapter}.xml")
                successful += 1
                
                # Short delay to be respectful to the API
                time.sleep(2)
                
            except Exception as e:
                print(f"    ❌ Error processing {book_title} {chapter}: {e}")
                failed += 1
        else:
            print(f"    ❌ Failed to fetch {book_title} {chapter}")
            failed += 1
            
            # If we hit rate limits, suggest waiting
            if failed >= 3:
                print(f"\n⚠️  Multiple failures detected. ESV API may be rate limiting.")
                print(f"   Successfully completed: {successful} chapters")
                print(f"   Failed: {failed} chapters")
                print(f"   Remaining: {len(missing_chapters) - i - 1} chapters")
                print(f"\n💡 Suggestion: Wait 1-24 hours and run this script again to continue from where it left off.")
                break
    
    print(f"\n📊 ESV Generation Summary:")
    print(f"   ✅ Successfully completed: {successful} chapters")
    print(f"   ❌ Failed: {failed} chapters")
    
    # Check if complete
    remaining = get_missing_esv_chapters()
    if not remaining:
        print(f"   🎉 ESV Bible generation is now COMPLETE!")
    else:
        print(f"   📝 {len(remaining)} chapters still need to be generated")

if __name__ == "__main__":
    resume_esv_generation()