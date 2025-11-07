import os
import requests
import xml.etree.ElementTree as ET
import xml.dom.minidom as minidom
import time
import json

def fetch_chapter_content(version, book_abbr, chapter, api_keys):
    """Fetch Bible content from appropriate API based on version."""
    
    if version == "ESV":
        # ESV API (https://api.esv.org/)
        url = f"https://api.esv.org/v3/passage/text/"
        headers = {
            "Authorization": f"Token {api_keys['esv']}"
        }
        params = {
            "q": f"{book_abbr} {chapter}",
            "include-passage-references": "true",
            "include-verse-numbers": "true", 
            "include-footnotes": "true",
            "include-headings": "true"
        }
        
        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            data = response.json()
            return data["passages"][0] if data["passages"] else None
        else:
            print(f"Error: ESV API returned status code {response.status_code}")
            return None
    
    elif version in ["KJV", "NKJV", "NIV", "AMP"]:
        # Use API.Bible for other versions (https://scripture.api.bible/)
        # Map of API.Bible IDs for different versions
        bible_ids = {
            "KJV": "de4e12af7f28f599-02",  # King James (Authorized) Version
            "NKJV": "19d8628a61a1936c-01", # New King James Version
            "NIV": "78a9f6124f344018-01",  # New International Version
            "AMP": "08a79c72d7abd6e8-01"   # Amplified Bible
        }
        
        bible_id = bible_ids.get(version)
        if not bible_id:
            print(f"Error: No Bible ID configured for version {version}")
            return None
        
        # Convert book abbreviation to full name for API.Bible
        book_name_map = {
            "gen": "Genesis", "exo": "Exodus", "lev": "Leviticus",
            "num": "Numbers", "deu": "Deuteronomy", "jos": "Joshua",
            "jdg": "Judges", "rut": "Ruth", "1sa": "1 Samuel",
            "2sa": "2 Samuel", "1ki": "1 Kings", "2ki": "2 Kings",
            "1ch": "1 Chronicles", "2ch": "2 Chronicles", "ezr": "Ezra",
            "neh": "Nehemiah", "est": "Esther", "job": "Job",
            "psa": "Psalms", "pro": "Proverbs", "ecc": "Ecclesiastes",
            "sng": "Song of Solomon", "isa": "Isaiah", "jer": "Jeremiah",
            "lam": "Lamentations", "ezk": "Ezekiel", "dan": "Daniel",
            "hos": "Hosea", "jol": "Joel", "amo": "Amos",
            "oba": "Obadiah", "jon": "Jonah", "mic": "Micah",
            "nah": "Nahum", "hab": "Habakkuk", "zep": "Zephaniah",
            "hag": "Haggai", "zec": "Zechariah", "mal": "Malachi",
            "mat": "Matthew", "mrk": "Mark", "luk": "Luke",
            "jhn": "John", "act": "Acts", "rom": "Romans",
            "1co": "1 Corinthians", "2co": "2 Corinthians", "gal": "Galatians",
            "eph": "Ephesians", "php": "Philippians", "col": "Colossians",
            "1th": "1 Thessalonians", "2th": "2 Thessalonians", "1ti": "1 Timothy",
            "2ti": "2 Timothy", "tit": "Titus", "phm": "Philemon",
            "heb": "Hebrews", "jas": "James", "1pe": "1 Peter",
            "2pe": "2 Peter", "1jn": "1 John", "2jn": "2 John",
            "3jn": "3 John", "jud": "Jude", "rev": "Revelation"
        }
        
        # Convert to API.Bible format
        book_name = book_name_map.get(book_abbr, book_abbr)
        
        # API.Bible endpoint
        url = f"https://api.scripture.api.bible/v1/bibles/{bible_id}/chapters/{book_name}.{chapter}"
        headers = {
            "api-key": api_keys['api_bible']
        }
        
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            content = data["data"]["content"]
            
            # API.Bible returns HTML content that needs to be parsed
            # For simplicity, we'll do some basic cleanup
            import re
            from html import unescape
            
            # Remove HTML tags but keep verse numbers
            content = re.sub(r'<span data-number="(\d+)" class="v">(\d+)</span>', r'\1 ', content)
            content = re.sub(r'<h3[^>]*>(.*?)</h3>', r'\1\n', content)
            content = re.sub(r'<[^>]+>', '', content)
            content = unescape(content)
            
            return content
        else:
            print(f"Error: API.Bible returned status code {response.status_code}")
            return None

    return None

def create_chapter_xml(version, book_info, chapter_num, content):
    """Convert chapter content to XML structure."""
    
    # Create root elements
    root = ET.Element("crossway-bible")
    
    # Create book element with attributes
    book = ET.SubElement(root, "book", {
        "title": book_info["title"],
        "num": str(book_info["num"]),
        "testament": book_info["testament"],
        "version": version,
        "bookAbbr": book_info["abbr"]
    })
    
    # Create chapter element
    chapter = ET.SubElement(book, "chapter", {"num": str(chapter_num)})
    
    # Process content based on the version and format
    lines = content.strip().split('\n')
    in_heading = False
    current_heading = ""
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # Check if this is a heading (no digits, all caps, or specific format)
        if all(not c.isdigit() for c in line) and (line.isupper() or line.endswith(':') or in_heading):
            if not in_heading:
                in_heading = True
                current_heading = line
            else:
                current_heading += " " + line
                
            # If heading seems complete, add it
            if line.endswith(':') or line.endswith('.'):
                heading = ET.SubElement(chapter, "heading")
                heading.text = current_heading
                in_heading = False
                current_heading = ""
                
                # Add paragraph markers
                begin_para = ET.SubElement(chapter, "begin-paragraph")
        else:
            # If there was a potential heading but it's not complete, add it now
            if in_heading:
                heading = ET.SubElement(chapter, "heading")
                heading.text = current_heading
                in_heading = False
                current_heading = ""
                begin_para = ET.SubElement(chapter, "begin-paragraph")
            
            # Try to extract verse number using regex
            import re
            verse_match = re.match(r'(\d+)\s+(.*)', line)
            
            if verse_match:
                verse_num = verse_match.group(1)
                verse_text = verse_match.group(2)
                
                # Create verse element
                v = ET.SubElement(chapter, "v", {"n": verse_num})
                v.text = verse_text
                
                # Add verse marker for next verse
                next_verse = int(verse_num) + 1
                if next_verse <= 200:  # reasonable upper limit
                    marker = ET.SubElement(chapter, "marker", {
                        "class": "begin-verse",
                        "mid": f"v{book_info['id']:02d}{chapter_num:03d}{next_verse:03d}"
                    })
            else:
                # This might be continuation of previous verse or other content
                # For simplicity, we'll add it as a paragraph
                para = ET.SubElement(chapter, "begin-paragraph")
                para.tail = line
    
    return ET.ElementTree(root)

def save_xml_file(tree, output_path):
    """Save XML tree to file with pretty formatting."""
    rough_string = ET.tostring(tree.getroot(), encoding='utf-8')
    reparsed = minidom.parseString(rough_string)
    pretty_xml = reparsed.toprettyxml(indent="  ", encoding="utf-8")
    
    # Remove empty lines (common issue with minidom.toprettyxml)
    lines = pretty_xml.decode('utf-8').split('\n')
    non_empty_lines = [line for line in lines if line.strip()]
    pretty_xml = '\n'.join(non_empty_lines).encode('utf-8')
    
    with open(output_path, "wb") as f:
        f.write(pretty_xml)
        
    print(f"  Saved: {os.path.basename(output_path)}")

def main():
    # API keys for Bible APIs
    api_keys = {
        'esv': "635f6f76a32703e82f372ce2f26a99db76896e07",          # Get from https://api.esv.org/
        'api_bible': "pyExkJPN1XXpoJ39Xa8Xi"  # Premium API.Bible key with NIV, NKJV, AMP access
    }
    
    # Versions to process
    versions = ["ESV", "KJV", "NIV", "NKJV", "AMP"]
    
    # Complete Bible book information
    books = [
        # Old Testament
        {"id": 1, "num": 1, "title": "Genesis", "testament": "old", "abbr": "gen"},
        {"id": 2, "num": 2, "title": "Exodus", "testament": "old", "abbr": "exo"},
        # ... more books
        
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
    print("\nAvailable versions: ESV, KJV, NIV, NKJV, AMP")
    selected_versions = input("Enter versions to process (comma-separated, or 'all'): ")
    if selected_versions.lower() == 'all':
        selected_versions = versions
    else:
        selected_versions = [v.strip().upper() for v in selected_versions.split(',')]
        # Filter to only valid versions
        selected_versions = [v for v in selected_versions if v in versions]
        
    if not selected_versions:
        print("No valid versions selected. Using ESV.")
        selected_versions = ["ESV"]
    
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
                content = fetch_chapter_content(version, book['abbr'], chapter_num, api_keys)
                
                if content:
                    # Create XML structure
                    xml_tree = create_chapter_xml(version, book, chapter_num, content)
                    
                    # Save to file
                    output_file = os.path.join(version_dir, f"{book['abbr']}_{chapter_num}.xml")
                    save_xml_file(xml_tree, output_file)
                    
                    # Be nice to the API - don't hammer it with requests
                    time.sleep(1)
                else:
                    print(f"  Failed to fetch content for {book['title']} {chapter_num}")
        
    print("\nProcess completed.")

if __name__ == "__main__":
    main()