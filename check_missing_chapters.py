import os
import re

def check_missing_chapters():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    esv_dir = os.path.join(base_dir, "esv")
    
    if not os.path.exists(esv_dir):
        print(f"ESV directory not found at: {esv_dir}")
        return
        
    # List of expected books and their chapter counts
    chapter_counts = {
        "genesis": 50, "exodus": 40, "leviticus": 27, "numbers": 36, "deuteronomy": 34, 
        "joshua": 24, "judges": 21, "ruth": 4, "1_samuel": 31, "2_samuel": 24, 
        "1_kings": 22, "2_kings": 25, "1_chronicles": 29, "2_chronicles": 36,
        "ezra": 10, "nehemiah": 13, "esther": 10, "job": 42, "psalms": 150, "proverbs": 31, 
        "ecclesiastes": 12, "song_of_solomon": 8, "isaiah": 66, "jeremiah": 52, "lamentations": 5, 
        "ezekiel": 48, "daniel": 12, "hosea": 14, "joel": 3, "amos": 9, 
        "obadiah": 1, "jonah": 4, "micah": 7, "nahum": 3, "habakkuk": 3,
        "zephaniah": 3, "haggai": 2, "zechariah": 14, "malachi": 4, "matthew": 28, 
        "mark": 16, "luke": 24, "john": 21, "acts": 28, "romans": 16, 
        "1_corinthians": 16, "2_corinthians": 13, "galatians": 6, "ephesians": 6, "philippians": 4, 
        "colossians": 4, "1_thessalonians": 5, "2_thessalonians": 3, "1_timothy": 6, "2_timothy": 4, 
        "titus": 3, "philemon": 1, "hebrews": 13, "james": 5, "1_peter": 5, 
        "2_peter": 3, "1_john": 5, "2_john": 1, "3_john": 1, "jude": 1, 
        "revelation": 22
    }
    
    # Get list of files in the directory
    existing_files = os.listdir(esv_dir)
    existing_files = [f for f in existing_files if f.endswith('.xml')]
    
    # Keep track of which files exist
    found_chapters = {}
    
    # Parse filenames to get book and chapter
    for filename in existing_files:
        match = re.match(r'(.+)_(\d+)\.xml', filename)
        if match:
            book = match.group(1)
            chapter = int(match.group(2))
            
            if book not in found_chapters:
                found_chapters[book] = []
            
            found_chapters[book].append(chapter)
    
    # Check for missing chapters
    print("\nMissing Chapters Report:")
    print("=======================")
    
    total_missing = 0
    total_books_with_missing = 0
    books_with_no_chapters = []
    
    for book, expected_count in chapter_counts.items():
        if book not in found_chapters:
            books_with_no_chapters.append(book)
            total_missing += expected_count
            total_books_with_missing += 1
            continue
            
        chapters = found_chapters[book]
        missing = [ch for ch in range(1, expected_count + 1) if ch not in chapters]
        
        if missing:
            total_books_with_missing += 1
            total_missing += len(missing)
            print(f"{book.replace('_', ' ').title()}: Missing chapters {', '.join(map(str, missing))}")
    
    if books_with_no_chapters:
        print("\nBooks with no chapters at all:")
        for book in books_with_no_chapters:
            print(f"- {book.replace('_', ' ').title()}")
    
    print("\nSummary:")
    print(f"Total missing chapters: {total_missing}")
    print(f"Books with missing chapters: {total_books_with_missing}")
    print(f"Total books: {len(chapter_counts)}")
    print(f"Total expected chapters: {sum(chapter_counts.values())}")
    print(f"Found chapters: {sum(len(chapters) for chapters in found_chapters.values())}")

if __name__ == "__main__":
    check_missing_chapters()