#!/usr/bin/env python3
"""
Convert esv_crossrefs_complete.txt to the raw cross_refs format used in the app.

Raw format structure:
C Chapter {number}
V {booknum}{chapter:03d}{verse:03d}
c {letter}
i c{booknum}{chapter:03d}{verse:03d}.{sequence}
r {ref_booknum}{ref_chapter:03d}{ref_verse:03d} {reference_text}
m {punctuation/text}
...
"""

import re
from pathlib import Path
from collections import defaultdict

BOOK_NUMBERS = {
    'genesis': '01', 'exodus': '02', 'leviticus': '03', 'numbers': '04',
    'deuteronomy': '05', 'joshua': '06', 'judges': '07', 'ruth': '08',
    '1_samuel': '09', '2_samuel': '10', '1_kings': '11', '2_kings': '12',
    '1_chronicles': '13', '2_chronicles': '14', 'ezra': '15', 'nehemiah': '16',
    'esther': '17', 'job': '18', 'psalms': '19', 'proverbs': '20',
    'ecclesiastes': '21', 'song_of_solomon': '22', 'isaiah': '23',
    'jeremiah': '24', 'lamentations': '25', 'ezekiel': '26', 'daniel': '27',
    'hosea': '28', 'joel': '29', 'amos': '30', 'obadiah': '31', 'jonah': '32',
    'micah': '33', 'nahum': '34', 'habakkuk': '35', 'zephaniah': '36',
    'haggai': '37', 'zechariah': '38', 'malachi': '39',
    'matthew': '40', 'mark': '41', 'luke': '42', 'john': '43', 'acts': '44',
    'romans': '45', '1_corinthians': '46', '2_corinthians': '47',
    'galatians': '48', 'ephesians': '49', 'philippians': '50',
    'colossians': '51', '1_thessalonians': '52', '2_thessalonians': '53',
    '1_timothy': '54', '2_timothy': '55', 'titus': '56', 'philemon': '57',
    'hebrews': '58', 'james': '59', '1_peter': '60', '2_peter': '61',
    '1_john': '62', '2_john': '63', '3_john': '64', 'jude': '65',
    'revelation': '66'
}

BOOK_NAME_TO_KEY = {
    'Genesis': 'genesis', 'Exodus': 'exodus', 'Leviticus': 'leviticus',
    'Numbers': 'numbers', 'Deuteronomy': 'deuteronomy', 'Joshua': 'joshua',
    'Judges': 'judges', 'Ruth': 'ruth', '1 Samuel': '1_samuel',
    '2 Samuel': '2_samuel', '1 Kings': '1_kings', '2 Kings': '2_kings',
    '1 Chronicles': '1_chronicles', '2 Chronicles': '2_chronicles',
    'Ezra': 'ezra', 'Nehemiah': 'nehemiah', 'Esther': 'esther', 'Job': 'job',
    'Psalm': 'psalms', 'Proverbs': 'proverbs', 'Ecclesiastes': 'ecclesiastes',
    'Song of Solomon': 'song_of_solomon', 'Isaiah': 'isaiah',
    'Jeremiah': 'jeremiah', 'Lamentations': 'lamentations',
    'Ezekiel': 'ezekiel', 'Daniel': 'daniel', 'Hosea': 'hosea', 'Joel': 'joel',
    'Amos': 'amos', 'Obadiah': 'obadiah', 'Jonah': 'jonah', 'Micah': 'micah',
    'Nahum': 'nahum', 'Habakkuk': 'habakkuk', 'Zephaniah': 'zephaniah',
    'Haggai': 'haggai', 'Zechariah': 'zechariah', 'Malachi': 'malachi',
    'Matthew': 'matthew', 'Mark': 'mark', 'Luke': 'luke', 'John': 'john',
    'Acts': 'acts', 'Romans': 'romans', '1 Corinthians': '1_corinthians',
    '2 Corinthians': '2_corinthians', 'Galatians': 'galatians',
    'Ephesians': 'ephesians', 'Philippians': 'philippians',
    'Colossians': 'colossians', '1 Thessalonians': '1_thessalonians',
    '2 Thessalonians': '2_thessalonians', '1 Timothy': '1_timothy',
    '2 Timothy': '2_timothy', 'Titus': 'titus', 'Philemon': 'philemon',
    'Hebrews': 'hebrews', 'James': 'james', '1 Peter': '1_peter',
    '2 Peter': '2_peter', '1 John': '1_john', '2 John': '2_john',
    '3 John': '3_john', 'Jude': 'jude', 'Revelation': 'revelation'
}

def parse_study_bible_crossrefs():
    """Parse esv_crossrefs_complete.txt into structured format."""
    file_path = Path('esv_crossrefs_complete.txt')
    text = file_path.read_text(encoding='utf-8')
    
    all_books = {}
    
    # Split by book sections
    sections = text.split('Cross-references for ')
    
    for section in sections[1:]:  # Skip first empty section
        lines = section.split('\n')
        book_name = lines[0].strip()
        
        if book_name not in BOOK_NAME_TO_KEY:
            print(f"Warning: Unknown book: {book_name}")
            continue
        
        book_key = BOOK_NAME_TO_KEY[book_name]
        
        # Parse cross-references for this book
        # Group by chapter:verse:letter
        book_data = defaultdict(lambda: defaultdict(list))
        
        # Pattern: chapter:verse letter reference_text
        pattern = r'(\d+):(\d+)\s+([a-z])\s+(.+?)(?=\s+\d+:\d+\s+[a-z]\s+|\Z)'
        
        full_text = '\n'.join(lines[1:])
        
        for match in re.finditer(pattern, full_text, re.DOTALL):
            chapter = int(match.group(1))
            verse = int(match.group(2))
            letter = match.group(3)
            ref_text = match.group(4).strip()
            
            book_data[chapter][(verse, letter)].append(ref_text)
        
        all_books[book_key] = book_data
    
    return all_books

def convert_to_raw_format(all_books, output_dir='raw/cross_refs_complete'):
    """Convert parsed data to raw format files."""
    output_path = Path(output_dir)
    
    total_chapters = 0
    total_refs = 0
    
    for book_key, chapters in all_books.items():
        book_num = BOOK_NUMBERS[book_key]
        book_dir = output_path / book_key
        book_dir.mkdir(parents=True, exist_ok=True)
        
        for chapter_num, verses in chapters.items():
            chapter_file = book_dir / f"{chapter_num}.txt"
            total_chapters += 1
            
            lines = []
            lines.append(f"C Chapter {chapter_num}")
            
            # Group by verse
            verse_groups = defaultdict(list)
            for (verse_num, letter), ref_texts in verses.items():
                verse_groups[verse_num].append((letter, ref_texts))
            
            for verse_num in sorted(verse_groups.keys()):
                # Verse marker
                verse_id = f"{book_num}{chapter_num:03d}{verse_num:03d}"
                lines.append(f"V {verse_id}")
                
                # Each cross-reference letter
                letter_data = sorted(verse_groups[verse_num], key=lambda x: x[0])
                
                for seq, (letter, ref_texts) in enumerate(letter_data, 1):
                    total_refs += 1
                    
                    lines.append(f"c {letter}")
                    lines.append(f"i c{verse_id}.{seq}")
                    
                    # Parse reference text to extract references
                    for ref_text in ref_texts:
                        # The reference text contains the actual scripture references
                        # For now, just store the text as-is with 'm' marker
                        lines.append(f"m {ref_text}")
            
            # Write chapter file
            chapter_file.write_text('\n'.join(lines) + '\n', encoding='utf-8')
    
    return total_chapters, total_refs

def main():
    print("Converting esv_crossrefs_complete.txt to raw format...")
    print("=" * 80)
    
    print("\n1. Parsing Study Bible cross-references...")
    all_books = parse_study_bible_crossrefs()
    
    total_books = len(all_books)
    total_chapter_count = sum(len(chapters) for chapters in all_books.values())
    total_verse_refs = sum(
        len(verses) 
        for chapters in all_books.values() 
        for verses in chapters.values()
    )
    
    print(f"   Found {total_books} books")
    print(f"   Found {total_chapter_count} chapters")
    print(f"   Found {total_verse_refs} verse references")
    
    print("\n2. Converting to raw format...")
    total_chapters, total_refs = convert_to_raw_format(all_books)
    
    print(f"   Created {total_chapters} chapter files")
    print(f"   Wrote {total_refs} cross-references")
    
    print("\n" + "=" * 80)
    print("✓ Conversion complete!")
    print(f"Output directory: raw/cross_refs_complete/")
    print()
    print("To use this data, you can:")
    print("  1. Compare with existing raw/cross_refs/")
    print("  2. Backup old raw/cross_refs/ and replace with new data")
    print("  3. Update your app to use raw/cross_refs_complete/")

if __name__ == '__main__':
    main()
