#!/usr/bin/env python3
"""
Parse complete cross-reference data from ESV Study Bible reference list.
This script will:
1. Parse cross-reference text for all chapters
2. Compare with existing XML files
3. Generate a report of missing cross-references
4. Optionally create a data file for adding missing ones
"""

import re
from collections import defaultdict
from pathlib import Path
import xml.etree.ElementTree as ET

def parse_crossref_text(text, book_name, chapter_num):
    """
    Parse cross-reference text format like '7:1 p ch. 5:18...'
    Returns dict of {verse_num: [letters]}
    """
    crossrefs = defaultdict(list)
    
    # Pattern: chapter:verse letter(s)
    # Example: "7:1 p ch. 5:18; 8:37, 40; 11:53"
    pattern = rf'{chapter_num}:(\d+)\s+([a-z])\s+'
    
    matches = re.finditer(pattern, text)
    for match in matches:
        verse_num = int(match.group(1))
        letter = match.group(2)
        crossrefs[verse_num].append(letter)
    
    return crossrefs

def get_xml_crossrefs(xml_file):
    """Extract cross-references from XML file."""
    if not xml_file.exists():
        return {}
    
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

def compare_chapter(book_name, chapter_num, crossref_text, xml_dir):
    """Compare one chapter's cross-references."""
    study_bible_refs = parse_crossref_text(crossref_text, book_name, chapter_num)
    
    # Get XML file path
    xml_file = xml_dir / f"{book_name.lower().replace(' ', '_')}_{chapter_num}.xml"
    xml_refs = get_xml_crossrefs(xml_file)
    
    # Calculate differences
    mismatches = []
    missing_total = 0
    extra_total = 0
    
    all_verses = sorted(set(list(study_bible_refs.keys()) + list(xml_refs.keys())))
    
    for verse_num in all_verses:
        study_refs = study_bible_refs.get(verse_num, [])
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
    
    return {
        'study_bible_total': sum(len(refs) for refs in study_bible_refs.values()),
        'xml_total': sum(len(refs) for refs in xml_refs.values()),
        'mismatches': mismatches,
        'missing_total': missing_total,
        'extra_total': extra_total,
        'verses_with_refs': len(study_bible_refs)
    }

def generate_report(results, output_file):
    """Generate a comprehensive report."""
    lines = []
    lines.append("="*80)
    lines.append("ESV BIBLE - COMPLETE CROSS-REFERENCE ANALYSIS")
    lines.append("="*80)
    lines.append("")
    
    grand_total_study = 0
    grand_total_xml = 0
    grand_total_missing = 0
    grand_total_extra = 0
    chapters_with_issues = 0
    
    for book_chapter, result in sorted(results.items()):
        book, chapter = book_chapter
        
        grand_total_study += result['study_bible_total']
        grand_total_xml += result['xml_total']
        grand_total_missing += result['missing_total']
        grand_total_extra += result['extra_total']
        
        if result['mismatches']:
            chapters_with_issues += 1
            lines.append(f"\n{book.upper()} {chapter}")
            lines.append("-"*80)
            lines.append(f"Study Bible: {result['study_bible_total']} cross-refs")
            lines.append(f"XML:         {result['xml_total']} cross-refs")
            lines.append(f"Missing:     {result['missing_total']}")
            lines.append(f"Extra:       {result['extra_total']}")
            lines.append("")
            
            for mismatch in result['mismatches']:
                lines.append(f"  Verse {mismatch['verse']}:")
                lines.append(f"    Study Bible: {', '.join(mismatch['study_bible'])}")
                lines.append(f"    XML:         {', '.join(mismatch['xml'])}")
                if mismatch['missing']:
                    lines.append(f"    → MISSING: {', '.join(mismatch['missing'])}")
                if mismatch['extra']:
                    lines.append(f"    → EXTRA:   {', '.join(mismatch['extra'])}")
    
    # Grand summary
    lines.append("\n" + "="*80)
    lines.append("GRAND SUMMARY")
    lines.append("="*80)
    lines.append(f"Chapters analyzed: {len(results)}")
    lines.append(f"Chapters with issues: {chapters_with_issues}")
    lines.append(f"Chapters perfect: {len(results) - chapters_with_issues}")
    lines.append("")
    lines.append(f"Total cross-references in Study Bible: {grand_total_study}")
    lines.append(f"Total cross-references in XML: {grand_total_xml}")
    lines.append(f"Total missing: {grand_total_missing}")
    lines.append(f"Total extra: {grand_total_extra}")
    lines.append("")
    if grand_total_study > 0:
        accuracy = 100 * (grand_total_study - grand_total_missing) / grand_total_study
        lines.append(f"Overall accuracy: {accuracy:.1f}%")
    lines.append("="*80)
    
    report = '\n'.join(lines)
    
    # Save to file
    Path(output_file).write_text(report, encoding='utf-8')
    
    return report

def main():
    print("ESV Cross-Reference Comparison Tool")
    print("="*80)
    print()
    print("This script will compare ESV Study Bible cross-references with your XML files.")
    print()
    print("To use this tool:")
    print("1. Save all ESV Study Bible cross-references to 'esv_crossrefs_complete.txt'")
    print("2. Format: One line per cross-reference, like:")
    print("   1:1 a Gen. 1:1; [Col. 1:17; ...]")
    print("3. Run this script")
    print()
    
    crossref_file = Path('esv_crossrefs_complete.txt')
    
    if not crossref_file.exists():
        print(f"❌ Error: {crossref_file} not found!")
        print()
        print("Please create this file with the complete ESV cross-reference data.")
        print("Example content:")
        print("John")
        print("1:1 a Gen. 1:1; [Col. 1:17; 1 John 1:1; Rev. 1:4, 8, 17; 3:14; 21:6; 22:13]")
        print("1:1 b Rev. 19:13; [Heb. 4:12; 1 John 1:1]")
        print("...")
        return
    
    print(f"✓ Found {crossref_file}")
    print()
    print("Reading cross-reference data...")
    
    # Read the file
    text = crossref_file.read_text(encoding='utf-8')
    
    # For now, we'll need to parse by book/chapter
    # This would need the complete data structure
    
    print()
    print("Note: This is a template. Please provide the complete cross-reference data")
    print("for all books, and I'll process them.")
    print()
    print("For a quick test with John 7, the previous comparison script works perfectly!")

if __name__ == '__main__':
    main()
