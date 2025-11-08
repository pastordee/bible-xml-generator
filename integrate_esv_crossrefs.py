#!/usr/bin/env python3
"""
Integrate cross-references from raw data files into ESV XML chapters.
This script reads the cross-reference data files and properly adds them to ESV XML files.
"""

import xml.etree.ElementTree as ET
from pathlib import Path
import re
from collections import defaultdict

def parse_crossref_file(crossref_file):
    """
    Parse a cross-reference data file and return structured data.
    
    Returns dict: {verse_num: [(letter, cid, references), ...]}
    """
    if not crossref_file.exists():
        return {}
    
    verse_refs = defaultdict(list)
    current_verse = None
    current_letter = None
    current_cid = None
    current_refs = []
    
    with open(crossref_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            
            # Verse marker: V 43003001
            if line.startswith('V '):
                # Save previous reference if exists
                if current_verse and current_letter and current_cid:
                    verse_refs[current_verse].append({
                        'letter': current_letter,
                        'cid': current_cid,
                        'references': ' '.join(current_refs)
                    })
                
                # Extract verse number (last 3 digits)
                verse_id = line.split()[1]  # e.g., 43003001
                current_verse = int(verse_id[-3:])  # Extract verse number
                current_refs = []
                
            # Cross-reference letter: c h
            elif line.startswith('c '):
                # Save previous reference if exists
                if current_letter and current_cid:
                    verse_refs[current_verse].append({
                        'letter': current_letter,
                        'cid': current_cid,
                        'references': ' '.join(current_refs)
                    })
                    current_refs = []
                
                current_letter = line.split()[1]  # e.g., 'h'
                
            # Cross-reference ID: i c43003001.1
            elif line.startswith('i '):
                current_cid = line.split()[1]  # e.g., 'c43003001.1'
                
            # Reference content: m [, r 43007050, etc.
            elif line.startswith('m ') or line.startswith('r '):
                current_refs.append(line)
    
    # Save last reference
    if current_verse and current_letter and current_cid:
        verse_refs[current_verse].append({
            'letter': current_letter,
            'cid': current_cid,
            'references': ' '.join(current_refs)
        })
    
    return dict(verse_refs)

def format_references(ref_data):
    """Format reference data into readable text."""
    lines = ref_data.split()
    result = []
    
    i = 0
    while i < len(lines):
        if lines[i] == 'm':
            # Marker text (like '[', ';', ']', 'See')
            if i + 1 < len(lines):
                result.append(lines[i + 1])
                i += 2
            else:
                i += 1
        elif lines[i] == 'r':
            # Reference to verse
            if i + 1 < len(lines):
                ref_code = lines[i + 1]
                # Parse reference code (e.g., 43007050 or 40022016)
                book_num = int(ref_code[:2])
                chapter = int(ref_code[2:5])
                verse = int(ref_code[5:])
                
                # Get book name from verse reference
                ref_text = lines[i + 2] if i + 2 < len(lines) and lines[i + 2] == 'm' else f"Ref: {chapter}:{verse}"
                result.append(ref_text)
                i += 2
            else:
                i += 1
        else:
            i += 1
    
    return ' '.join(result)

def integrate_crossrefs_into_xml(xml_file, crossref_data):
    """
    Integrate cross-references from data into XML file.
    """
    try:
        tree = ET.parse(xml_file)
        root = tree.getroot()
        
        # Find all verse elements
        book = root.find('book')
        if book is None:
            print(f"  ❌ No book element found in {xml_file.name}")
            return False
        
        chapter = book.find('chapter')
        if chapter is None:
            print(f"  ❌ No chapter element found in {xml_file.name}")
            return False
        
        verses = chapter.findall('v')
        modifications_made = False
        
        for verse in verses:
            verse_num = int(verse.get('n'))
            
            if verse_num not in crossref_data:
                continue
            
            # Remove existing crossref elements
            existing_crossrefs = verse.findall('crossref')
            for crossref in existing_crossrefs:
                verse.remove(crossref)
            
            # Add new crossrefs from data
            refs = crossref_data[verse_num]
            
            # Insert crossrefs at appropriate positions in the verse text
            # For now, we'll add them at the end of the verse
            for ref in refs:
                crossref_elem = ET.Element('crossref')
                crossref_elem.set('let', ref['letter'])
                crossref_elem.set('cid', ref['cid'])
                crossref_elem.text = format_references(ref['references'])
                verse.append(crossref_elem)
            
            modifications_made = True
        
        if modifications_made:
            # Write back to file
            tree.write(xml_file, encoding='utf-8', xml_declaration=True)
            return True
        
        return False
        
    except Exception as e:
        print(f"  ❌ Error processing {xml_file.name}: {e}")
        return False

def get_book_name_from_xml(xml_file):
    """Extract book name from XML filename (e.g., john_3.xml -> john)"""
    name = xml_file.stem  # Remove .xml
    parts = name.split('_')
    if parts[-1].isdigit():
        parts = parts[:-1]
    return '_'.join(parts)

def integrate_esv_crossrefs():
    """Main function to integrate cross-references into all ESV XML files."""
    
    xml_dir = Path(__file__).parent / "xml_esv"
    crossref_dir = Path(__file__).parent / "raw" / "cross_refs"
    
    if not xml_dir.exists():
        print(f"❌ ESV XML directory not found: {xml_dir}")
        return
    
    if not crossref_dir.exists():
        print(f"❌ Cross-reference directory not found: {crossref_dir}")
        return
    
    # Get all XML chapter files
    xml_files = sorted(xml_dir.glob("*_*.xml"))
    
    if not xml_files:
        print("❌ No XML chapter files found in xml_esv/")
        return
    
    print(f"Found {len(xml_files)} ESV XML chapter files")
    print(f"Cross-reference data directory: {crossref_dir}")
    
    # Ask for confirmation
    response = input(f"\n⚠️  Integrate cross-references into {len(xml_files)} ESV XML files? (yes/no): ")
    
    if response.lower() != 'yes':
        print("❌ Operation cancelled.")
        return
    
    print("\nIntegrating cross-references...\n")
    
    processed = 0
    updated = 0
    skipped = 0
    failed = 0
    
    for xml_file in xml_files:
        # Extract book name and chapter number
        book_name = get_book_name_from_xml(xml_file)
        chapter_num = xml_file.stem.split('_')[-1]
        
        # Find corresponding cross-reference file
        crossref_book_dir = crossref_dir / book_name
        if not crossref_book_dir.exists():
            print(f"  ⚠️  No cross-reference folder for {book_name}")
            skipped += 1
            continue
        
        crossref_file = crossref_book_dir / f"{chapter_num}.txt"
        if not crossref_file.exists():
            print(f"  ⚠️  No cross-reference file: {crossref_file.name}")
            skipped += 1
            continue
        
        # Parse cross-reference data
        crossref_data = parse_crossref_file(crossref_file)
        
        if not crossref_data:
            print(f"  ⚠️  No cross-reference data in {crossref_file.name}")
            skipped += 1
            continue
        
        # Integrate into XML
        if integrate_crossrefs_into_xml(xml_file, crossref_data):
            updated += 1
            print(f"  ✅ Updated {xml_file.name} ({len(crossref_data)} verses with refs)")
        else:
            failed += 1
        
        processed += 1
        
        if processed % 50 == 0:
            print(f"\n  Progress: {processed}/{len(xml_files)} files processed\n")
    
    print(f"\n{'='*60}")
    print(f"✅ Integration complete!")
    print(f"   Total files: {len(xml_files)}")
    print(f"   Updated: {updated}")
    print(f"   Skipped: {skipped}")
    if failed > 0:
        print(f"   Failed: {failed}")
    print(f"{'='*60}")

if __name__ == "__main__":
    integrate_esv_crossrefs()
