#!/usr/bin/env python3
"""
Analyze the cross-reference comparison report to find patterns.
"""

import re
from pathlib import Path
from collections import defaultdict

def analyze_report(report_file):
    """Analyze the comparison report."""
    text = Path(report_file).read_text(encoding='utf-8')
    
    # Parse each chapter section
    pattern = r'([A-Z0-9 ]+)\n-+\nStudy Bible: (\d+)[^\n]+\nXML:\s+(\d+)[^\n]+\nMissing:\s+(\d+)\nExtra:\s+(\d+)'
    
    matches = re.findall(pattern, text)
    
    chapters_by_missing = []
    chapters_by_extra = []
    total_study = 0
    total_xml = 0
    total_missing = 0
    total_extra = 0
    
    for chapter, study, xml, missing, extra in matches:
        study = int(study)
        xml = int(xml)
        missing = int(missing)
        extra = int(extra)
        
        total_study += study
        total_xml += xml
        total_missing += missing 
        total_extra += extra
        
        if missing > 0:
            chapters_by_missing.append((chapter.strip(), missing, study))
        if extra > 0:
            chapters_by_extra.append((chapter.strip(), extra, xml))
    
    # Sort by most missing
    chapters_by_missing.sort(key=lambda x: x[1], reverse=True)
    chapters_by_extra.sort(key=lambda x: x[1], reverse=True)
    
    print("="*80)
    print("CROSS-REFERENCE COMPARISON ANALYSIS")
    print("="*80)
    print()
    print("OVERALL STATISTICS")
    print("-"*80)
    print(f"Total chapters analyzed:      {len(matches)}")
    print(f"Chapters with missing refs:   {len(chapters_by_missing)}")
    print(f"Chapters with extra refs:     {len(chapters_by_extra)}")
    print()
    print(f"Total cross-refs (Study Bible): {total_study:,}")
    print(f"Total cross-refs (XML):         {total_xml:,}")
    print(f"Total missing:                  {total_missing:,}")
    print(f"Total extra:                    {total_extra:,}")
    print()
    if total_study > 0:
        accuracy = 100 * (total_study - total_missing) / total_study
        print(f"Overall accuracy: {accuracy:.2f}%")
        print(f"Missing rate:     {100 - accuracy:.2f}%")
    print()
    
    print("="*80)
    print("TOP 20 CHAPTERS WITH MOST MISSING CROSS-REFERENCES")
    print("="*80)
    for i, (chapter, missing, study) in enumerate(chapters_by_missing[:20], 1):
        pct = 100 * missing / study if study > 0 else 0
        print(f"{i:2d}. {chapter:30s} Missing: {missing:3d}/{study:3d} ({pct:.1f}%)")
    print()
    
    if chapters_by_extra:
        print("="*80)
        print("TOP 20 CHAPTERS WITH MOST EXTRA CROSS-REFERENCES")
        print("="*80)
        for i, (chapter, extra, xml) in enumerate(chapters_by_extra[:20], 1):
            pct = 100 * extra / xml if xml > 0 else 0
            print(f"{i:2d}. {chapter:30s} Extra: {extra:3d}/{xml:3d} ({pct:.1f}%)")
        print()
    
    # Book-level summary
    book_stats = defaultdict(lambda: {'missing': 0, 'extra': 0, 'study': 0, 'xml': 0})
    
    for chapter, study, xml, missing, extra in matches:
        book = ' '.join(chapter.strip().split()[:-1])  # Remove chapter number
        book_stats[book]['study'] += int(study)
        book_stats[book]['xml'] += int(xml)
        book_stats[book]['missing'] += int(missing)
        book_stats[book]['extra'] += int(extra)
    
    books_by_missing = [(book, stats['missing'], stats['study']) 
                        for book, stats in book_stats.items() if stats['missing'] > 0]
    books_by_missing.sort(key=lambda x: x[1], reverse=True)
    
    print("="*80)
    print("TOP 20 BOOKS WITH MOST MISSING CROSS-REFERENCES")
    print("="*80)
    for i, (book, missing, study) in enumerate(books_by_missing[:20], 1):
        pct = 100 * missing / study if study > 0 else 0
        print(f"{i:2d}. {book:30s} Missing: {missing:4d}/{study:4d} ({pct:.1f}%)")
    print()

if __name__ == '__main__':
    analyze_report('crossref_comparison_report.txt')
