#!/usr/bin/env python3
"""
Cross-Reference Coverage Analyzer
Compares existing XML files against comprehensive data files to identify missing cross-references.
"""

import os
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from collections import defaultdict


def parse_crossref_data_file(file_path):
    """Parse a cross-reference data file and return structured data."""
    crossrefs = defaultdict(list)
    
    if not file_path.exists():
        return crossrefs
    
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    current_verse = None
    current_ref = {}
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        if line.startswith('V '):
            if current_verse and current_ref:
                crossrefs[current_verse].append(current_ref)
            
            verse_id = line.split()[1]
            current_verse = verse_id
            current_ref = {}
        
        elif line.startswith('c '):
            if current_ref:
                crossrefs[current_verse].append(current_ref)
            current_ref = {'letter': line.split()[1]}
        
        elif line.startswith('i '):
            current_ref['cid'] = line.split()[1]
    
    if current_verse and current_ref:
        crossrefs[current_verse].append(current_ref)
    
    return crossrefs


def count_xml_crossrefs(xml_file):
    """Count cross-references in XML file by verse."""
    verse_crossrefs = defaultdict(int)
    
    try:
        tree = ET.parse(xml_file)
        root = tree.getroot()
    except ET.ParseError:
        return verse_crossrefs
    
    for crossref_elem in root.findall('.//crossref'):
        cid = crossref_elem.get('cid')
        if cid:
            match = re.match(r'c(\d{8})', cid)
            if match:
                verse_id = match.group(1)
                verse_crossrefs[verse_id] += 1
    
    return verse_crossrefs


def analyze_chapter(xml_file, crossref_data_file):
    """Analyze a single chapter file."""
    
    # Get expected cross-references from data file
    expected_crossrefs = parse_crossref_data_file(crossref_data_file)
    
    # Get actual cross-references from XML
    actual_crossrefs = count_xml_crossrefs(xml_file)
    
    # Compare
    total_expected = sum(len(refs) for refs in expected_crossrefs.values())
    total_actual = sum(actual_crossrefs.values())
    
    missing_by_verse = {}
    extra_by_verse = {}
    
    # Check for missing cross-references
    for verse_id, expected_refs in expected_crossrefs.items():
        expected_count = len(expected_refs)
        actual_count = actual_crossrefs.get(verse_id, 0)
        
        if actual_count < expected_count:
            missing_by_verse[verse_id] = expected_count - actual_count
        elif actual_count > expected_count:
            extra_by_verse[verse_id] = actual_count - expected_count
    
    # Check for verses with cross-references that shouldn't have them
    for verse_id, actual_count in actual_crossrefs.items():
        if verse_id not in expected_crossrefs and actual_count > 0:
            extra_by_verse[verse_id] = actual_count
    
    return {
        'total_expected': total_expected,
        'total_actual': total_actual,
        'total_missing': total_expected - total_actual,
        'missing_by_verse': missing_by_verse,
        'extra_by_verse': extra_by_verse
    }


def analyze_all_chapters(xml_dir, crossref_base_dir):
    """Analyze all chapter files."""
    
    xml_files = sorted(Path(xml_dir).glob("*.xml"))
    
    print("="*80)
    print("CROSS-REFERENCE COVERAGE ANALYSIS")
    print("="*80)
    print(f"\nAnalyzing {len(xml_files)} XML files...\n")
    
    total_stats = {
        'files_analyzed': 0,
        'total_expected': 0,
        'total_actual': 0,
        'total_missing': 0,
        'files_with_missing': 0,
        'files_perfect': 0,
        'worst_chapters': []
    }
    
    for xml_file in xml_files:
        filename = xml_file.stem
        parts = filename.rsplit('_', 1)
        
        if len(parts) != 2:
            continue
        
        book_name, chapter = parts
        
        # Find corresponding data file
        crossref_file = Path(crossref_base_dir) / book_name / f"{chapter}.txt"
        
        if not crossref_file.exists():
            continue
        
        # Analyze this chapter
        stats = analyze_chapter(xml_file, crossref_file)
        
        total_stats['files_analyzed'] += 1
        total_stats['total_expected'] += stats['total_expected']
        total_stats['total_actual'] += stats['total_actual']
        total_stats['total_missing'] += stats['total_missing']
        
        if stats['total_missing'] > 0:
            total_stats['files_with_missing'] += 1
            
            # Track worst chapters
            missing_pct = (stats['total_missing'] / stats['total_expected'] * 100) if stats['total_expected'] > 0 else 0
            total_stats['worst_chapters'].append({
                'file': filename,
                'missing': stats['total_missing'],
                'expected': stats['total_expected'],
                'actual': stats['total_actual'],
                'percentage': missing_pct
            })
        else:
            total_stats['files_perfect'] += 1
    
    # Sort worst chapters by percentage missing
    total_stats['worst_chapters'].sort(key=lambda x: x['percentage'], reverse=True)
    
    return total_stats


def main():
    """Main execution."""
    base_dir = Path(__file__).parent
    xml_dir = base_dir / "xml_esv"
    crossref_base_dir = base_dir / "raw" / "cross_refs"
    
    if not xml_dir.exists():
        print(f"❌ XML directory not found: {xml_dir}")
        return
    
    if not crossref_base_dir.exists():
        print(f"❌ Cross-reference data directory not found: {crossref_base_dir}")
        return
    
    # Analyze all chapters
    stats = analyze_all_chapters(xml_dir, crossref_base_dir)
    
    # Print summary
    print("\n" + "="*80)
    print("SUMMARY STATISTICS")
    print("="*80)
    print(f"\nFiles analyzed: {stats['files_analyzed']}")
    print(f"Files with perfect coverage: {stats['files_perfect']} ({stats['files_perfect']/stats['files_analyzed']*100:.1f}%)")
    print(f"Files with missing crossrefs: {stats['files_with_missing']} ({stats['files_with_missing']/stats['files_analyzed']*100:.1f}%)")
    
    print(f"\nCross-reference totals:")
    print(f"  Expected (from data files): {stats['total_expected']:,}")
    print(f"  Actually in XML files: {stats['total_actual']:,}")
    print(f"  Missing: {stats['total_missing']:,}")
    
    if stats['total_expected'] > 0:
        coverage_pct = (stats['total_actual'] / stats['total_expected'] * 100)
        print(f"\nOverall coverage: {coverage_pct:.2f}%")
        print(f"Missing coverage: {100-coverage_pct:.2f}%")
    
    # Show worst chapters
    if stats['worst_chapters']:
        print(f"\n{'='*80}")
        print("TOP 20 CHAPTERS WITH MOST MISSING CROSS-REFERENCES")
        print("="*80)
        print(f"\n{'Chapter':<25} {'Expected':>10} {'Actual':>10} {'Missing':>10} {'% Missing':>12}")
        print("-"*80)
        
        for chapter in stats['worst_chapters'][:20]:
            print(f"{chapter['file']:<25} {chapter['expected']:>10} {chapter['actual']:>10} {chapter['missing']:>10} {chapter['percentage']:>11.1f}%")
    
    print("\n" + "="*80)
    print("ANALYSIS COMPLETE")
    print("="*80)


if __name__ == "__main__":
    main()
