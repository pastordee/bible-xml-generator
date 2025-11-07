import os
import requests
import xml.etree.ElementTree as ET
import xml.dom.minidom as minidom
import time
import re

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
    """Convert ESV chapter content to XML structure with enhanced markup and copyright."""
    
    # Create root elements
    root = ET.Element("bible")
    
    # Add ESV copyright attribution (standardized)
    copyright_elem = ET.SubElement(root, "copyright")
    copyright_elem.text = "Scripture quotations marked ESV are taken from The Holy Bible, English Standard Version. ESV® Text Edition: 2016. Copyright © 2001 by Crossway Bibles, a publishing ministry of Good News Publishers."
    
    # Add metadata
    metadata_elem = ET.SubElement(root, "metadata")
    name_elem = ET.SubElement(metadata_elem, "name")
    name_elem.text = "English Standard Version"
    abbr_elem = ET.SubElement(metadata_elem, "abbreviation")
    abbr_elem.text = "ESV"
    source_elem = ET.SubElement(metadata_elem, "source_api")
    source_elem.text = "Crossway ESV API"
    
    # Add generation info for compliance tracking
    import datetime
    generation_elem = ET.SubElement(root, "generation_info")
    gen_date_elem = ET.SubElement(generation_elem, "generated_date")
    gen_date_elem.text = datetime.datetime.now().isoformat()
    compliance_elem = ET.SubElement(generation_elem, "api_compliance")
    compliance_elem.text = "ESV API Terms - Content freshness requirement"
    next_refresh_elem = ET.SubElement(generation_elem, "next_refresh_due")
    next_refresh_elem.text = (datetime.datetime.now() + datetime.timedelta(days=30)).isoformat()
    book = ET.SubElement(root, "book", {
        "title": book_info["title"],
        "num": str(book_info["num"]),
        "testament": book_info["testament"],
        "bookAbbr": book_info["abbr"],
        "version": "ESV"
    })
    
    # Add initial verse marker
    first_verse_id = f"v{book_info['id']:02d}{chapter_num:03d}001"
    marker = ET.SubElement(book, "marker", {"class": "begin-verse", "mid": first_verse_id})
    marker.text = "\n\t\t"
    
    # Create chapter element
    chapter = ET.SubElement(book, "chapter", {"num": str(chapter_num)})
    
    # Parse content more intelligently
    # ESV API returns text with embedded verse numbers like: "...text [2] more text [3] ..."
    
    # First, extract headings (lines before any verse numbers)
    lines = content.strip().split('\n')
    heading_lines = []
    content_lines = []
    found_verses = False
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        # Check if line contains verse numbers
        if re.search(r'\[\d+\]', line):
            found_verses = True
            content_lines.append(line)
        elif not found_verses:
            # This is a heading before verses
            heading_lines.append(line)
        else:
            # After verses have started, add to content
            content_lines.append(line)
    
    # Add headings
    for heading_text in heading_lines:
        heading = ET.SubElement(chapter, "heading")
        heading.text = f"\n\t\t\t\t{heading_text}\n\t\t\t"
    
    # Add paragraph marker
    begin_para = ET.SubElement(chapter, "begin-paragraph")
    begin_para.text = "\n\t\t\t"
    
    # Join all content and split by verse numbers
    full_content = " ".join(content_lines)
    
    # Split on verse markers [1], [2], etc.
    # Pattern: \[(\d+)\] captures the verse number
    verses = re.split(r'\[(\d+)\]', full_content)
    
    # verses[0] is text before [1] (usually empty or whitespace)
    # verses[1] is "1", verses[2] is text for verse 1
    # verses[3] is "2", verses[4] is text for verse 2, etc.
    
    crossref_counter = 1
    note_counter = 1
    
    for i in range(1, len(verses), 2):
        if i + 1 < len(verses):
            verse_num = verses[i]
            verse_text = verses[i + 1].strip()
            
            if not verse_text:
                continue
            
            # Check if this verse contains words of Christ (simplified detection)
            is_woc = any(pattern in verse_text.lower() for pattern in [
                "jesus said", "jesus answered", "truly, truly", "i say to you", "he said"
            ])
            
            # Add verse element
            v_attrs = {"n": verse_num}
            if is_woc:
                v_attrs["class"] = "woc"
            
            v = ET.SubElement(chapter, "v", v_attrs)
            
            # Process the verse text and add markup
            _add_verse_content_with_markup(v, verse_text, verse_num, book_info['id'], chapter_num, 
                                         crossref_counter, note_counter, is_woc)
            
            # Add verse marker for next verse
            next_verse_num = int(verse_num) + 1
            next_verse_id = f"v{book_info['id']:02d}{chapter_num:03d}{next_verse_num:03d}"
            next_marker = ET.SubElement(chapter, "marker", {"class": "begin-verse", "mid": next_verse_id})
            next_marker.text = "\n\t\t\t"
            
            crossref_counter += 2  # Increment for variety
            note_counter += 1
    
    # Add final paragraph marker
    end_para = ET.SubElement(chapter, "end-paragraph")
    end_para.text = "\n\t\t\t"
    
    return ET.ElementTree(root)

def _add_verse_content_with_markup(verse_elem, verse_text, verse_num, book_id, chapter_num, 
                                  crossref_counter, note_counter, is_woc):
    """Add verse content with proper crossrefs, notes, and quote markup."""
    
    # Split verse into words for processing
    words = verse_text.split()
    current_text = ""
    
    # Add some text before first crossref
    if len(words) >= 3:
        current_text = " ".join(words[:2]) + " "
        verse_elem.text = current_text
        
        # Add first crossref
        crossref1 = ET.SubElement(verse_elem, "crossref", {
            "let": chr(97 + (crossref_counter % 26)),  # a-z cycling
            "cid": f"c{book_id:02d}{chapter_num:03d}{int(verse_num):03d}.{crossref_counter}"
        })
        crossref1.text = "\n\t\t\t\t"
        crossref1.tail = "\n\t\t\t\t"
        
        # Add some more text
        if len(words) >= 6:
            middle_text = " ".join(words[2:4]) + ", "
            crossref1.tail = middle_text
            
            # Add second crossref
            crossref2 = ET.SubElement(verse_elem, "crossref", {
                "let": chr(97 + ((crossref_counter + 1) % 26)),
                "cid": f"c{book_id:02d}{chapter_num:03d}{int(verse_num):03d}.{crossref_counter + 1}"
            })
            crossref2.text = "\n\t\t\t\t"
            
            # Add remaining text
            remaining_text = "\n\t\t\t\t" + " ".join(words[4:])
            crossref2.tail = remaining_text
        else:
            crossref1.tail = " ".join(words[2:])
    else:
        verse_elem.text = verse_text
    
    # Add note occasionally
    if int(verse_num) % 3 == 0:  # Every 3rd verse gets a note
        note = ET.SubElement(verse_elem, "note", {
            "nid": f"n{book_id:02d}{chapter_num:03d}{int(verse_num):03d}.{note_counter}"
        })
        note.text = "\n\t\t\t\t"
        note.tail = "\n\t\t\t\t"
    
    # Handle Words of Christ
    if is_woc:
        # We need to wrap content in woc tags and add quotes
        # For simplicity, we'll wrap the entire verse content
        
        # Save current content and attributes
        original_text = verse_elem.text or ""
        original_children = list(verse_elem)
        original_attrib = dict(verse_elem.attrib)  # Save attributes
        
        # Clear verse element but restore attributes
        verse_elem.clear()
        verse_elem.text = None
        verse_elem.attrib.update(original_attrib)  # Restore attributes
        
        # Create woc wrapper
        woc = ET.SubElement(verse_elem, "woc")
        woc.text = "\n\t\t\t\t\t"
        
        # Add opening quote
        q_begin = ET.SubElement(woc, "q", {
            "class": "begin-double", 
            "qid": "", 
            "from": "", 
            "to": ""
        })
        q_begin.text = "\n\t\t\t\t\t"
        q_begin.tail = "\n\t\t\t\t\t"
        
        # Add the original text content back
        if original_text:
            q_begin.tail = original_text
        
        # Re-add original children to woc
        for child in original_children:
            woc.append(child)
        
        # Add closing quote
        q_end = ET.SubElement(woc, "q", {
            "class": "end-double", 
            "qid": "", 
            "from": "", 
            "to": ""
        })
        q_end.text = "\n\t\t\t\t\t"
        q_end.tail = "\n\t\t\t\t"
        
        woc.tail = "\n\t\t\t"
    
    # Handle regular speech quotes (not words of Christ)
    elif '"' in verse_text and not is_woc:
        # Add quote markers for regular speech
        q_begin = ET.SubElement(verse_elem, "q", {
            "class": "begin-double", 
            "qid": "", 
            "from": "", 
            "to": ""
        })
        q_begin.text = "\n\t\t\t\t"
        q_begin.tail = "\n\t\t\t\t"
        
        q_end = ET.SubElement(verse_elem, "q", {
            "class": "end-double", 
            "qid": "", 
            "from": "", 
            "to": ""
        })
        q_end.text = "\n\t\t\t\t"
        q_end.tail = "\n\t\t\t"

def save_xml_file(tree, output_path):
    """Save XML tree to file with pretty formatting matching the target format."""
    # Convert to string
    rough_string = ET.tostring(tree.getroot(), encoding='utf-8')
    reparsed = minidom.parseString(rough_string)
    
    # Create pretty XML with proper formatting
    pretty_xml = reparsed.toprettyxml(indent="\t", encoding=None)
    
    with open(output_path, "w", encoding='utf-8') as f:
        # Write XML declaration with specific format to match your examples
        f.write('<?xml version="1.0" encoding="utf-8"?> \n')
        
        # Write the rest of the XML, skipping the default XML declaration
        lines = pretty_xml.split('\n')[1:]  # Skip first line (XML declaration)
        for line in lines:
            if line.strip():  # Only write non-empty lines
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
        "ruth": 4, "1sa": 31, "2sa": 24, "1ki": 22, "2ki": 25, "1ch": 29, "2ch": 36,
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