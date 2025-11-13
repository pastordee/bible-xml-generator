#!/usr/bin/env python3
"""
Compare cross-references from /raw/cross_refs with esv_crossrefs_complete.txt
to verify they contain the same data.
"""

import re
from pathlib import Path
from collections import defaultdict

def parse_raw_crossrefs(book_name, chapter_num):
    """Parse cross-references from /raw/cross_refs/{book}/{chapter}.txt"""
    file_path = Path(f'raw/cross_refs/{book_name}/{chapter_num}.txt')
    
    if not file_path.exists():
        return None
    
    crossrefs = defaultdict(list)
    current_verse = None
    current_letter = None
    
    content = file_path.read_text()
    
    for line in content.split('\n'):
        line = line.strip()
        
        # Verse marker: V 43007001
        if line.startswith('V '):
            verse_id = line.split()[1]
            # Extract verse number (last 3 digits)
            current_verse = int(verse_id[-3:])
        
        # Cross-reference letter: c p
        elif line.startswith('c ') and len(line.split()) == 2:
            current_letter = line.split()[1]
            if current_verse and current_letter:
                crossrefs[current_verse].append(current_letter)
    
    return crossrefs

def parse_studybible_crossrefs(book_name, chapter_num):
    """Parse cross-references from esv_crossrefs_complete.txt"""
    file_path = Path('esv_crossrefs_complete.txt')
    text = file_path.read_text()
    
    # Book name mapping
    book_mapping = {
        'genesis': 'Genesis',
        'exodus': 'Exodus',
        'leviticus': 'Leviticus',
        'numbers': 'Numbers',
        'deuteronomy': 'Deuteronomy',
        'joshua': 'Joshua',
        'judges': 'Judges',
        'ruth': 'Ruth',
        '1_samuel': '1 Samuel',
        '2_samuel': '2 Samuel',
        '1_kings': '1 Kings',
        '2_kings': '2 Kings',
        '1_chronicles': '1 Chronicles',
        '2_chronicles': '2 Chronicles',
        'ezra': 'Ezra',
        'nehemiah': 'Nehemiah',
        'esther': 'Esther',
        'job': 'Job',
        'psalms': 'Psalm',
        'proverbs': 'Proverbs',
        'ecclesiastes': 'Ecclesiastes',
        'song_of_solomon': 'Song of Solomon',
        'isaiah': 'Isaiah',
        'jeremiah': 'Jeremiah',
        'lamentations': 'Lamentations',
        'ezekiel': 'Ezekiel',
        'daniel': 'Daniel',
        'hosea': 'Hosea',
        'joel': 'Joel',
        'amos': 'Amos',
        'obadiah': 'Obadiah',
        'jonah': 'Jonah',
        'micah': 'Micah',
        'nahum': 'Nahum',
        'habakkuk': 'Habakkuk',
        'zephaniah': 'Zephaniah',
        'haggai': 'Haggai',
        'zechariah': 'Zechariah',
        'malachi': 'Malachi',
        'matthew': 'Matthew',
        'mark': 'Mark',
        'luke': 'Luke',
        'john': 'John',
        'acts': 'Acts',
        'romans': 'Romans',
        '1_corinthians': '1 Corinthians',
        '2_corinthians': '2 Corinthians',
        'galatians': 'Galatians',
        'ephesians': 'Ephesians',
        'philippians': 'Philippians',
        'colossians': 'Colossians',
        '1_thessalonians': '1 Thessalonians',
        '2_thessalonians': '2 Thessalonians',
        '1_timothy': '1 Timothy',
        '2_timothy': '2 Timothy',
        'titus': 'Titus',
        'philemon': 'Philemon',
        'hebrews': 'Hebrews',
        'james': 'James',
        '1_peter': '1 Peter',
        '2_peter': '2 Peter',
        '1_john': '1 John',
        '2_john': '2 John',
        '3_john': '3 John',
        'jude': 'Jude',
        'revelation': 'Revelation'
    }
    
    study_book = book_mapping.get(book_name, book_name.capitalize())
    
    # Find the book section
    book_pattern = rf'Cross-references for {study_book}'
    book_match = re.search(book_pattern, text, re.IGNORECASE)
    
    if not book_match:
        return None
    
    # Get text from this book section until next book
    start = book_match.end()
    next_book = re.search(r'Cross-references for [A-Z]', text[start:])
    if next_book:
        book_text = text[start:start + next_book.start()]
    else:
        book_text = text[start:]
    
    # Find all references for this chapter
    crossrefs = defaultdict(list)
    pattern = rf'{chapter_num}:(\d+)\s+([a-z])\s+'
    matches = re.findall(pattern, book_text)
    
    for verse, letter in matches:
        crossrefs[int(verse)].append(letter)
    
    return crossrefs

def compare_sources(book_name, chapter_num):
    """Compare cross-references from both sources."""
    raw_refs = parse_raw_crossrefs(book_name, chapter_num)
    study_refs = parse_studybible_crossrefs(book_name, chapter_num)
    
    if raw_refs is None:
        return None, f"Raw file not found: raw/cross_refs/{book_name}/{chapter_num}.txt"
    
    if study_refs is None:
        return None, f"Study Bible section not found for {book_name}"
    
    # Compare
    all_verses = sorted(set(list(raw_refs.keys()) + list(study_refs.keys())))
    
    mismatches = []
    matches = 0
    
    for verse in all_verses:
        raw_list = sorted(raw_refs.get(verse, []))
        study_list = sorted(study_refs.get(verse, []))
        
        if raw_list == study_list:
            matches += 1
        else:
            mismatches.append({
                'verse': verse,
                'raw': raw_list,
                'study_bible': study_list,
                'missing_from_raw': sorted(set(study_list) - set(raw_list)),
                'extra_in_raw': sorted(set(raw_list) - set(study_list))
            })
    
    return {
        'matches': matches,
        'mismatches': mismatches,
        'total_verses': len(all_verses)
    }, None

def main():
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python3 compare_crossref_sources.py <book> <chapter>")
        print("Example: python3 compare_crossref_sources.py john 7")
        print()
        print("Or run comparison for all books:")
        print("  python3 compare_crossref_sources.py --all")
        return
    
    if sys.argv[1] == '--all':
        # Compare all books
        print("Comparing all cross-references...")
        print("=" * 80)
        
        total_matches = 0
        total_mismatches = 0
        books_with_differences = []
        
        raw_dir = Path('raw/cross_refs')
        for book_dir in sorted(raw_dir.iterdir()):
            if not book_dir.is_dir():
                continue
            
            book_name = book_dir.name
            
            for chapter_file in sorted(book_dir.glob('*.txt')):
                chapter_num = chapter_file.stem
                
                result, error = compare_sources(book_name, chapter_num)
                
                if error:
                    print(f"⚠ {book_name} {chapter_num}: {error}")
                    continue
                
                if result['mismatches']:
                    books_with_differences.append((book_name, chapter_num, result))
                    total_mismatches += len(result['mismatches'])
                
                total_matches += result['matches']
        
        print()
        print("=" * 80)
        print("SUMMARY")
        print("=" * 80)
        print(f"Verses matching: {total_matches}")
        print(f"Verses with differences: {total_mismatches}")
        
        if books_with_differences:
            print()
            print(f"Books/chapters with differences: {len(books_with_differences)}")
            for book, chapter, result in books_with_differences[:10]:
                print(f"  {book} {chapter}: {len(result['mismatches'])} verses differ")
            if len(books_with_differences) > 10:
                print(f"  ... and {len(books_with_differences) - 10} more")
        
        return
    
    book_name = sys.argv[1]
    chapter_num = sys.argv[2]
    
    print(f"Comparing {book_name} chapter {chapter_num}")
    print("=" * 80)
    print()
    
    result, error = compare_sources(book_name, chapter_num)
    
    if error:
        print(f"Error: {error}")
        return
    
    print(f"Total verses: {result['total_verses']}")
    print(f"Matching verses: {result['matches']}")
    print(f"Verses with differences: {len(result['mismatches'])}")
    print()
    
    if result['mismatches']:
        print("DIFFERENCES:")
        print("-" * 80)
        for mismatch in result['mismatches']:
            print(f"\nVerse {mismatch['verse']}:")
            print(f"  Raw file:     {mismatch['raw']}")
            print(f"  Study Bible:  {mismatch['study_bible']}")
            if mismatch['missing_from_raw']:
                print(f"  Missing from raw: {mismatch['missing_from_raw']}")
            if mismatch['extra_in_raw']:
                print(f"  Extra in raw: {mismatch['extra_in_raw']}")
    else:
        print("✓ All cross-references match perfectly!")

if __name__ == '__main__':
    main()
