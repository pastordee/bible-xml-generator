#!/usr/bin/env python3
"""
Extract cross-references from acts_to_revlations.txt file
This file has a different format than nkjv2_trimmed.txt
"""

import re
import subprocess

# NT book chapter counts
nt_books = [
    ('acts', 28), ('romans', 16), ('1corinthians', 16), ('2corinthians', 13),
    ('galatians', 6), ('ephesians', 6), ('philippians', 4), ('colossians', 4),
    ('1thessalonians', 5), ('2thessalonians', 3), ('1timothy', 6), ('2timothy', 4),
    ('titus', 3), ('philemon', 1), ('hebrews', 13), ('james', 5),
    ('1peter', 5), ('2peter', 3), ('1john', 5), ('2john', 1), ('3john', 1),
    ('jude', 1), ('revelation', 22)
]

book_keywords = [
    'Gen.', 'Ex.', 'Lev.', 'Num.', 'Deut.', 'Josh.', 'Judg.', 'Ruth', '1 Sam.', '2 Sam.',
    '1 Kin.', '2 Kin.', '1 Chr.', '2 Chr.', 'Ezra', 'Neh.', 'Esth.', 'Job', 'Ps.', 'Prov.',
    'Eccl.', 'Song', 'Is.', 'Jer.', 'Lam.', 'Ezek.', 'Dan.', 'Hos.', 'Joel', 'Amos',
    'Obad.', 'Jon.', 'Mic.', 'Nah.', 'Hab.', 'Zeph.', 'Hag.', 'Zech.', 'Mal.',
    'Matt.', 'Mark', 'Luke', 'John', 'Acts', 'Rom.', '1 Cor.', '2 Cor.', 'Gal.', 'Eph.',
    'Phil.', 'Col.', '1 Thess.', '2 Thess.', '1 Tim.', '2 Tim.', 'Titus', 'Philem.', 'Heb.',
    'James', '1 Pet.', '2 Pet.', '1 John', '2 John', '3 John', 'Jude', 'Rev.'
]

def extract_crossrefs_from_study_bible():
    """Extract cross-references from the formatted study Bible text"""
    
    with open('raw/cross_refs_nkjv/acts_to_revlations.txt', 'r') as f:
        content = f.read()
    
    lines = content.split('\n')
    
    # Track current book/chapter as we scan
    current_book = None
    current_chapter = None
    chapter_refs = {}
    
    for i, line in enumerate(lines):
        # Check for book introduction headers
        if 'ACTS INTRODUCTION' in line or line.strip() == 'The Acts':
            current_book = 'acts'
            current_chapter = None
        elif 'ROMANS INTRODUCTION' in line or (line.strip() == 'Romans' and i < 10000):
            current_book = 'romans'
            current_chapter = None
        # Add more book markers...
        
        # Check for chapter markers
        chapter_match = re.match(r'CHAPTER\s+(\d+)', line)
        if chapter_match and current_book:
            current_chapter = int(chapter_match.group(1))
            key = (current_book, current_chapter)
            if key not in chapter_refs:
                chapter_refs[key] = []
        
        # Extract cross-reference lines
        # Pattern: "verse# letter book:chapter" like "1 a Luke 1:3"
        ref_match = re.match(r'^(\d+)\s+([a-z])\s+(.+)$', line.strip())
        if ref_match and current_book and current_chapter:
            verse_num = ref_match.group(1)
            letter = ref_match.group(2)
            references = ref_match.group(3)
            
            # Check if this contains actual book references
            if any(keyword in references for keyword in book_keywords):
                key = (current_book, current_chapter)
                chapter_refs[key].append(line.strip())
    
    return chapter_refs

def main():
    print("="*70)
    print("EXTRACTING ACTS-REVELATION CROSS-REFERENCES")
    print("="*70)
    print()
    
    chapter_refs = extract_crossrefs_from_study_bible()
    
    print(f"Found cross-references for {len(chapter_refs)} chapters")
    
    # Display sample
    for key in list(chapter_refs.keys())[:5]:
        book, ch = key
        refs = chapter_refs[key]
        print(f"\n{book.upper()} Chapter {ch}: {len(refs)} references")
        for ref in refs[:3]:
            print(f"  {ref}")

if __name__ == '__main__':
    main()
