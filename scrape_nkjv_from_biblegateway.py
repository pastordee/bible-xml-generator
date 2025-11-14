#!/usr/bin/env python3
"""
Scrape NKJV Bible text from Bible Gateway and create chapter files.
"""

import requests
from bs4 import BeautifulSoup
import time
import re
from pathlib import Path

# Bible structure: (book_name, book_code, num_chapters, testament)
BIBLE_STRUCTURE = [
    # Old Testament
    ('genesis', 'Genesis', 50, 'ot'), ('exodus', 'Exodus', 40, 'ot'), 
    ('leviticus', 'Leviticus', 27, 'ot'), ('numbers', 'Numbers', 36, 'ot'), 
    ('deuteronomy', 'Deuteronomy', 34, 'ot'), ('joshua', 'Joshua', 24, 'ot'),
    ('judges', 'Judges', 21, 'ot'), ('ruth', 'Ruth', 4, 'ot'), 
    ('1_samuel', '1 Samuel', 31, 'ot'), ('2_samuel', '2 Samuel', 24, 'ot'), 
    ('1_kings', '1 Kings', 22, 'ot'), ('2_kings', '2 Kings', 25, 'ot'),
    ('1_chronicles', '1 Chronicles', 29, 'ot'), ('2_chronicles', '2 Chronicles', 36, 'ot'), 
    ('ezra', 'Ezra', 10, 'ot'), ('nehemiah', 'Nehemiah', 13, 'ot'), 
    ('esther', 'Esther', 10, 'ot'), ('job', 'Job', 42, 'ot'),
    ('psalms', 'Psalm', 150, 'ot'), ('proverbs', 'Proverbs', 31, 'ot'), 
    ('ecclesiastes', 'Ecclesiastes', 12, 'ot'), ('song_of_solomon', 'Song of Solomon', 8, 'ot'), 
    ('isaiah', 'Isaiah', 66, 'ot'), ('jeremiah', 'Jeremiah', 52, 'ot'),
    ('lamentations', 'Lamentations', 5, 'ot'), ('ezekiel', 'Ezekiel', 48, 'ot'), 
    ('daniel', 'Daniel', 12, 'ot'), ('hosea', 'Hosea', 14, 'ot'), 
    ('joel', 'Joel', 3, 'ot'), ('amos', 'Amos', 9, 'ot'),
    ('obadiah', 'Obadiah', 1, 'ot'), ('jonah', 'Jonah', 4, 'ot'), 
    ('micah', 'Micah', 7, 'ot'), ('nahum', 'Nahum', 3, 'ot'), 
    ('habakkuk', 'Habakkuk', 3, 'ot'), ('zephaniah', 'Zephaniah', 3, 'ot'),
    ('haggai', 'Haggai', 2, 'ot'), ('zechariah', 'Zechariah', 14, 'ot'), 
    ('malachi', 'Malachi', 4, 'ot'),
    # New Testament
    ('matthew', 'Matthew', 28, 'nt'), ('mark', 'Mark', 16, 'nt'), 
    ('luke', 'Luke', 24, 'nt'), ('john', 'John', 21, 'nt'), 
    ('acts', 'Acts', 28, 'nt'), ('romans', 'Romans', 16, 'nt'),
    ('1_corinthians', '1 Corinthians', 16, 'nt'), ('2_corinthians', '2 Corinthians', 13, 'nt'),
    ('galatians', 'Galatians', 6, 'nt'), ('ephesians', 'Ephesians', 6, 'nt'), 
    ('philippians', 'Philippians', 4, 'nt'), ('colossians', 'Colossians', 4, 'nt'), 
    ('1_thessalonians', '1 Thessalonians', 5, 'nt'), ('2_thessalonians', '2 Thessalonians', 3, 'nt'), 
    ('1_timothy', '1 Timothy', 6, 'nt'), ('2_timothy', '2 Timothy', 4, 'nt'),
    ('titus', 'Titus', 3, 'nt'), ('philemon', 'Philemon', 1, 'nt'), 
    ('hebrews', 'Hebrews', 13, 'nt'), ('james', 'James', 5, 'nt'), 
    ('1_peter', '1 Peter', 5, 'nt'), ('2_peter', '2 Peter', 3, 'nt'),
    ('1_john', '1 John', 5, 'nt'), ('2_john', '2 John', 1, 'nt'), 
    ('3_john', '3 John', 1, 'nt'), ('jude', 'Jude', 1, 'nt'), 
    ('revelation', 'Revelation', 22, 'nt')
]

def fetch_chapter(book_name, chapter_num):
    """Fetch a chapter from Bible Gateway with crossreferences."""
    # Add interface=print to get cleaner HTML with crossrefs visible
    url = f"https://www.biblegateway.com/passage/?search={book_name}+{chapter_num}&version=NKJV&interface=print"
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Find the passage text
        passage_div = soup.find('div', class_='passage-text')
        if not passage_div:
            return None
        
        # Convert crossref markers from (A) to lowercase a, (B) to b, etc.
        for crossref in passage_div.find_all('sup', class_='crossreference'):
            letter_upper = crossref.get_text(strip=True)
            # Remove parentheses and convert to lowercase
            letter_clean = letter_upper.strip('()').lower()
            # Replace the sup element with just the lowercase letter
            crossref.replace_with(f' {letter_clean} ')
        
        # Remove footnote markers
        for footnote in passage_div.find_all('sup', class_='footnote'):
            footnote.decompose()
        
        # Get the full text with embedded crossref letters
        chapter_text = passage_div.get_text(separator=' ', strip=True)
        
        # Clean up extra whitespace
        chapter_text = re.sub(r'\s+', ' ', chapter_text)
        chapter_text = chapter_text.strip()
        
        return chapter_text
        
    except Exception as e:
        print(f"    Error fetching {book_name} {chapter_num}: {e}")
        return None

def scrape_bible():
    """Scrape all NKJV chapters from Bible Gateway."""
    
    # Create output directories
    ot_dir = Path('raw/chapter_texts_nkjv_ot')
    nt_dir = Path('raw/chapter_texts_nkjv_nt')
    ot_dir.mkdir(parents=True, exist_ok=True)
    nt_dir.mkdir(parents=True, exist_ok=True)
    
    total_chapters = sum(num_chaps for _, _, num_chaps, _ in BIBLE_STRUCTURE)
    chapters_created = 0
    failed = []
    
    print(f"Fetching {total_chapters} chapters from Bible Gateway...")
    print()
    
    for book_file, book_name, num_chapters, testament in BIBLE_STRUCTURE:
        print(f"Fetching {book_name} ({num_chapters} chapters)...")
        
        for chapter_num in range(1, num_chapters + 1):
            # Fetch chapter
            chapter_text = fetch_chapter(book_name, chapter_num)
            
            if chapter_text:
                # Save to file
                output_dir = ot_dir if testament == 'ot' else nt_dir
                filename = f"{book_file}_{chapter_num}.txt"
                filepath = output_dir / filename
                
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(chapter_text)
                
                chapters_created += 1
                
                if chapters_created % 50 == 0:
                    print(f"  Progress: {chapters_created}/{total_chapters} chapters...")
            else:
                failed.append(f"{book_name} {chapter_num}")
            
            # Be nice to the server
            time.sleep(0.5)
    
    print()
    print(f"✓ Successfully fetched {chapters_created}/{total_chapters} chapters")
    
    if failed:
        print(f"✗ Failed to fetch {len(failed)} chapters:")
        for f in failed[:10]:  # Show first 10
            print(f"  - {f}")
        if len(failed) > 10:
            print(f"  ... and {len(failed) - 10} more")
    
    return chapters_created

def main():
    print("=" * 80)
    print("SCRAPING NKJV FROM BIBLE GATEWAY")
    print("=" * 80)
    print()
    print("This will fetch all 1,189 chapters from biblegateway.com")
    print("It will take approximately 10-15 minutes with delays between requests.")
    print()
    
    try:
        total = scrape_bible()
        
        print()
        print("=" * 80)
        print("COMPLETE")
        print("=" * 80)
        print()
        print(f"Created {total} chapter files:")
        print("  - Old Testament: raw/chapter_texts_nkjv_ot/")
        print("  - New Testament: raw/chapter_texts_nkjv_nt/")
        
    except KeyboardInterrupt:
        print("\n\nInterrupted by user. Partial results saved.")
    except Exception as e:
        print(f"\n\nError: {e}")

if __name__ == '__main__':
    main()
