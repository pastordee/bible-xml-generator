#!/usr/bin/env python3
"""
Resumable ESV Bible download with rate limit handling.
Downloads in stages and can resume from where it left off.
"""

import os
import json
import time
from create_esv_version_chapters import fetch_esv_chapter_content, create_detailed_chapter_xml, save_xml_file

# Progress tracking file
PROGRESS_FILE = "esv_download_progress.json"
ESV_DIR = "esv"

def load_progress():
    """Load download progress from file."""
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, 'r') as f:
            return json.load(f)
    return {"completed_chapters": [], "last_book": None, "last_chapter": None, "total_downloaded": 0}

def save_progress(progress):
    """Save download progress to file."""
    with open(PROGRESS_FILE, 'w') as f:
        json.dump(progress, f, indent=2)

def get_all_books():
    """Get complete list of all 66 Bible books."""
    return [
        # Old Testament
        {"id": 1, "num": 1, "title": "Genesis", "testament": "old", "abbr": "gen", "chapters": 50},
        {"id": 2, "num": 2, "title": "Exodus", "testament": "old", "abbr": "exo", "chapters": 40},
        {"id": 3, "num": 3, "title": "Leviticus", "testament": "old", "abbr": "lev", "chapters": 27},
        {"id": 4, "num": 4, "title": "Numbers", "testament": "old", "abbr": "num", "chapters": 36},
        {"id": 5, "num": 5, "title": "Deuteronomy", "testament": "old", "abbr": "deu", "chapters": 34},
        {"id": 6, "num": 6, "title": "Joshua", "testament": "old", "abbr": "jos", "chapters": 24},
        {"id": 7, "num": 7, "title": "Judges", "testament": "old", "abbr": "jdg", "chapters": 21},
        {"id": 8, "num": 8, "title": "Ruth", "testament": "old", "abbr": "rut", "chapters": 4},
        {"id": 9, "num": 9, "title": "1 Samuel", "testament": "old", "abbr": "1sa", "chapters": 31},
        {"id": 10, "num": 10, "title": "2 Samuel", "testament": "old", "abbr": "2sa", "chapters": 24},
        {"id": 11, "num": 11, "title": "1 Kings", "testament": "old", "abbr": "1ki", "chapters": 22},
        {"id": 12, "num": 12, "title": "2 Kings", "testament": "old", "abbr": "2ki", "chapters": 25},
        {"id": 13, "num": 13, "title": "1 Chronicles", "testament": "old", "abbr": "1ch", "chapters": 29},
        {"id": 14, "num": 14, "title": "2 Chronicles", "testament": "old", "abbr": "2ch", "chapters": 36},
        {"id": 15, "num": 15, "title": "Ezra", "testament": "old", "abbr": "ezr", "chapters": 10},
        {"id": 16, "num": 16, "title": "Nehemiah", "testament": "old", "abbr": "neh", "chapters": 13},
        {"id": 17, "num": 17, "title": "Esther", "testament": "old", "abbr": "est", "chapters": 10},
        {"id": 18, "num": 18, "title": "Job", "testament": "old", "abbr": "job", "chapters": 42},
        {"id": 19, "num": 19, "title": "Psalms", "testament": "old", "abbr": "psa", "chapters": 150},
        {"id": 20, "num": 20, "title": "Proverbs", "testament": "old", "abbr": "pro", "chapters": 31},
        {"id": 21, "num": 21, "title": "Ecclesiastes", "testament": "old", "abbr": "ecc", "chapters": 12},
        {"id": 22, "num": 22, "title": "Song of Solomon", "testament": "old", "abbr": "sng", "chapters": 8},
        {"id": 23, "num": 23, "title": "Isaiah", "testament": "old", "abbr": "isa", "chapters": 66},
        {"id": 24, "num": 24, "title": "Jeremiah", "testament": "old", "abbr": "jer", "chapters": 52},
        {"id": 25, "num": 25, "title": "Lamentations", "testament": "old", "abbr": "lam", "chapters": 5},
        {"id": 26, "num": 26, "title": "Ezekiel", "testament": "old", "abbr": "ezk", "chapters": 48},
        {"id": 27, "num": 27, "title": "Daniel", "testament": "old", "abbr": "dan", "chapters": 12},
        {"id": 28, "num": 28, "title": "Hosea", "testament": "old", "abbr": "hos", "chapters": 14},
        {"id": 29, "num": 29, "title": "Joel", "testament": "old", "abbr": "jol", "chapters": 3},
        {"id": 30, "num": 30, "title": "Amos", "testament": "old", "abbr": "amo", "chapters": 9},
        {"id": 31, "num": 31, "title": "Obadiah", "testament": "old", "abbr": "oba", "chapters": 1},
        {"id": 32, "num": 32, "title": "Jonah", "testament": "old", "abbr": "jon", "chapters": 4},
        {"id": 33, "num": 33, "title": "Micah", "testament": "old", "abbr": "mic", "chapters": 7},
        {"id": 34, "num": 34, "title": "Nahum", "testament": "old", "abbr": "nam", "chapters": 3},
        {"id": 35, "num": 35, "title": "Habakkuk", "testament": "old", "abbr": "hab", "chapters": 3},
        {"id": 36, "num": 36, "title": "Zephaniah", "testament": "old", "abbr": "zep", "chapters": 3},
        {"id": 37, "num": 37, "title": "Haggai", "testament": "old", "abbr": "hag", "chapters": 2},
        {"id": 38, "num": 38, "title": "Zechariah", "testament": "old", "abbr": "zec", "chapters": 14},
        {"id": 39, "num": 39, "title": "Malachi", "testament": "old", "abbr": "mal", "chapters": 4},
        # New Testament
        {"id": 40, "num": 40, "title": "Matthew", "testament": "new", "abbr": "mat", "chapters": 28},
        {"id": 41, "num": 41, "title": "Mark", "testament": "new", "abbr": "mrk", "chapters": 16},
        {"id": 42, "num": 42, "title": "Luke", "testament": "new", "abbr": "luk", "chapters": 24},
        {"id": 43, "num": 43, "title": "John", "testament": "new", "abbr": "jhn", "chapters": 21},
        {"id": 44, "num": 44, "title": "Acts", "testament": "new", "abbr": "act", "chapters": 28},
        {"id": 45, "num": 45, "title": "Romans", "testament": "new", "abbr": "rom", "chapters": 16},
        {"id": 46, "num": 46, "title": "1 Corinthians", "testament": "new", "abbr": "1co", "chapters": 16},
        {"id": 47, "num": 47, "title": "2 Corinthians", "testament": "new", "abbr": "2co", "chapters": 13},
        {"id": 48, "num": 48, "title": "Galatians", "testament": "new", "abbr": "gal", "chapters": 6},
        {"id": 49, "num": 49, "title": "Ephesians", "testament": "new", "abbr": "eph", "chapters": 6},
        {"id": 50, "num": 50, "title": "Philippians", "testament": "new", "abbr": "php", "chapters": 4},
        {"id": 51, "num": 51, "title": "Colossians", "testament": "new", "abbr": "col", "chapters": 4},
        {"id": 52, "num": 52, "title": "1 Thessalonians", "testament": "new", "abbr": "1th", "chapters": 5},
        {"id": 53, "num": 53, "title": "2 Thessalonians", "testament": "new", "abbr": "2th", "chapters": 3},
        {"id": 54, "num": 54, "title": "1 Timothy", "testament": "new", "abbr": "1ti", "chapters": 6},
        {"id": 55, "num": 55, "title": "2 Timothy", "testament": "new", "abbr": "2ti", "chapters": 4},
        {"id": 56, "num": 56, "title": "Titus", "testament": "new", "abbr": "tit", "chapters": 3},
        {"id": 57, "num": 57, "title": "Philemon", "testament": "new", "abbr": "phm", "chapters": 1},
        {"id": 58, "num": 58, "title": "Hebrews", "testament": "new", "abbr": "heb", "chapters": 13},
        {"id": 59, "num": 59, "title": "James", "testament": "new", "abbr": "jas", "chapters": 5},
        {"id": 60, "num": 60, "title": "1 Peter", "testament": "new", "abbr": "1pe", "chapters": 5},
        {"id": 61, "num": 61, "title": "2 Peter", "testament": "new", "abbr": "2pe", "chapters": 3},
        {"id": 62, "num": 62, "title": "1 John", "testament": "new", "abbr": "1jn", "chapters": 5},
        {"id": 63, "num": 63, "title": "2 John", "testament": "new", "abbr": "2jn", "chapters": 1},
        {"id": 64, "num": 64, "title": "3 John", "testament": "new", "abbr": "3jn", "chapters": 1},
        {"id": 65, "num": 65, "title": "Jude", "testament": "new", "abbr": "jud", "chapters": 1},
        {"id": 66, "num": 66, "title": "Revelation", "testament": "new", "abbr": "rev", "chapters": 22}
    ]

def download_esv_resumable(api_key, batch_size=100, delay_between_chapters=1):
    """
    Download ESV Bible with progress tracking and rate limit handling.
    
    Args:
        api_key: ESV API key
        batch_size: Number of chapters to download before pausing (default 100)
        delay_between_chapters: Seconds to wait between API calls (default 1)
    """
    
    # Create ESV directory if it doesn't exist
    os.makedirs(ESV_DIR, exist_ok=True)
    
    # Load progress
    progress = load_progress()
    print(f"Loading progress... {progress['total_downloaded']} chapters already downloaded")
    
    # Get all books
    books = get_all_books()
    total_chapters = sum(book['chapters'] for book in books)
    
    print(f"\nTotal chapters in Bible: {total_chapters}")
    print(f"Remaining to download: {total_chapters - progress['total_downloaded']}")
    print(f"Batch size: {batch_size} chapters per session")
    print("="*60)
    
    chapters_in_this_session = 0
    
    try:
        for book in books:
            print(f"\nProcessing {book['title']}...")
            
            for chapter_num in range(1, book['chapters'] + 1):
                # Create chapter identifier
                chapter_id = f"{book['title']}_{chapter_num}"
                
                # Skip if already downloaded
                if chapter_id in progress['completed_chapters']:
                    continue
                
                # Check if we've hit the batch limit
                if chapters_in_this_session >= batch_size:
                    print(f"\n{'='*60}")
                    print(f"✅ Batch limit reached ({batch_size} chapters)")
                    print(f"📊 Session progress: {chapters_in_this_session} chapters downloaded")
                    print(f"📊 Total progress: {progress['total_downloaded']}/{total_chapters} chapters ({progress['total_downloaded']*100//total_chapters}%)")
                    print(f"💾 Progress saved to {PROGRESS_FILE}")
                    print(f"\n⏸️  PAUSING to respect API limits.")
                    print(f"🔄 To continue, run this script again.")
                    print(f"{'='*60}")
                    return True  # Successful pause, can resume later
                
                # Check if file already exists
                safe_title = book['title'].lower().replace(' ', '_')
                output_file = os.path.join(ESV_DIR, f"{safe_title}_{chapter_num}.xml")
                
                if os.path.exists(output_file):
                    print(f"  ⏭️  Skipping {book['title']} {chapter_num} (file exists)")
                    progress['completed_chapters'].append(chapter_id)
                    progress['total_downloaded'] += 1
                    save_progress(progress)
                    continue
                
                # Fetch chapter content
                print(f"  📥 Fetching {book['title']} chapter {chapter_num}...")
                content = fetch_esv_chapter_content(book['title'], chapter_num, api_key)
                
                if content:
                    # Create XML
                    xml_tree = create_detailed_chapter_xml(book, chapter_num, content)
                    
                    # Save to file
                    save_xml_file(xml_tree, output_file)
                    print(f"  ✅ Saved: {os.path.basename(output_file)}")
                    
                    # Update progress
                    progress['completed_chapters'].append(chapter_id)
                    progress['last_book'] = book['title']
                    progress['last_chapter'] = chapter_num
                    progress['total_downloaded'] += 1
                    chapters_in_this_session += 1
                    
                    # Save progress after each chapter
                    save_progress(progress)
                    
                    # Be nice to the API
                    time.sleep(delay_between_chapters)
                else:
                    print(f"  ❌ Failed to fetch {book['title']} {chapter_num}")
                    print(f"  ⚠️  This might be a rate limit. Progress saved.")
                    print(f"  💡 Wait a while and run the script again to resume.")
                    return False  # Failed, might be rate limited
        
        # All done!
        print(f"\n{'='*60}")
        print(f"🎉 COMPLETE! All {total_chapters} chapters downloaded!")
        print(f"📂 Files saved to: {ESV_DIR}/")
        print(f"{'='*60}")
        
        # Clean up progress file
        if os.path.exists(PROGRESS_FILE):
            os.remove(PROGRESS_FILE)
            print(f"🧹 Cleaned up progress file")
        
        return True
        
    except KeyboardInterrupt:
        print(f"\n\n⚠️  Download interrupted by user")
        print(f"📊 Progress: {progress['total_downloaded']}/{total_chapters} chapters")
        print(f"💾 Progress saved to {PROGRESS_FILE}")
        print(f"🔄 Run the script again to resume from where you left off")
        return False

def show_progress():
    """Display current download progress."""
    progress = load_progress()
    total_chapters = 1189
    
    print("="*60)
    print("ESV DOWNLOAD PROGRESS")
    print("="*60)
    print(f"Chapters downloaded: {progress['total_downloaded']}/{total_chapters}")
    print(f"Progress: {progress['total_downloaded']*100//total_chapters}%")
    if progress['last_book']:
        print(f"Last completed: {progress['last_book']} chapter {progress['last_chapter']}")
    print("="*60)

def main():
    import sys
    
    api_key = "635f6f76a32703e82f372ce2f26a99db76896e07"
    
    # Check command line arguments
    if len(sys.argv) > 1:
        if sys.argv[1] == "status":
            show_progress()
            return
        elif sys.argv[1] == "reset":
            if os.path.exists(PROGRESS_FILE):
                os.remove(PROGRESS_FILE)
                print("✅ Progress reset. Starting fresh on next run.")
            return
    
    print("="*60)
    print("ESV BIBLE RESUMABLE DOWNLOADER")
    print("="*60)
    print("Features:")
    print("  ✓ Downloads in batches to respect API limits")
    print("  ✓ Saves progress after each chapter")
    print("  ✓ Can resume from where it left off")
    print("  ✓ Skips already downloaded files")
    print("="*60)
    print()
    
    # Ask for batch size
    print("Recommended batch sizes:")
    print("  - 50 chapters: ~1 minute, very safe")
    print("  - 100 chapters: ~2 minutes, safe")
    print("  - 200 chapters: ~3-4 minutes, moderate")
    print("  - 500 chapters: ~8-10 minutes, aggressive")
    print("  - 1189 chapters: ~20 minutes, all at once (risky)")
    print()
    
    batch_input = input("Enter batch size (default 100): ").strip()
    batch_size = int(batch_input) if batch_input.isdigit() else 100
    
    print(f"\n🚀 Starting download with batch size: {batch_size}")
    print("💡 Press Ctrl+C to stop safely at any time\n")
    
    success = download_esv_resumable(api_key, batch_size=batch_size)
    
    if not success:
        print("\n💡 TIP: If you hit rate limits, wait 10-30 minutes and run again")

if __name__ == "__main__":
    main()
