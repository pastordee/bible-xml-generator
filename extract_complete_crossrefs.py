#!/usr/bin/env python3
"""
Extract complete cross-reference information from ESV Global Study Bible PDF.
This script extracts cross-reference letters and their verse locations.
"""

import pdfplumber
import re
from collections import defaultdict
from pathlib import Path

def extract_john_7_crossrefs(pdf_path):
    """Extract all cross-references from John 7 in the PDF."""
    print("Extracting John 7 from ESV Global Study Bible PDF...")
    
    crossref_data = defaultdict(list)
    
    with pdfplumber.open(pdf_path) as pdf:
        # John 7 is on pages 3935-3937 (0-indexed: 3934-3936)
        john_7_pages = [3934, 3935, 3936]
        
        full_text = ""
        for page_num in john_7_pages:
            if page_num < len(pdf.pages):
                page = pdf.pages[page_num]
                text = page.extract_text()
                if text:
                    full_text += text + "\n"
        
        # Save raw extraction
        with open('john_7_raw_pdf.txt', 'w', encoding='utf-8') as f:
            f.write(full_text)
        print("✓ Saved raw PDF text to john_7_raw_pdf.txt")
        
        # Parse verses and their cross-reference letters
        # Pattern: verse number followed by content with superscript letters
        verse_pattern = r'(\d+)(?:\[\†\])?\s+(.*?)(?=(?:\d+(?:\[\†\])?\s+|$))'
        
        # Find all verses
        matches = re.finditer(verse_pattern, full_text, re.DOTALL)
        
        for match in matches:
            verse_num = int(match.group(1))
            verse_text = match.group(2)
            
            # Skip if not in John 7 range (1-52)
            if verse_num < 1 or verse_num > 52:
                continue
            
            # Extract all single lowercase letters (cross-reference markers)
            # These appear as standalone letters between words
            letters = re.findall(r'\b([a-z])\b', verse_text)
            
            if letters:
                crossref_data[verse_num] = letters
        
        return crossref_data

def compare_with_xml(crossref_data, xml_file):
    """Compare PDF cross-references with current XML."""
    import xml.etree.ElementTree as ET
    
    print(f"\nComparing with {xml_file}...")
    
    # Parse XML
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
    
    # Create comparison report
    report = []
    report.append("="*80)
    report.append("JOHN 7 CROSS-REFERENCE COMPARISON REPORT")
    report.append("="*80)
    report.append("")
    
    all_verses = sorted(set(list(crossref_data.keys()) + list(xml_crossrefs.keys())))
    
    missing_total = 0
    extra_total = 0
    perfect_match = 0
    
    for verse_num in all_verses:
        pdf_refs = crossref_data.get(verse_num, [])
        xml_refs = xml_crossrefs.get(verse_num, [])
        
        if pdf_refs == xml_refs:
            perfect_match += 1
            status = "✓ PERFECT"
        else:
            status = "⚠ MISMATCH"
        
        report.append(f"Verse {verse_num:2d}: {status}")
        report.append(f"  PDF has: {', '.join(pdf_refs) if pdf_refs else '(none)'}")
        report.append(f"  XML has: {', '.join(xml_refs) if xml_refs else '(none)'}")
        
        # Calculate differences
        pdf_set = set(pdf_refs)
        xml_set = set(xml_refs)
        
        missing = pdf_set - xml_set
        extra = xml_set - pdf_set
        
        if missing:
            report.append(f"  MISSING in XML: {', '.join(sorted(missing))}")
            missing_total += len(missing)
        
        if extra:
            report.append(f"  EXTRA in XML: {', '.join(sorted(extra))}")
            extra_total += len(extra)
        
        report.append("")
    
    # Summary
    report.append("="*80)
    report.append("SUMMARY")
    report.append("="*80)
    report.append(f"Total verses checked: {len(all_verses)}")
    report.append(f"Perfect matches: {perfect_match}")
    report.append(f"Mismatches: {len(all_verses) - perfect_match}")
    report.append(f"Total cross-references in PDF: {sum(len(refs) for refs in crossref_data.values())}")
    report.append(f"Total cross-references in XML: {sum(len(refs) for refs in xml_crossrefs.values())}")
    report.append(f"Missing from XML: {missing_total}")
    report.append(f"Extra in XML: {extra_total}")
    report.append("="*80)
    
    return "\n".join(report)

def generate_alphabetical_check(crossref_data):
    """Check if PDF cross-references follow alphabetical order."""
    report = []
    report.append("\n" + "="*80)
    report.append("ALPHABETICAL ORDER CHECK (PDF Data)")
    report.append("="*80)
    report.append("")
    
    prev_letter = None
    issue_count = 0
    
    for verse_num in sorted(crossref_data.keys()):
        letters = crossref_data[verse_num]
        letters_str = ', '.join(letters)
        
        issue = ""
        if prev_letter and letters:
            expected_next = chr(ord(prev_letter) + 1) if prev_letter != 'z' else 'a'
            if letters[0] != expected_next:
                issue = f" ⚠️ (expected '{expected_next}')"
                issue_count += 1
        
        report.append(f"Verse {verse_num:2d}: {letters_str}{issue}")
        
        if letters:
            prev_letter = letters[-1]
    
    report.append("")
    report.append(f"Total alphabetical issues: {issue_count}")
    report.append("="*80)
    
    return "\n".join(report)

def main():
    pdf_path = Path('raw/ESV Global Study Bible - Crossway Bibles-3.pdf')
    xml_file = Path('xml_esv/john_7.xml')
    
    if not pdf_path.exists():
        print(f"Error: PDF not found at {pdf_path}")
        return
    
    if not xml_file.exists():
        print(f"Error: XML not found at {xml_file}")
        return
    
    # Extract cross-references from PDF
    crossref_data = extract_john_7_crossrefs(pdf_path)
    
    print(f"\n✓ Extracted cross-references from PDF")
    print(f"  Found {len(crossref_data)} verses with cross-references")
    print(f"  Total cross-references: {sum(len(refs) for refs in crossref_data.values())}")
    
    # Compare with XML
    comparison_report = compare_with_xml(crossref_data, xml_file)
    
    # Check alphabetical order in PDF
    alphabet_report = generate_alphabetical_check(crossref_data)
    
    # Combine reports
    full_report = comparison_report + "\n" + alphabet_report
    
    # Save report
    report_file = Path('john_7_crossref_analysis.txt')
    report_file.write_text(full_report, encoding='utf-8')
    
    print(f"\n✓ Full analysis saved to {report_file}")
    print("\n" + "="*80)
    print("REPORT PREVIEW:")
    print("="*80)
    print(full_report)

if __name__ == '__main__':
    main()
