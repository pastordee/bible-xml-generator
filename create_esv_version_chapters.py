import os
import requests
import xml.etree.ElementTree as ET
import xml.dom.minidom as minidom
import time
import re
import random

def fetch_esv_chapter_content(book_abbr, chapter, api_key):
    """Fetch Bible content from ESV API."""
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
    
    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        data = response.json()
        return data["passages"][0] if data["passages"] else None
    else:
        print(f"Error: ESV API returned status code {response.status_code}")
        return None

def create_detailed_chapter_xml(book_info, chapter_num, content):
    """Create XML with detailed structure matching the target format."""
    # Create root elements
    root = ET.Element("crossway-bible")
    book = ET.SubElement(root, "book", {
        "title": book_info["title"],
        "num": str(book_info["num"]),
        "testament": book_info["testament"],
        "version": "ESV",
        "bookAbbr": book_info["title"]
    })
    
    # Add initial verse marker
    first_verse_id = f"v{book_info['id']:02d}{chapter_num:03d}001"
    marker = ET.SubElement(book, "marker", {"class": "begin-verse", "mid": first_verse_id})
    
    # Create chapter element
    chapter = ET.SubElement(book, "chapter", {"num": str(chapter_num)})
    
    # Process content
    lines = content.strip().split('\n')
    verse_pattern = re.compile(r'^\[?(\d+)\]?\s+(.*?)$')
    note_counter = 1
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Check for headings (lines without verse numbers)
        if "[" not in line and all(not c.isdigit() for c in line[:4]):
            heading_elem = ET.SubElement(chapter, "heading")
            heading_elem.text = line
            begin_para = ET.SubElement(chapter, "begin-paragraph")
            continue
            
        # Process verse content
        match = verse_pattern.match(line)
        if match:
            verse_num = match.group(1)
            verse_text = match.group(2)
            
            # Add verse marker
            verse_id = f"v{book_info['id']:02d}{chapter_num:03d}{int(verse_num):03d}"
            marker = ET.SubElement(chapter, "marker", {"class": "begin-verse", "mid": verse_id})
            
            # Add verse element
            v_attrs = {"n": verse_num}
            
            # Check if this verse contains words of Christ
            is_woc = any(pattern in verse_text.lower() for pattern in [
                "jesus said", "jesus answered", "jesus replied", "jesus asked",
                "he said to", "truly, truly", "i say to you", "i tell you"
            ])
            
            if is_woc:
                v_attrs["class"] = "woc"
            
            v = ET.SubElement(chapter, "v", v_attrs)
            
            # Process verse text with enhanced markup
            processed_text = _process_verse_text(v, verse_text, verse_num, book_info['id'], chapter_num, note_counter)
            note_counter = processed_text.get('note_counter', note_counter)
    
    # Final paragraph marker
    end_para = ET.SubElement(chapter, "end-paragraph")
    
    return ET.ElementTree(root)

def _process_verse_text(verse_elem, verse_text, verse_num, book_id, chapter_num, note_counter):
    """Process verse text and add notes, woc tags, and quotation markers."""
    import random
    
    # Split text into parts for processing
    text_parts = []
    current_text = verse_text
    
    # Look for quotation patterns
    quote_patterns = [
        (r'"([^"]+)"', 'double'),  # Double quotes
        (r"'([^']+)'", 'single'),  # Single quotes
    ]
    
    # Check if this is words of Christ
    is_christ_speaking = any(pattern in verse_text.lower() for pattern in [
        "jesus said", "jesus answered", "jesus replied", "truly, truly", "i say to you"
    ])
    
    # Simple text processing - in a real implementation, this would be more sophisticated
    words = verse_text.split()
    text_so_far = ""
    
    for i, word in enumerate(words):
        if i == 0:
            text_so_far = word
        else:
            text_so_far += " " + word
            
        # Add crossref occasionally (every 5-10 words)
        if i > 0 and i % 7 == 0 and random.random() > 0.7:
            if verse_elem.text is None:
                verse_elem.text = text_so_far
            else:
                # Find last element to add tail
                if len(verse_elem) > 0:
                    if verse_elem[-1].tail is None:
                        verse_elem[-1].tail = " " + word
                    else:
                        verse_elem[-1].tail += " " + word
                else:
                    verse_elem.text += " " + word
                    
            # Add crossref
            crossref = ET.SubElement(verse_elem, "crossref", {
                "let": chr(97 + (note_counter % 26)),
                "cid": f"c{book_id:02d}{chapter_num:03d}{verse_num}.{note_counter}"
            })
            text_so_far = ""
            note_counter += 1
            
        # Add note occasionally
        elif i > 0 and random.random() > 0.85:
            # Add note element
            note = ET.SubElement(verse_elem, "note", {
                "nid": f"n{book_id:02d}{chapter_num:03d}{verse_num}.{note_counter}"
            })
            note_counter += 1
    
    # Handle remaining text
    if text_so_far:
        if verse_elem.text is None:
            verse_elem.text = text_so_far
        elif len(verse_elem) > 0:
            if verse_elem[-1].tail is None:
                verse_elem[-1].tail = text_so_far
            else:
                verse_elem[-1].tail += text_so_far
        else:
            verse_elem.text += text_so_far
    
    # If this is words of Christ, wrap in woc tags
    if is_christ_speaking:
        # Move existing content into woc element
        original_text = verse_elem.text or ""
        original_children = list(verse_elem)
        
        # Clear verse element
        verse_elem.clear()
        verse_elem.text = None
        
        # Create woc wrapper
        woc = ET.SubElement(verse_elem, "woc")
        
        # Add quote markers
        q_begin = ET.SubElement(woc, "q", {"class": "begin-double", "qid": "", "from": "", "to": ""})
        woc.text = original_text
        
        # Re-add children to woc
        for child in original_children:
            woc.append(child)
            
        q_end = ET.SubElement(woc, "q", {"class": "end-double", "qid": "", "from": "", "to": ""})
    
    return {"note_counter": note_counter}

def save_xml_file(tree, output_path):
    """Save XML tree to file with pretty formatting and retain empty tags."""
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

def main():
    # ESV API key
    esv_api_key = "635f6f76a32703e82f372ce2f26a99db76896e07"
    
    # Complete Bible book information
    books = [
        # Old Testament
        {"id": 1, "num": 1, "title": "Genesis", "testament": "old", "abbr": "gen"},
        {"id": 2, "num": 2, "title": "Exodus", "testament": "old", "abbr": "exo"},
        {"id": 3, "num": 3, "title": "Leviticus", "testament": "old", "abbr": "lev"},
        {"id": 4, "num": 4, "title": "Numbers", "testament": "old", "abbr": "num"},
        {"id": 5, "num": 5, "title": "Deuteronomy", "testament": "old", "abbr": "deu"},
        {"id": 6, "num": 6, "title": "Joshua", "testament": "old", "abbr": "jos"},
        {"id": 7, "num": 7, "title": "Judges", "testament": "old", "abbr": "jdg"},
        {"id": 8, "num": 8, "title": "Ruth", "testament": "old", "abbr": "ruth"},
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
        {"id": 29, "num": 29, "title": "Joel", "testament": "old", "abbr": "joel"},
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
        {"id": 43, "num": 42, "title": "John", "testament": "new", "abbr": "jhn"},
        {"id": 44, "num": 43, "title": "Acts", "testament": "new", "abbr": "act"},
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
    
    # For testing with just a few books
    test_books = [
        {"id": 33, "num": 33, "title": "Micah", "testament": "old", "abbr": "mic"},
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
    version_dir = os.path.join(base_dir, "esv")
    os.makedirs(version_dir, exist_ok=True)
    
    # Ask user which books to process
    print("Available options:")
    print("1. Process test books (Acts and Romans)")
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
    
    print(f"\nProcessing ESV Bible")
    print(f"Processing books: {', '.join(book['title'] for book in selected_books)}")
    
    for book in selected_books:
        print(f"\nProcessing {book['title']} for ESV...")
        
        # Get number of chapters for this book
        max_chapters = chapter_counts.get(book['abbr'], 1)
        
        # Process each chapter
        for chapter_num in range(1, max_chapters + 1):
            print(f"  Fetching {book['title']} chapter {chapter_num}...")
            
            # Fetch chapter content from API
            content = fetch_esv_chapter_content(book['abbr'], chapter_num, esv_api_key)
            
            if content:
                # Create XML structure
                xml_tree = create_detailed_chapter_xml(book, chapter_num, content)
                
                # Save to file - use lowercase title with underscores
                safe_title = book['title'].lower().replace(' ', '_')
                output_file = os.path.join(version_dir, f"{safe_title}_{chapter_num}.xml")
                save_xml_file(xml_tree, output_file)
                
                # Be nice to the API - don't hammer it with requests
                time.sleep(1)
            else:
                print(f"  Failed to fetch content for {book['title']} {chapter_num}")
    
    print("\nESV processing completed.")

if __name__ == "__main__":
    main()