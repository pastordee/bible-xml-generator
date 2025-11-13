#!/usr/bin/env python3
"""
Generate a CSV file of all missing cross-references for easy manual addition.
"""

import re
import csv
from pathlib import Path

def parse_report(report_file):
    """Parse the comparison report to extract missing cross-references."""
    text = Path(report_file).read_text(encoding='utf-8')
    
    missing_refs = []
    
    # Read line by line
    lines = text.split('\n')
    current_book = None
    current_chapter = None
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        # Check if this is a chapter header (book name followed by dashes)
        if line and i + 1 < len(lines) and lines[i + 1].strip().startswith('---'):
            # Parse book and chapter from line like "1 CHRONICLES 1"
            parts = line.rsplit(' ', 1)
            if len(parts) == 2 and parts[1].isdigit():
                current_book = parts[0]
                current_chapter = parts[1]
        
        # Check for missing line like "    → MISSING: n"
        elif line.startswith('→ MISSING:'):
            letters_str = line.replace('→ MISSING:', '').strip()
            letter_list = [l.strip() for l in letters_str.split(',')]
            
            # Look back for verse number
            verse_num = None
            for j in range(i - 1, max(0, i - 5), -1):
                verse_match = re.match(r'\s*Verse (\d+):', lines[j])
                if verse_match:
                    verse_num = verse_match.group(1)
                    break
            
            if current_book and current_chapter and verse_num:
                for letter in letter_list:
                    missing_refs.append({
                        'book': current_book,
                        'chapter': current_chapter,
                        'verse': verse_num,
                        'letter': letter
                    })
        
        i += 1
    
    return missing_refs

def generate_csv(missing_refs, output_file):
    """Generate CSV file with missing cross-references."""
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['book', 'chapter', 'verse', 'letter', 'added'])
        writer.writeheader()
        
        for ref in missing_refs:
            ref['added'] = 'NO'  # Track which ones have been added
            writer.writerow(ref)
    
    print(f"✓ CSV file saved: {output_file}")
    print(f"  Total missing cross-references: {len(missing_refs)}")

def generate_checklist(missing_refs, output_file):
    """Generate a human-readable checklist organized by book."""
    from collections import defaultdict
    
    by_book = defaultdict(list)
    
    for ref in missing_refs:
        key = ref['book']
        by_book[key].append(ref)
    
    lines = []
    lines.append("="*80)
    lines.append("ESV MISSING CROSS-REFERENCES - CHECKLIST")
    lines.append("="*80)
    lines.append("")
    lines.append(f"Total missing: {len(missing_refs)} cross-references across {len(by_book)} books")
    lines.append("")
    lines.append("Instructions:")
    lines.append("1. For each entry, locate the verse in your ESV Study Bible")
    lines.append("2. Find where letter marker appears in the verse text")
    lines.append("3. Add <crossref let=\"X\" cid=\"...\"></crossref> at that position")
    lines.append("4. Mark as [X] when completed")
    lines.append("")
    lines.append("="*80)
    lines.append("")
    
    for book in sorted(by_book.keys()):
        refs = by_book[book]
        lines.append(f"\n{book} ({len(refs)} missing)")
        lines.append("-"*80)
        
        # Group by chapter
        by_chapter = defaultdict(list)
        for ref in refs:
            by_chapter[ref['chapter']].append(ref)
        
        for chapter in sorted(by_chapter.keys(), key=int):
            chapter_refs = by_chapter[chapter]
            lines.append(f"\n  Chapter {chapter}:")
            
            # Group by verse
            by_verse = defaultdict(list)
            for ref in chapter_refs:
                by_verse[ref['verse']].append(ref['letter'])
            
            for verse in sorted(by_verse.keys(), key=int):
                letters = ', '.join(sorted(by_verse[verse]))
                lines.append(f"    [ ] Verse {verse}: Add letters {letters}")
    
    lines.append("\n" + "="*80)
    
    Path(output_file).write_text('\n'.join(lines), encoding='utf-8')
    print(f"✓ Checklist saved: {output_file}")

def generate_json(missing_refs, output_file):
    """Generate JSON file for programmatic access."""
    import json
    from collections import defaultdict
    
    # Organize by book > chapter > verse
    organized = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
    
    for ref in missing_refs:
        book = ref['book']
        chapter = int(ref['chapter'])
        verse = int(ref['verse'])
        letter = ref['letter']
        
        organized[book][chapter][verse].append(letter)
    
    # Convert to regular dicts for JSON
    output = {}
    for book, chapters in organized.items():
        output[book] = {}
        for chapter, verses in chapters.items():
            output[book][str(chapter)] = {}
            for verse, letters in verses.items():
                output[book][str(chapter)][str(verse)] = sorted(letters)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2)
    
    print(f"✓ JSON file saved: {output_file}")

def main():
    print("="*80)
    print("MISSING CROSS-REFERENCES EXPORT TOOL")
    print("="*80)
    print()
    
    report_file = Path('crossref_comparison_report.txt')
    
    if not report_file.exists():
        print(f"Error: {report_file} not found!")
        print("Please run parse_all_crossrefs.py first to generate the comparison report.")
        return
    
    print("Parsing comparison report...")
    missing_refs = parse_report(report_file)
    
    print(f"Found {len(missing_refs)} missing cross-references")
    print()
    
    # Generate CSV
    print("Generating CSV file...")
    generate_csv(missing_refs, 'missing_crossrefs.csv')
    print()
    
    # Generate checklist
    print("Generating checklist...")
    generate_checklist(missing_refs, 'missing_crossrefs_checklist.txt')
    print()
    
    # Generate JSON
    print("Generating JSON file...")
    generate_json(missing_refs, 'missing_crossrefs.json')
    print()
    
    print("="*80)
    print("SUMMARY")
    print("="*80)
    print(f"Total missing cross-references: {len(missing_refs)}")
    print()
    print("Files created:")
    print("  1. missing_crossrefs.csv - Spreadsheet format (Excel/Numbers)")
    print("  2. missing_crossrefs_checklist.txt - Human-readable checklist")
    print("  3. missing_crossrefs.json - Structured data (for scripts)")
    print()
    print("Recommended workflow:")
    print("  1. Open missing_crossrefs_checklist.txt to see organized list")
    print("  2. Open CSV in spreadsheet app to track progress")
    print("  3. Reference your ESV Study Bible to find exact positions")
    print("  4. Add <crossref> elements to XML files")
    print("="*80)

if __name__ == '__main__':
    main()
