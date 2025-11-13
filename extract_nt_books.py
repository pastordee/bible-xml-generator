#!/usr/bin/env python3
"""
Extract Acts-Revelation cross-references from NKJV Study Bible format
"""
import re
import subprocess
import os

# Bible book keywords for filtering
BOOK_KEYWORDS = [
    'Gen.', 'Ex.', 'Lev.', 'Num.', 'Deut.', 'Josh.', 'Judg.', 'Ruth', '1 Sam.', '2 Sam.',
    '1 Kin.', '2 Kin.', '1 Chr.', '2 Chr.', 'Ezra', 'Neh.', 'Esth.', 'Job', 'Ps.', 'Prov.',
    'Eccl.', 'Song', 'Is.', 'Jer.', 'Lam.', 'Ezek.', 'Dan.', 'Hos.', 'Joel', 'Amos',
    'Obad.', 'Jon.', 'Mic.', 'Nah.', 'Hab.', 'Zeph.', 'Hag.', 'Zech.', 'Mal.',
    'Matt.', 'Mark', 'Luke', 'John', 'Acts', 'Rom.', '1 Cor.', '2 Cor.', 'Gal.', 'Eph.',
    'Phil.', 'Col.', '1 Thess.', '2 Thess.', '1 Tim.', '2 Tim.', 'Titus', 'Philem.', 'Heb.',
    'James', '1 Pet.', '2 Pet.', '1 John', '2 John', '3 John', 'Jude', 'Rev.'
]

# NT book definitions (book_name, chapter_count)
NT_BOOKS = [
    ('acts', 28), ('romans', 16), ('1corinthians', 16), ('2corinthians', 13),
    ('galatians', 6), ('ephesians', 6), ('philippians', 4), ('colossians', 4),
    ('1thessalonians', 5), ('2thessalonians', 3), ('1timothy', 6), ('2timothy', 4),
    ('titus', 3), ('philemon', 1), ('hebrews', 13), ('james', 5),
    ('1peter', 5), ('2peter', 3), ('1john', 5), ('2john', 1), ('3john', 1),
    ('jude', 1), ('revelation', 22)
]

# Book title patterns to find in the file
BOOK_PATTERNS = [
    ('acts', 'ACTS'),
    ('romans', 'ROMANS'),
    ('1corinthians', '1 CORINTHIANS'),
    ('2corinthians', '2 CORINTHIANS'),
    ('galatians', 'GALATIANS'),
    ('ephesians', 'EPHESIANS'),
    ('philippians', 'PHILIPPIANS'),
    ('colossians', 'COLOSSIANS'),
    ('1thessalonians', '1 THESSALONIANS'),
    ('2thessalonians', '2 THESSALONIANS'),
    ('1timothy', '1 TIMOTHY'),
    ('2timothy', '2 TIMOTHY'),
    ('titus', 'TITUS'),
    ('philemon', 'PHILEMON'),
    ('hebrews', 'HEBREWS'),
    ('james', 'JAMES'),
    ('1peter', '1 PETER'),
    ('2peter', '2 PETER'),
    ('1john', '1 JOHN'),
    ('2john', '2 JOHN'),
    ('3john', '3 JOHN'),
    ('jude', 'JUDE'),
    ('revelation', 'REVELATION')
]

def is_crossref_line(line):
    """Check if a line is a cross-reference"""
    stripped = line.strip()
    # Must start with number + letter and contain a book reference
    if re.match(r'^\d+\s+[a-z]\s+', stripped):
        return any(keyword in stripped for keyword in BOOK_KEYWORDS)
    return False

def extract_book(lines, book_name, chapter_count, start_line, end_line, book_pattern):
    """Extract cross-references for one book"""
    print(f"\nProcessing {book_name.upper()}: chapters 1-{chapter_count}")
    
    # Get the book's section
    book_lines = lines[start_line:end_line] if end_line else lines[start_line:]
    
    # Find chapter markers using verse references like "ACTS 1:1"
    chapters = {}
    current_chapter = None
    
    for i, line in enumerate(book_lines):
        # Check for verse reference marker (e.g., "ACTS 1:1", "ROMANS 2:5")
        verse_match = re.match(rf'^{book_pattern}\s+(\d+):', line.strip())
        if verse_match:
            new_chapter = int(verse_match.group(1))
            # Only update if it's a new chapter
            if new_chapter != current_chapter:
                current_chapter = new_chapter
                if current_chapter not in chapters:
                    chapters[current_chapter] = []
        
        # Alternative: Check for "CHAPTER X" marker
        ch_match = re.match(r'^CHAPTER (\d+)', line.strip())
        if ch_match and current_chapter is None:
            current_chapter = int(ch_match.group(1))
            if current_chapter not in chapters:
                chapters[current_chapter] = []
        
        # Collect cross-references for current chapter
        if current_chapter and is_crossref_line(line):
            chapters[current_chapter].append(line.strip())
    
    # Write each chapter
    written = 0
    for ch in range(1, chapter_count + 1):
        if ch in chapters and chapters[ch]:
            filename = f"{book_name}_ch{ch}_raw.txt"
            with open(filename, 'w') as f:
                for ref in chapters[ch]:
                    f.write(ref + '\n')
            print(f"  ✓ {filename}: {len(chapters[ch])} refs")
            written += 1
        else:
            print(f"  ✗ {book_name} chapter {ch}: No refs found")
    
    return written

def main():
    filepath = 'raw/cross_refs_nkjv/acts_to_revlations.txt'
    
    print("="*70)
    print("EXTRACTING NEW TESTAMENT CROSS-REFERENCES")
    print("="*70)
    
    # Read the file
    with open(filepath, 'r') as f:
        lines = f.readlines()
    
    print(f"Loaded {len(lines)} lines from {filepath}")
    
    # Find book boundaries
    book_positions = []
    for i, line in enumerate(lines):
        for book_name, pattern in BOOK_PATTERNS:
            if line.strip().startswith(pattern + ' ') or line.strip() == pattern:
                book_positions.append((i, book_name, pattern))
                break
    
    print(f"Found {len(book_positions)} book markers")
    
    # Process each book
    total_written = 0
    for idx, (book_name, chapter_count) in enumerate(NT_BOOKS):
        # Find this book's start position and pattern
        start_pos = None
        end_pos = None
        book_pattern = None
        
        for i, (pos, bname, pattern) in enumerate(book_positions):
            if bname == book_name:
                start_pos = pos
                book_pattern = pattern
                # Next book's position is the end
                if i + 1 < len(book_positions):
                    end_pos = book_positions[i + 1][0]
                break
        
        if start_pos is None:
            print(f"\n⚠ {book_name.upper()}: Not found in file!")
            continue
        
        written = extract_book(lines, book_name, chapter_count, start_pos, end_pos, book_pattern)
        total_written += written
    
    print("\n" + "="*70)
    print(f"EXTRACTION COMPLETE: {total_written} chapters written")
    print("="*70)

if __name__ == '__main__':
    main()
