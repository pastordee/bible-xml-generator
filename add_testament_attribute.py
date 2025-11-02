import os
import xml.etree.ElementTree as ET
import sys
import re

# Define which books belong to which testament with abbreviations
old_testament_map = {
    "gen": "Genesis", "exo": "Exodus", "lev": "Leviticus", "num": "Numbers", "deu": "Deuteronomy",
    "jos": "Joshua", "jdg": "Judges", "rut": "Ruth", "1sa": "1 Samuel", "2sa": "2 Samuel", 
    "1ki": "1 Kings", "2ki": "2 Kings", "1ch": "1 Chronicles", "2ch": "2 Chronicles", 
    "ezr": "Ezra", "neh": "Nehemiah", "est": "Esther", "job": "Job", "psa": "Psalms", 
    "pro": "Proverbs", "ecc": "Ecclesiastes", "sng": "Song of Solomon", "isa": "Isaiah", 
    "jer": "Jeremiah", "lam": "Lamentations", "ezk": "Ezekiel", "dan": "Daniel", 
    "hos": "Hosea", "jol": "Joel", "amo": "Amos", "oba": "Obadiah", "jon": "Jonah", 
    "mic": "Micah", "nah": "Nahum", "hab": "Habakkuk", "zep": "Zephaniah", "hag": "Haggai", 
    "zec": "Zechariah", "mal": "Malachi"
}

new_testament_map = {
    "mat": "Matthew", "mrk": "Mark", "luk": "Luke", "jhn": "John", "acts": "acts", 
    "rom": "Romans", "1co": "1 Corinthians", "2co": "2 Corinthians", "gal": "Galatians", 
    "eph": "Ephesians", "php": "Philippians", "col": "Colossians", "1th": "1 Thessalonians", 
    "2th": "2 Thessalonians", "1ti": "1 Timothy", "2ti": "2 Timothy", "tit": "Titus", 
    "phm": "Philemon", "heb": "Hebrews", "jas": "James", "1pe": "1 Peter", "2pe": "2 Peter", 
    "1jn": "1 John", "2jn": "2 John", "3jn": "3 John", "jud": "Jude", "rev": "Revelation"
}

# Extract book abbreviation from filename
def extract_book_from_filename(filename):
    # Extract book code (letters before underscore or number)
    match = re.match(r'([a-z0-9]+)[-_]?\d*\.xml', filename.lower())
    if match:
        book_code = match.group(1)
        
        # Check if this is an Old Testament book
        if book_code in old_testament_map:
            return old_testament_map[book_code], "Old Testament"
        
        # Check if this is a New Testament book
        if book_code in new_testament_map:
            return new_testament_map[book_code], "New Testament"
    
    return filename, "Unknown"

def process_directory():
    """Process all MXL files in the bible directory"""
    bible_dir = os.path.dirname(os.path.abspath(__file__))
    modified_count = 0
    error_count = 0
    
    print(f"Scanning directory: {bible_dir}")
    
    # Get all MXL files in the directory
    files = [f for f in os.listdir(bible_dir) if os.path.isfile(os.path.join(bible_dir, f)) and f.endswith('.mxl')]
    
    for filename in files:
        file_path = os.path.join(bible_dir, filename)
        try:
            # Parse the XML file
            tree = ET.parse(file_path)
            root = tree.getroot()
            
            # Skip if testament attribute already exists
            if root.get("testament") is not None:
                print(f"Skipping {filename}: Testament attribute already exists")
                continue
            
            # Try to get book name from XML structure or use filename
            book_element = root.find(".//book") or root.find(".//name") or root.find(".//title")
            
            if book_element is not None and book_element.text:
                book_name = book_element.text
                # Determine testament based on book name in XML
                if any(book.lower() in book_name.lower() for book in old_testament_map.values()):
                    testament = "Old Testament"
                elif any(book.lower() in book_name.lower() for book in new_testament_map.values()):
                    testament = "New Testament"
                else:
                    testament = "Unknown"
            else:
                # Extract from filename if XML doesn't contain book name
                book_name, testament = extract_book_from_filename(filename)
                
            if testament == "Unknown":
                print(f"Warning: Could not determine testament for {filename}")
                continue
                
            # Add the testament attribute to the root element
            root.set("testament", testament)
            
            # Write the updated XML back to the file
            tree.write(file_path, encoding="utf-8", xml_declaration=True)
                
            print(f"Updated {filename}: {testament} (Book: {book_name})")
            modified_count += 1
            
        except Exception as e:
            print(f"Error processing {filename}: {str(e)}")
            error_count += 1
    
    print(f"\nProcess completed: {modified_count} files modified, {error_count} errors")

if __name__ == "__main__":
    process_directory()