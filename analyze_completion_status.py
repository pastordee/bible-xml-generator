#!/usr/bin/env python3
"""
Analyze completion status and generate priority reports.
"""

import re
from pathlib import Path
from collections import defaultdict

def parse_report():
    """Parse the comparison report to find completion stats."""
    report_file = Path('crossref_comparison_report.txt')
    
    if not report_file.exists():
        print("Error: crossref_comparison_report.txt not found!")
        return None
    
    text = report_file.read_text()
    
    chapters_data = []
    current_book = None
    current_chapter = None
    expected = 0
    present = 0
    missing = 0
    
    for line in text.split('\n'):
        # Chapter header: "1 CHRONICLES 1" or "MATTHEW 5"
        if re.match(r'^[A-Z\d\s]+\d+$', line.strip()) and not line.startswith('-'):
            # Save previous chapter if exists
            if current_book and current_chapter and expected > 0:
                completion = (present / expected) * 100
                chapters_data.append({
                    'book': current_book,
                    'chapter': current_chapter,
                    'expected': expected,
                    'present': present,
                    'missing': missing,
                    'completion': completion
                })
            
            # Parse new chapter
            parts = line.strip().rsplit(maxsplit=1)
            if len(parts) == 2:
                current_book = parts[0]
                current_chapter = int(parts[1])
                expected = 0
                present = 0
                missing = 0
        
        # Study Bible line
        elif line.startswith('Study Bible:'):
            match = re.search(r'Study Bible:\s+(\d+)', line)
            if match:
                expected = int(match.group(1))
        
        # XML line
        elif line.startswith('XML:'):
            match = re.search(r'XML:\s+(\d+)', line)
            if match:
                present = int(match.group(1))
        
        # Missing line
        elif line.startswith('Missing:'):
            match = re.search(r'Missing:\s+(\d+)', line)
            if match:
                missing = int(match.group(1))
    
    # Add last chapter
    if current_book and current_chapter and expected > 0:
        completion = (present / expected) * 100
        chapters_data.append({
            'book': current_book,
            'chapter': current_chapter,
            'expected': expected,
            'present': present,
            'missing': missing,
            'completion': completion
        })
    
    return chapters_data

def generate_reports(chapters_data):
    """Generate multiple reports."""
    
    print("="*80)
    print("CROSS-REFERENCE COMPLETION ANALYSIS")
    print("="*80)
    print()
    
    # Sort by completion percentage (descending)
    chapters_data.sort(key=lambda x: x['completion'], reverse=True)
    
    # 1. Chapters at 100% completion
    print("="*80)
    print("CHAPTERS AT 100% COMPLETION")
    print("="*80)
    complete = [c for c in chapters_data if c['completion'] == 100.0 and c['expected'] > 0]
    print(f"Total: {len(complete)} chapters")
    print()
    
    by_book = defaultdict(list)
    for c in complete:
        by_book[c['book']].append(c['chapter'])
    
    for book in sorted(by_book.keys()):
        chapters = sorted(by_book[book])
        print(f"{book}: {len(chapters)} chapters - {', '.join(map(str, chapters))}")
    
    print()
    
    # 2. Chapters 90-99% complete (almost there!)
    print("="*80)
    print("CHAPTERS 90-99% COMPLETE (PRIORITY)")
    print("="*80)
    almost = [c for c in chapters_data if 90 <= c['completion'] < 100 and c['missing'] > 0]
    print(f"Total: {len(almost)} chapters - {sum(c['missing'] for c in almost)} refs needed")
    print()
    
    for c in sorted(almost, key=lambda x: x['missing']):
        print(f"{c['book']} {c['chapter']}: {c['completion']:.1f}% ({c['present']}/{c['expected']}) - {c['missing']} missing")
    
    print()
    
    # 3. Top 30 chapters needing most work
    print("="*80)
    print("TOP 30 CHAPTERS NEEDING MOST WORK")
    print("="*80)
    worst = [c for c in chapters_data if c['missing'] > 0]
    worst.sort(key=lambda x: x['missing'], reverse=True)
    
    for i, c in enumerate(worst[:30], 1):
        print(f"{i:2}. {c['book']} {c['chapter']}: {c['completion']:.1f}% ({c['present']}/{c['expected']}) - {c['missing']} missing")
    
    print()
    
    # 4. Books completion summary
    print("="*80)
    print("COMPLETION BY BOOK")
    print("="*80)
    
    by_book_stats = defaultdict(lambda: {'expected': 0, 'present': 0, 'missing': 0, 'chapters': 0})
    
    for c in chapters_data:
        by_book_stats[c['book']]['expected'] += c['expected']
        by_book_stats[c['book']]['present'] += c['present']
        by_book_stats[c['book']]['missing'] += c['missing']
        by_book_stats[c['book']]['chapters'] += 1
    
    book_list = []
    for book, stats in by_book_stats.items():
        if stats['expected'] > 0:
            completion = (stats['present'] / stats['expected']) * 100
            book_list.append({
                'book': book,
                'completion': completion,
                'expected': stats['expected'],
                'present': stats['present'],
                'missing': stats['missing'],
                'chapters': stats['chapters']
            })
    
    book_list.sort(key=lambda x: x['completion'], reverse=True)
    
    for b in book_list:
        status = "✓" if b['completion'] == 100 else " "
        print(f"{status} {b['book']:20} {b['completion']:5.1f}% ({b['present']:4}/{b['expected']:4}) {b['missing']:3} missing across {b['chapters']:3} chapters")
    
    print()
    
    # 5. Overall stats
    print("="*80)
    print("OVERALL STATISTICS")
    print("="*80)
    total_expected = sum(c['expected'] for c in chapters_data)
    total_present = sum(c['present'] for c in chapters_data)
    total_missing = sum(c['missing'] for c in chapters_data)
    
    print(f"Total chapters analyzed: {len(chapters_data)}")
    print(f"Total cross-references expected: {total_expected}")
    print(f"Total cross-references present: {total_present}")
    print(f"Total cross-references missing: {total_missing}")
    print(f"Overall completion: {(total_present/total_expected)*100:.2f}%")
    print()
    print(f"Chapters at 100%: {len(complete)}")
    print(f"Chapters at 90-99%: {len(almost)}")
    print(f"Chapters below 90%: {len([c for c in chapters_data if c['completion'] < 90 and c['expected'] > 0])}")
    print("="*80)

def main():
    chapters_data = parse_report()
    
    if chapters_data:
        generate_reports(chapters_data)
        print()
        print("Tip: Focus on the 90-99% chapters first - they're closest to completion!")
    else:
        print("Could not parse report data.")

if __name__ == '__main__':
    main()
