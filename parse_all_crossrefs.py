#!/usr/bin/env python3
"""
Extract and parse all ESV cross-references from the complete file.
"""

import re
from collections import defaultdict
from pathlib import Path
import xml.etree.ElementTree as ET

# Book name mappings
BOOK_MAPPINGS = {
    'Genesis': 'genesis',
    'Exodus': 'exodus',
    'Leviticus': 'leviticus',
    'Numbers': 'numbers',
    'Deuteronomy': 'deuteronomy',
    'Joshua': 'joshua',
    'Judges': 'judges',
    'Ruth': 'ruth',
    '1 Samuel': '1_samuel',
    '2 Samuel': '2_samuel',
    '1 Kings': '1_kings',
    '2 Kings': '2_kings',
    '1 Chronicles': '1_chronicles',
    '2 Chronicles': '2_chronicles',
    'Ezra': 'ezra',
    'Nehemiah': 'nehemiah',
    'Esther': 'esther',
    'Job': 'job',
    'Psalm': 'psalms',
    'Proverbs': 'proverbs',
    'Ecclesiastes': 'ecclesiastes',
    'Song of Solomon': 'song_of_solomon',
    'Isaiah': 'isaiah',
    'Jeremiah': 'jeremiah',
    'Lamentations': 'lamentations',
    'Ezekiel': 'ezekiel',
    'Daniel': 'daniel',
    'Hosea': 'hosea',
    'Joel': 'joel',
    'Amos': 'amos',
    'Obadiah': 'obadiah',
    'Jonah': 'jonah',
    'Micah': 'micah',
    'Nahum': 'nahum',
    'Habakkuk': 'habakkuk',
    'Zephaniah': 'zephaniah',
    'Haggai': 'haggai',
    'Zechariah': 'zechariah',
    'Malachi': 'malachi',
    'Matthew': 'matthew',
    'Mark': 'mark',
    'Luke': 'luke',
    'John': 'john',
    'Acts': 'acts',
    'Romans': 'romans',
    '1 Corinthians': '1_corinthians',
    '2 Corinthians': '2_corinthians',
    'Galatians': 'galatians',
    'Ephesians': 'ephesians',
    'Philippians': 'philippians',
    'Colossians': 'colossians',
    '1 Thessalonians': '1_thessalonians',
    '2 Thessalonians': '2_thessalonians',
    '1 Timothy': '1_timothy',
    '2 Timothy': '2_timothy',
    'Titus': 'titus',
    'Philemon': 'philemon',
    'Hebrews': 'hebrews',
    'James': 'james',
    '1 Peter': '1_peter',
    '2 Peter': '2_peter',
    '1 John': '1_john',
    '2 John': '2_john',
    '3 John': '3_john',
    'Jude': 'jude',
    'Revelation': 'revelation'
}

def extract_all_crossrefs(filepath):
    """Extract all cross-references from the ESV file."""
    print("Reading ESV cross-reference file...")
    text = Path(filepath).read_text(encoding='utf-8')
    
    # Find all "Cross-references for {Book}" sections
    book_pattern = r'Cross-references for (.+?)\n((?:\d+:\d+\s+[a-z]\s+.+?\n?)+)'
    
    all_books = {}
    
    # Split by book sections
    sections = text.split('Cross-references for ')
    print(f"Found {len(sections)} sections")
    
    for section in sections[1:]:  # Skip first empty section
        lines = section.split('\n')
        book_name = lines[0].strip()
        
        if book_name not in BOOK_MAPPINGS:
            print(f"  Skipping unknown book: {book_name}")
            continue
        
        print(f"Processing {book_name}...")
        
        # Parse cross-references for this book
        book_crossrefs = defaultdict(lambda: defaultdict(list))
        
        # Pattern: chapter:verse letter reference
        pattern = r'(\d+):(\d+)\s+([a-z])\s+'
        
        for line in lines[1:]:
            if not line.strip() or line.startswith('Cross-references for'):
                break
            
            matches = re.finditer(pattern, line)
            for match in matches:
                chapter = int(match.group(1))
                verse = int(match.group(2))
                letter = match.group(3)
                
                book_crossrefs[chapter][verse].append(letter)
        
        all_books[book_name] = book_crossrefs
    
    return all_books

def get_xml_crossrefs(xml_file):
    """Extract cross-references from XML file."""
    if not xml_file.exists():
        return {}
    
    try:
        tree = ET.parse(xml_file)
        root = tree.getroot()
        
        xml_crossrefs = defaultdict(list)
        for crossref in root.findall('.//crossref'):
            cid = crossref.get('cid', '')
            letter = crossref.get('let', '')
            if cid.startswith('c'):
                verse_id = cid[1:9]
                verse_num = int(verse_id[-3:])
                xml_crossrefs[verse_num].append(letter)
        
        return xml_crossrefs
    except Exception as e:
        print(f"  Error reading {xml_file}: {e}")
        return {}

def compare_all_books(all_books, xml_dir='xml_esv'):
    """Compare all books with XML files."""
    results = {}
    xml_path = Path(xml_dir)
    
    for book_name, chapters in all_books.items():
        book_file = BOOK_MAPPINGS[book_name]
        
        for chapter_num, verses in chapters.items():
            xml_file = xml_path / f"{book_file}_{chapter_num}.xml"
            xml_refs = get_xml_crossrefs(xml_file)
            
            mismatches = []
            missing_total = 0
            extra_total = 0
            
            all_verses = sorted(set(list(verses.keys()) + list(xml_refs.keys())))
            
            for verse_num in all_verses:
                study_refs = verses.get(verse_num, [])
                xml_list = xml_refs.get(verse_num, [])
                
                if study_refs != xml_list:
                    study_set = set(study_refs)
                    xml_set = set(xml_list)
                    
                    missing = study_set - xml_set
                    extra = xml_set - study_set
                    
                    if missing or extra:
                        mismatches.append({
                            'verse': verse_num,
                            'study_bible': study_refs,
                            'xml': xml_list,
                            'missing': sorted(missing),
                            'extra': sorted(extra)
                        })
                        missing_total += len(missing)
                        extra_total += len(extra)
            
            if mismatches:  # Only record if there are issues
                key = (book_name, chapter_num)
                results[key] = {
                    'study_bible_total': sum(len(refs) for refs in verses.values()),
                    'xml_total': sum(len(refs) for refs in xml_refs.values()),
                    'mismatches': mismatches,
                    'missing_total': missing_total,
                    'extra_total': extra_total
                }
    
    return results

def generate_report(results, output_file='crossref_comparison_report.txt'):
    """Generate comprehensive report."""
    lines = []
    lines.append("="*80)
    lines.append("ESV BIBLE - COMPLETE CROSS-REFERENCE COMPARISON")
    lines.append("="*80)
    lines.append("")
    
    grand_total_missing = 0
    grand_total_extra = 0
    
    for (book, chapter), result in sorted(results.items()):
        grand_total_missing += result['missing_total']
        grand_total_extra += result['extra_total']
        
        lines.append(f"\n{book.upper()} {chapter}")
        lines.append("-"*80)
        lines.append(f"Study Bible: {result['study_bible_total']} cross-refs")
        lines.append(f"XML:         {result['xml_total']} cross-refs")
        lines.append(f"Missing:     {result['missing_total']}")
        lines.append(f"Extra:       {result['extra_total']}")
        lines.append("")
        
        for mismatch in result['mismatches']:
            lines.append(f"  Verse {mismatch['verse']}:")
            lines.append(f"    Study Bible: {', '.join(mismatch['study_bible']) if mismatch['study_bible'] else '(none)'}")
            lines.append(f"    XML:         {', '.join(mismatch['xml']) if mismatch['xml'] else '(none)'}")
            if mismatch['missing']:
                lines.append(f"    → MISSING: {', '.join(mismatch['missing'])}")
            if mismatch['extra']:
                lines.append(f"    → EXTRA:   {', '.join(mismatch['extra'])}")
    
    # Grand summary
    lines.append("\n" + "="*80)
    lines.append("GRAND SUMMARY")
    lines.append("="*80)
    lines.append(f"Chapters with issues: {len(results)}")
    lines.append(f"Total missing cross-references: {grand_total_missing}")
    lines.append(f"Total extra cross-references: {grand_total_extra}")
    lines.append("="*80)
    
    report = '\n'.join(lines)
    Path(output_file).write_text(report, encoding='utf-8')
    
    print(f"\n✓ Report saved to {output_file}")
    return report

def main():
    filepath = 'esv_crossrefs_complete.txt'
    
    print("="*80)
    print("ESV CROSS-REFERENCE COMPARISON TOOL")
    print("="*80)
    print()
    
    # Extract all cross-references
    all_books = extract_all_crossrefs(filepath)
    
    print(f"\n✓ Extracted cross-references for {len(all_books)} books")
    
    # Compare with XML
    print("\nComparing with XML files...")
    results = compare_all_books(all_books)
    
    # Generate report
    report = generate_report(results)
    
    # Print summary
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    print(f"Chapters with mismatches: {len(results)}")
    print(f"Total missing: {sum(r['missing_total'] for r in results.values())}")
    print(f"Total extra: {sum(r['extra_total'] for r in results.values())}")
    print("="*80)

if __name__ == '__main__':
    main()
