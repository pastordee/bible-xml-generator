import os
import requests
import xml.etree.ElementTree as ET
import xml.dom.minidom as minidom
import time
import json
import re
from html import unescape

def fetch_bible_metadata(version, api_key):
    """Fetch Bible metadata including copyright information from API.Bible."""
    
    # Map of API.Bible IDs for different versions
    bible_ids = {
        "KJV": "de4e12af7f28f599-02",  # King James (Authorized) Version
        "NKJV": "63097d2a0a2f7db3-01",  # New King James Version ✅ CORRECT ID
        "NIV": "78a9f6124f344018-01",   # New International Version (NOT AVAILABLE via API.Bible)
        "AMP": "a81b73293d3080c9-01",   # Amplified Bible ✅ CORRECT ID
        "NLT": "d6e14a625393b4da-01",   # New Living Translation ✅ PREMIUM ACCESS
        "MSG": "65eec8e0b60e656b-01",   # The Message Bible (may require subscription)
        "WEB": "9879dbb7cfe39e4d-01",   # World English Bible (Free)
        "ASV": "06125adad2d5898a-01",   # American Standard Version (Free)
        "BSB": "bba9f40183526463-01",   # Berean Standard Bible (Free)
        "CEV": "555fef9a6cb31151-01",   # Contemporary English Version (Free)
        "FBV": "65eec8e0b60e656b-01",   # Free Bible Version (Free)
        "GNV": "c315fa9f71d4af3a-01",   # Geneva Bible (Free)
        "DRA": "179568874c45066f-01",   # Douay-Rheims American 1899 (Free)
        "BRS": "6bab4d6c61b31b80-01",   # Brenton English Septuagint (Free)
        "LSV": "01b29f4b342acc35-01"    # Literal Standard Version (Free)
    }
    
    bible_id = bible_ids.get(version)
    if not bible_id:
        return None
    
    url = f"https://rest.api.bible/v1/bibles/{bible_id}"
    headers = {"api-key": api_key}
    
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        data = response.json()
        bible_info = data["data"]
        return {
            "name": bible_info.get("name", ""),
            "abbreviation": bible_info.get("abbreviation", version),
            "copyright": bible_info.get("copyright", ""),
            "description": bible_info.get("description", ""),
            "updated_at": bible_info.get("updatedAt", "")
        }
    else:
        print(f"Error fetching metadata for {version}: {response.status_code}")
        return None

def fetch_api_bible_chapter_content(version, book_abbr, chapter, api_key):
    """Fetch Bible content from API.Bible."""
    
    # Map of API.Bible IDs for different versions
    bible_ids = {
        "KJV": "de4e12af7f28f599-02",  # King James (Authorized) Version
        "NKJV": "63097d2a0a2f7db3-01",  # New King James Version ✅ CORRECT ID
        "NIV": "78a9f6124f344018-01",   # New International Version (NOT AVAILABLE via API.Bible)
        "AMP": "a81b73293d3080c9-01",   # Amplified Bible ✅ CORRECT ID
        "NLT": "d6e14a625393b4da-01",   # New Living Translation ✅ PREMIUM ACCESS
        "MSG": "65eec8e0b60e656b-01",   # The Message Bible (may require subscription)
        "WEB": "9879dbb7cfe39e4d-01",   # World English Bible (Free)
        "ASV": "06125adad2d5898a-01",   # American Standard Version (Free)
        "BSB": "bba9f40183526463-01",   # Berean Standard Bible (Free)
        "CEV": "555fef9a6cb31151-01",   # Contemporary English Version (Free)
        "FBV": "65eec8e0b60e656b-01",   # Free Bible Version (Free)
        "GNV": "c315fa9f71d4af3a-01",   # Geneva Bible (Free)
        "DRA": "179568874c45066f-01",   # Douay-Rheims American 1899 (Free)
        "BRS": "6bab4d6c61b31b80-01",   # Brenton English Septuagint (Free)
        "LSV": "01b29f4b342acc35-01"    # Literal Standard Version (Free)
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
    url = f"https://rest.api.bible/v1/bibles/{bible_id}/chapters/{book_id}.{chapter}"
    
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
        # Convert span verse markers to numbered lines
        content = re.sub(r'<span[^>]*data-number="(\d+)"[^>]*class="v"[^>]*>\d+</span>', r'\n\1 ', content)
        content = re.sub(r'<h3[^>]*>(.*?)</h3>', r'\1\n', content)
        content = re.sub(r'<[^>]+>', '', content)
        content = unescape(content)
        
        return content
    else:
        print(f"Error: API.Bible returned status code {response.status_code}")
        print(f"Response: {response.text}")  # Print full error response
        return None

def create_detailed_chapter_xml(version, book_info, chapter_num, content, bible_metadata=None):
    """Convert chapter content to XML structure matching the target format."""
    
    # Create root elements
    root = ET.Element("bible")
    
    # Add copyright attribution if metadata is available
    if bible_metadata and bible_metadata.get("copyright"):
        copyright_elem = ET.SubElement(root, "copyright")
        copyright_text = bible_metadata["copyright"]
        # Format according to API.Bible Terms of Service requirements
        if "PUBLIC DOMAIN" not in copyright_text.upper():
            formatted_copyright = f"Scripture quotations marked {version} are taken from {bible_metadata.get('name', version)}. {copyright_text}"
        else:
            formatted_copyright = f"{bible_metadata.get('name', version)} - {copyright_text}"
        copyright_elem.text = formatted_copyright
        
        # Add metadata elements
        metadata_elem = ET.SubElement(root, "metadata")
        if bible_metadata.get("name"):
            name_elem = ET.SubElement(metadata_elem, "name")
            name_elem.text = bible_metadata["name"]
        if bible_metadata.get("abbreviation"):
            abbr_elem = ET.SubElement(metadata_elem, "abbreviation")
            abbr_elem.text = bible_metadata["abbreviation"]
        if bible_metadata.get("updated_at"):
            updated_elem = ET.SubElement(metadata_elem, "last_updated")
            updated_elem.text = bible_metadata["updated_at"]
    
    # Add generation info for compliance tracking
    import datetime
    generation_elem = ET.SubElement(root, "generation_info")
    gen_date_elem = ET.SubElement(generation_elem, "generated_date")
    gen_date_elem.text = datetime.datetime.now().isoformat()
    compliance_elem = ET.SubElement(generation_elem, "api_compliance")
    compliance_elem.text = "API.Bible Terms of Service - 30-day refresh requirement"
    next_refresh_elem = ET.SubElement(generation_elem, "next_refresh_due")
    next_refresh_elem.text = (datetime.datetime.now() + datetime.timedelta(days=30)).isoformat()
    
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
    url = "https://rest.api.bible/v1/bibles"
    headers = {"api-key": api_key}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()["data"]
    else:
        print(f"Error fetching Bible versions: {response.status_code}")
        return []

def main():
    # API.Bible API key
    api_bible_key = "pyExkJPN1XXpoJ39Xa8Xi"  # Premium API key with access to NKJV, AMP, NLT
    
    # Versions to process - 11 free versions + 3 premium (NKJV, AMP, NLT). Note: NIV not available via API.Bible
    versions = ["KJV", "WEB", "ASV", "BSB", "CEV", "FBV", "GNV", "DRA", "BRS", "LSV", "MSG", "NKJV", "AMP", "NLT"]
    
    # Complete Bible book information (all 66 books)
    books = [
        # Old Testament
        {"id": 1, "num": 1, "title": "Genesis", "testament": "old", "abbr": "gen"},
        {"id": 2, "num": 2, "title": "Exodus", "testament": "old", "abbr": "exo"},
        {"id": 3, "num": 3, "title": "Leviticus", "testament": "old", "abbr": "lev"},
        {"id": 4, "num": 4, "title": "Numbers", "testament": "old", "abbr": "num"},
        {"id": 5, "num": 5, "title": "Deuteronomy", "testament": "old", "abbr": "deu"},
        {"id": 6, "num": 6, "title": "Joshua", "testament": "old", "abbr": "jos"},
        {"id": 7, "num": 7, "title": "Judges", "testament": "old", "abbr": "jdg"},
        {"id": 8, "num": 8, "title": "Ruth", "testament": "old", "abbr": "rut"},
        {"id": 9, "num": 9, "title": "1 Samuel", "testament": "old", "abbr": "1sa"},
        {"id": 10, "num": 10, "title": "2 Samuel", "testament": "old", "abbr": "2sa"},
        {"id": 11, "num": 11, "title": "1 Kings", "testament": "old", "abbr": "1ki"},
        {"id": 12, "num": 12, "title": "2 Kings", "testament": "old", "abbr": "2ki"},
        {"id": 13, "num": 13, "title": "1 Chronicles", "testament": "old", "abbr": "1ch"},
        {"id": 14, "num": 14, "title": "2 Chronicles", "testament": "old", "abbr": "2ch"},
        {"id": 15, "num": 15, "title": "Ezra", "testament": "old", "abbr": "ezr"},
        {"id": 16, "num": 16, "title": "Nehemiah", "testament": "old", "abbr": "neh"},
        {"id": 17, "num": 17, "title": "Esther", "testament": "old", "abbr": "est"},
        {"id": 18, "num": 18, "title": "Job", "testament": "old", "abbr": "job"},
        {"id": 19, "num": 19, "title": "Psalms", "testament": "old", "abbr": "psa"},
        {"id": 20, "num": 20, "title": "Proverbs", "testament": "old", "abbr": "pro"},
        {"id": 21, "num": 21, "title": "Ecclesiastes", "testament": "old", "abbr": "ecc"},
        {"id": 22, "num": 22, "title": "Song of Solomon", "testament": "old", "abbr": "sng"},
        {"id": 23, "num": 23, "title": "Isaiah", "testament": "old", "abbr": "isa"},
        {"id": 24, "num": 24, "title": "Jeremiah", "testament": "old", "abbr": "jer"},
        {"id": 25, "num": 25, "title": "Lamentations", "testament": "old", "abbr": "lam"},
        {"id": 26, "num": 26, "title": "Ezekiel", "testament": "old", "abbr": "ezk"},
        {"id": 27, "num": 27, "title": "Daniel", "testament": "old", "abbr": "dan"},
        {"id": 28, "num": 28, "title": "Hosea", "testament": "old", "abbr": "hos"},
        {"id": 29, "num": 29, "title": "Joel", "testament": "old", "abbr": "jol"},
        {"id": 30, "num": 30, "title": "Amos", "testament": "old", "abbr": "amo"},
        {"id": 31, "num": 31, "title": "Obadiah", "testament": "old", "abbr": "oba"},
        {"id": 32, "num": 32, "title": "Jonah", "testament": "old", "abbr": "jon"},
        {"id": 33, "num": 33, "title": "Micah", "testament": "old", "abbr": "mic"},
        {"id": 34, "num": 34, "title": "Nahum", "testament": "old", "abbr": "nah"},
        {"id": 35, "num": 35, "title": "Habakkuk", "testament": "old", "abbr": "hab"},
        {"id": 36, "num": 36, "title": "Zephaniah", "testament": "old", "abbr": "zep"},
        {"id": 37, "num": 37, "title": "Haggai", "testament": "old", "abbr": "hag"},
        {"id": 38, "num": 38, "title": "Zechariah", "testament": "old", "abbr": "zec"},
        {"id": 39, "num": 39, "title": "Malachi", "testament": "old", "abbr": "mal"},
        # New Testament
        {"id": 40, "num": 40, "title": "Matthew", "testament": "new", "abbr": "mat"},
        {"id": 41, "num": 41, "title": "Mark", "testament": "new", "abbr": "mrk"},
        {"id": 42, "num": 42, "title": "Luke", "testament": "new", "abbr": "luk"},
        {"id": 43, "num": 43, "title": "John", "testament": "new", "abbr": "jhn"},
        {"id": 44, "num": 44, "title": "Acts", "testament": "new", "abbr": "act"},
        {"id": 45, "num": 45, "title": "Romans", "testament": "new", "abbr": "rom"},
        {"id": 46, "num": 46, "title": "1 Corinthians", "testament": "new", "abbr": "1co"},
        {"id": 47, "num": 47, "title": "2 Corinthians", "testament": "new", "abbr": "2co"},
        {"id": 48, "num": 48, "title": "Galatians", "testament": "new", "abbr": "gal"},
        {"id": 49, "num": 49, "title": "Ephesians", "testament": "new", "abbr": "eph"},
        {"id": 50, "num": 50, "title": "Philippians", "testament": "new", "abbr": "php"},
        {"id": 51, "num": 51, "title": "Colossians", "testament": "new", "abbr": "col"},
        {"id": 52, "num": 52, "title": "1 Thessalonians", "testament": "new", "abbr": "1th"},
        {"id": 53, "num": 53, "title": "2 Thessalonians", "testament": "new", "abbr": "2th"},
        {"id": 54, "num": 54, "title": "1 Timothy", "testament": "new", "abbr": "1ti"},
        {"id": 55, "num": 55, "title": "2 Timothy", "testament": "new", "abbr": "2ti"},
        {"id": 56, "num": 56, "title": "Titus", "testament": "new", "abbr": "tit"},
        {"id": 57, "num": 57, "title": "Philemon", "testament": "new", "abbr": "phm"},
        {"id": 58, "num": 58, "title": "Hebrews", "testament": "new", "abbr": "heb"},
        {"id": 59, "num": 59, "title": "James", "testament": "new", "abbr": "jas"},
        {"id": 60, "num": 60, "title": "1 Peter", "testament": "new", "abbr": "1pe"},
        {"id": 61, "num": 61, "title": "2 Peter", "testament": "new", "abbr": "2pe"},
        {"id": 62, "num": 62, "title": "1 John", "testament": "new", "abbr": "1jn"},
        {"id": 63, "num": 63, "title": "2 John", "testament": "new", "abbr": "2jn"},
        {"id": 64, "num": 64, "title": "3 John", "testament": "new", "abbr": "3jn"},
        {"id": 65, "num": 65, "title": "Jude", "testament": "new", "abbr": "jud"},
        {"id": 66, "num": 66, "title": "Revelation", "testament": "new", "abbr": "rev"}
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
    print("\nAvailable versions:")
    print("FREE: KJV, WEB, ASV, BSB, CEV, FBV, GNV, DRA, BRS, LSV, MSG")
    print("PREMIUM (with subscription): NKJV, AMP, NLT")
    print("NOTE: NIV is not available through API.Bible")
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
        
        # Fetch Bible metadata once per version for copyright compliance
        print(f"\nFetching metadata for {version}...")
        bible_metadata = fetch_bible_metadata(version, api_bible_key)
        if bible_metadata:
            print(f"  {bible_metadata['name']}")
            if bible_metadata['copyright']:
                print(f"  Copyright: {bible_metadata['copyright'][:100]}...")
        
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
                    # Create XML structure with copyright metadata
                    xml_tree = create_detailed_chapter_xml(version, book, chapter_num, content, bible_metadata)
                    
                    # Save to file - use lowercase title instead of abbreviation
                    safe_title = book['title'].lower().replace(' ', '_')
                    output_file = os.path.join(version_dir, f"{safe_title}_{chapter_num}.xml")
                    save_xml_file(xml_tree, output_file)
                    
                    # Be nice to the API - don't hammer it with requests (reduced to 2 seconds)
                    time.sleep(2)
                else:
                    print(f"  Failed to fetch content for {book['title']} {chapter_num}")
        
    print("\nProcess completed.")

    # Use this function to list available Bibles
    bibles = get_available_bibles(api_bible_key)
    for bible in bibles:
        print(f"{bible['name']} - ID: {bible['id']}")

if __name__ == "__main__":
    main()