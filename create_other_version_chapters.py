import os
import requests
import xml.etree.ElementTree as ET
import xml.dom.minidom as minidom
import time
import json
import re
from html import unescape

def fetch_api_bible_chapter_content(version, book_abbr, chapter, api_key):
    """Fetch Bible content from API.Bible."""
    
    # Map of API.Bible IDs for different versions
    bible_ids = {
        "KJV": "de4e12af7f28f599-02",  # King James (Authorized) Version
        "NKJV": "19d8628a61a1936c-01", # New King James Version
        "NIV": "78a9f6124f344018-01",  # New International Version
        "AMP": "08a79c72d7abd6e8-01",  # Amplified Bible
        "MSG": "65eec8e0b60e656b-01"   # The Message Bible
    }
    
    bible_id = bible_ids.get(version)
    if not bible_id:
        print(f"Error: No Bible ID configured for version {version}")
        return None
    
    # API.Bible uses standardized book IDs, not abbreviations
    # This mapping converts your abbreviations to API.Bible IDs
    api_bible_books = {
        "gen": "GEN", "exo": "EXO", "lev": "LEV", "num": "NUM", "deu": "DEU",
        "jos": "JOS", "jdg": "JDG", "rut": "RUT", "1sa": "1SA", "2sa": "2SA",
        "1ki": "1KI", "2ki": "2KI", "1ch": "1CH", "2ch": "2CH", "ezr": "EZR",
        "neh": "NEH", "est": "EST", "job": "JOB", "psa": "PSA", "pro": "PRO",
        "ecc": "ECC", "sng": "SNG", "isa": "ISA", "jer": "JER", "lam": "LAM",
        "ezk": "EZK", "dan": "DAN", "hos": "HOS", "jol": "JOL", "amo": "AMO",
        "oba": "OBA", "jon": "JON", "mic": "MIC", "nah": "NAH", "hab": "HAB",
        "zep": "ZEP", "hag": "HAG", "zec": "ZEC", "mal": "MAL", "mat": "MAT",
        "mrk": "MRK", "luk": "LUK", "jhn": "JHN", "act": "ACT", "rom": "ROM",
        "1co": "1CO", "2co": "2CO", "gal": "GAL", "eph": "EPH", "php": "PHP",
        "col": "COL", "1th": "1TH", "2th": "2TH", "1ti": "1TI", "2ti": "2TI",
        "tit": "TIT", "phm": "PHM", "heb": "HEB", "jas": "JAS", "1pe": "1PE",
        "2pe": "2PE", "1jn": "1JN", "2jn": "2JN", "3jn": "3JN", "jud": "JUD",
        "rev": "REV"
    }
    
    # Get the proper book ID for API.Bible
    book_id = api_bible_books.get(book_abbr.lower())
    if not book_id:
        print(f"Error: No API.Bible book ID found for '{book_abbr}'")
        return None
    
    # IMPORTANT: API.Bible uses a different URL format than what you're using
    # The correct format is /bibles/{bibleId}/chapters/{bookId}.{chapter}
    url = f"https://api.scripture.api.bible/v1/bibles/{bible_id}/chapters/{book_id}.{chapter}"
    
    headers = {
        "api-key": api_key
    }
    
    # Debug info to see what's being requested
    print(f"  Requesting URL: {url}")
    
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        data = response.json()
        content = data["data"]["content"]
        
        # API.Bible returns HTML content that needs to be parsed
        # Remove HTML tags but keep verse numbers
        content = re.sub(r'<span data-number="(\d+)" class="v">(\d+)</span>', r'\1 ', content)
        content = re.sub(r'<h3[^>]*>(.*?)</h3>', r'\1\n', content)
        content = re.sub(r'<[^>]+>', '', content)
        content = unescape(content)
        
        return content
    else:
        print(f"Error: API.Bible returned status code {response.status_code}")
        print(f"Response: {response.text}")  # Print full error response
        return None

def create_detailed_chapter_xml(version, book_info, chapter_num, content):
    """Convert chapter content to XML structure matching the target format."""
    
    # Create root elements
    root = ET.Element("bible", {"version": version})
    
    # Create book element with attributes
    book = ET.SubElement(root, "book", {
        "title": book_info["title"],
        "num": str(book_info["num"]),
        "testament": book_info["testament"],
        "version": version,
        "bookAbbr": book_info["abbr"]
    })
    
    # Add initial verse marker - this goes BEFORE the chapter element
    first_verse_id = f"v{book_info['id']:02d}{chapter_num:03d}001"
    marker = ET.SubElement(book, "marker", {"class": "begin-verse", "mid": first_verse_id})
    
    # Create chapter element
    chapter = ET.SubElement(book, "chapter", {"num": str(chapter_num)})
    
    # Process content
    lines = content.strip().split('\n')
    verse_pattern = re.compile(r'^(\d+)\s+(.*?)$')
    has_heading = False
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # Check if this is a heading (no digits at start)
        if not line[0].isdigit():
            # Add heading element
            heading = ET.SubElement(chapter, "heading")
            heading.text = line
            
            # Add paragraph marker after heading
            begin_para = ET.SubElement(chapter, "begin-paragraph")
            has_heading = True
            continue
        
        # If no heading was found yet, add a paragraph marker
        if not has_heading:
            begin_para = ET.SubElement(chapter, "begin-paragraph")
            has_heading = True  # Prevent adding more paragraph markers
        
        # Process verse content
        match = verse_pattern.match(line)
        if match:
            verse_num = match.group(1)
            verse_text = match.group(2)
            
            # Add verse element
            v = ET.SubElement(chapter, "v", {"n": verse_num})
            
            # Simulate cross references and formatting based on patterns
            # This is simplified - real cross references would come from a database
            words = verse_text.split()
            if len(words) > 3:
                # Insert a crossref after the first few words for demonstration
                v.text = " ".join(words[:2]) + " "
                
                # Crossref with proper attributes
                crossref_id = f"c{book_info['id']:02d}{chapter_num:03d}{verse_num}.1"
                crossref = ET.SubElement(v, "crossref", {
                    "let": chr(97 + (int(verse_num) % 26)),  # a-z based on verse number
                    "cid": crossref_id
                })
                
                # Rest of text follows the crossref
                crossref.tail = " " + " ".join(words[2:])
            else:
                v.text = verse_text
            
            # Add verse marker for next verse
            next_verse_num = int(verse_num) + 1
            next_verse_id = f"v{book_info['id']:02d}{chapter_num:03d}{next_verse_num:03d}"
            next_marker = ET.SubElement(chapter, "marker", {"class": "begin-verse", "mid": next_verse_id})
    
    # Add final paragraph marker
    end_para = ET.SubElement(chapter, "end-paragraph")
    
    return ET.ElementTree(root)

def save_xml_file(tree, output_path):
    """Save XML tree to file with pretty formatting."""
    rough_string = ET.tostring(tree.getroot(), encoding='utf-8')
    reparsed = minidom.parseString(rough_string)
    
    with open(output_path, "w", encoding='utf-8') as f:
        # Write XML declaration
        f.write('<?xml version="1.0" encoding="utf-8"?>\n')
        
        # Format with proper indentation and empty tags
        lines = reparsed.toprettyxml(indent="\t").split('\n')[1:]  # Skip XML declaration
        for line in lines:
            f.write(line + '\n')
            
    print(f"  Saved: {os.path.basename(output_path)}")

def get_available_bibles(api_key):
    url = "https://api.scripture.api.bible/v1/bibles"
    headers = {"api-key": api_key}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()["data"]
    else:
        print(f"Error fetching Bible versions: {response.status_code}")
        return []

def main():
    # API.Bible API key
    api_bible_key = "8c29820374c66aa96f914a9376b808e2"
    
    # Versions to process
    versions = ["KJV", "NIV", "NKJV", "AMP", 'MSG']
    
    # Complete Bible book information
    books = [
        # Old Testament
        {"id": 1, "num": 1, "title": "Genesis", "testament": "old", "abbr": "gen"},
        {"id": 2, "num": 2, "title": "Exodus", "testament": "old", "abbr": "exo"},
        # New Testament
        {"id": 40, "num": 40, "title": "Matthew", "testament": "new", "abbr": "mat"},
        {"id": 41, "num": 41, "title": "Mark", "testament": "new", "abbr": "mrk"},
        {"id": 42, "num": 42, "title": "Luke", "testament": "new", "abbr": "luk"},
        {"id": 43, "num": 43, "title": "John", "testament": "new", "abbr": "jhn"},
        {"id": 44, "num": 44, "title": "Acts", "testament": "new", "abbr": "act"},
        {"id": 45, "num": 45, "title": "Romans", "testament": "new", "abbr": "rom"},
        # ... more books
    ]
    
    # For testing with a smaller subset
    test_books = [
        {"id": 45, "num": 45, "title": "Romans", "testament": "new", "abbr": "rom"},
        {"id": 44, "num": 44, "title": "Acts", "testament": "new", "abbr": "act"},
    ]
    
    # Chapter counts for each book
    chapter_counts = {
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
    
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Ask user which books to process
    print("Available options:")
    print("1. Process test books (Romans and Acts)")
    print("2. Process full Bible (all 66 books)")
    print("3. Process specific book")
    
    choice = input("Enter choice (1-3): ")
    
    if choice == "1":
        selected_books = test_books
    elif choice == "2":
        selected_books = books
    elif choice == "3":
        book_abbr = input("Enter book abbreviation (e.g., 'rom', 'jhn'): ").lower()
        for book in books:
            if book['abbr'] == book_abbr:
                selected_books = [book]
                break
        else:
            print(f"Book '{book_abbr}' not found. Using test books instead.")
            selected_books = test_books
    else:
        print("Invalid choice. Using test books.")
        selected_books = test_books
    
    # Ask user which versions to process
    print("\nAvailable versions: KJV, NIV, NKJV, AMP")
    selected_versions = input("Enter versions to process (comma-separated, or 'all'): ")
    if selected_versions.lower() == 'all':
        selected_versions = versions
    else:
        selected_versions = [v.strip().upper() for v in selected_versions.split(',')]
        # Filter to only valid versions
        selected_versions = [v for v in selected_versions if v in versions]
        
    if not selected_versions:
        print("No valid versions selected. Using KJV.")
        selected_versions = ["KJV"]
    
    print(f"\nProcessing versions: {', '.join(selected_versions)}")
    print(f"Processing books: {', '.join(book['title'] for book in selected_books)}")
    
    for version in selected_versions:
        # Create version directory
        version_dir = os.path.join(base_dir, version.lower())
        os.makedirs(version_dir, exist_ok=True)
        
        for book in selected_books:
            print(f"\nProcessing {book['title']} for {version}...")
            
            # Get number of chapters for this book
            max_chapters = chapter_counts.get(book['abbr'], 1)
            
            # Process each chapter
            for chapter_num in range(1, max_chapters + 1):
                print(f"  Fetching {book['title']} chapter {chapter_num}...")
                
                # Fetch chapter content from API
                content = fetch_api_bible_chapter_content(version, book['abbr'], chapter_num, api_bible_key)
                
                if content:
                    # Create XML structure using the updated detailed function
                    xml_tree = create_detailed_chapter_xml(version, book, chapter_num, content)
                    
                    # Save to file - use lowercase title instead of abbreviation
                    safe_title = book['title'].lower().replace(' ', '_')
                    output_file = os.path.join(version_dir, f"{safe_title}_{chapter_num}.xml")
                    save_xml_file(xml_tree, output_file)
                    
                    # Be nice to the API - don't hammer it with requests
                    time.sleep(5)
                else:
                    print(f"  Failed to fetch content for {book['title']} {chapter_num}")
        
    print("\nProcess completed.")

    # Use this function to list available Bibles
    bibles = get_available_bibles(api_bible_key)
    for bible in bibles:
        print(f"{bible['name']} - ID: {bible['id']}")

if __name__ == "__main__":
    main()