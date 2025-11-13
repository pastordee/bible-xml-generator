#!/usr/bin/env python3
"""
Simple extraction: Use CHAPTER markers to segment the file
"""
import re

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

# Books and their chapter counts
BOOKS = [
    ('acts', 28), ('romans', 16), ('1corinthians', 16), ('2corinthians', 13),
    ('galatians', 6), ('ephesians', 6), ('philippians', 4), ('colossians', 4),
    ('1thessalonians', 5), ('2thessalonians', 3), ('1timothy', 6), ('2timothy', 4),
    ('titus', 3), ('philemon', 1), ('hebrews', 13), ('james', 5),
    ('1peter', 5), ('2peter', 3), ('1john', 5), ('2john', 1), ('3john', 1),
    ('jude', 1), ('revelation', 22)
]

def is_crossref_line(line):
    """Check if line is a cross-reference"""
    stripped = line.strip()
    # Must start with number + letter and contain a book keyword
    if re.match(r'^\d+\s+[a-z]\s+', stripped):
        return any(keyword in stripped for keyword in BOOK_KEYWORDS)
    return False

print("="*70)
print("EXTRACTING NT CROSS-REFERENCES BY CHAPTER MARKER")
print("="*70)

with open('raw/cross_refs_nkjv/acts_to_revlations.txt', 'r') as f:
    lines = f.readlines()

print(f"Loaded {len(lines)} lines")

# Find all CHAPTER markers
chapter_markers = []
for i, line in enumerate(lines):
    if re.match(r'^CHAPTER \d+$', line.strip()):
        ch_num = int(re.match(r'^CHAPTER (\d+)', line.strip()).group(1))
        chapter_markers.append((i, ch_num))

print(f"Found {len(chapter_markers)} CHAPTER markers")
print(f"First few: {chapter_markers[:10]}")

# Extract cross-references between chapter markers
chapters_data = []
for i, (line_num, ch_num) in enumerate(chapter_markers):
    # Find the end of this chapter (start of next chapter)
    if i + 1 < len(chapter_markers):
        end_line = chapter_markers[i + 1][0]
    else:
        end_line = len(lines)
    
    # Extract cross-ref lines
    crossrefs = []
    for line in lines[line_num + 1:end_line]:
        if is_crossref_line(line):
            crossrefs.append(line.strip())
    
    chapters_data.append((ch_num, crossrefs))
    if len(crossrefs) > 0 and ch_num <= 3:
        print(f"\nChapter {ch_num}: {len(crossrefs)} refs")
        for ref in crossrefs[:3]:
            print(f"  {ref[:70]}")

# Now assign chapters to books
print("\n" + "="*70)
print("ASSIGNING CHAPTERS TO BOOKS")
print("="*70)

chapter_idx = 0
total_written = 0

for book_name, chapter_count in BOOKS:
    print(f"\n{book_name.upper()}: expecting {chapter_count} chapters")
    
    for ch in range(1, chapter_count + 1):
        if chapter_idx < len(chapters_data):
            ch_num, crossrefs = chapters_data[chapter_idx]
            
            if len(crossrefs) > 0:
                filename = f"{book_name}_ch{ch}_raw.txt"
                with open(filename, 'w') as f:
                    for ref in crossrefs:
                        f.write(ref + '\n')
                print(f"  ✓ {filename}: {len(crossrefs)} refs")
                total_written += 1
            else:
                print(f"  ✗ {book_name} ch{ch}: No refs")
            
            chapter_idx += 1
        else:
            print(f"  ✗ {book_name} ch{ch}: Out of data")

print("\n" + "="*70)
print(f"COMPLETE: {total_written}/{chapter_idx} chapters written")
print("="*70)
