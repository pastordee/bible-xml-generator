#!/usr/bin/env python3
"""
Process ESV XML files to:
1. Extract footnotes from verse text and create <footnotes> section
2. Add <note> tags with fid attributes only where footnote markers exist in text
3. Remove empty <note> tags that don't have corresponding markers
"""

import re
import xml.etree.ElementTree as ET
from pathlib import Path
from collections import defaultdict

def extract_footnotes_from_text(text):
    """
    Extract footnotes from text like 'Footnotes (1) 1:6 Septuagint...'
    Returns list of (footnote_id, footnote_text) tuples
    """
    footnotes = []
    
    # Find the "Footnotes" section
    footnotes_match = re.search(r'Footnotes\s+(.*?)(?:\(ESV\)|$)', text, re.DOTALL)
    if not footnotes_match:
        return footnotes
    
    footnotes_text = footnotes_match.group(1).strip()
    
    # Pattern: (number) verse:verse_num then everything until next (number) verse: or end
    # This handles parentheses in footnote content like "(compare Ruth 4:21)"
    pattern = r'\((\d+)\)\s+(\d+:\d+\s+.*?)(?=\s*\(\d+\)\s+\d+:\d+|$)'
    
    for match in re.finditer(pattern, footnotes_text, re.DOTALL):
        footnote_id = match.group(1)
        footnote_content = match.group(2).strip()
        footnotes.append((footnote_id, footnote_content))
    
    return footnotes

def get_verse_number_from_footnote(footnote_text):
    """Extract verse number from '1:6 ...' -> 6"""
    match = re.match(r'\d+:(\d+)', footnote_text)
    return int(match.group(1)) if match else None

def find_footnote_markers_in_verse(verse_elem):
    """Find all footnote markers like (1), (2) in verse text"""
    markers = []
    
    # Get all text content from the verse
    text_parts = []
    if verse_elem.text:
        text_parts.append(verse_elem.text)
    
    for child in verse_elem:
        if child.tail:
            text_parts.append(child.tail)
    
    full_text = ''.join(text_parts)
    
    # Find all (number) patterns
    for match in re.finditer(r'\((\d+)\)', full_text):
        markers.append(match.group(1))
    
    return markers

def process_xml_file(xml_file):
    """Process one XML file to structure footnotes properly."""
    try:
        tree = ET.parse(xml_file)
        root = tree.getroot()
        
        # Check if footnotes section already exists
        existing_footnotes = root.find('.//footnotes')
        if existing_footnotes:
            # Already processed, just add fid attributes to existing notes
            return add_fid_to_existing_notes(xml_file, tree, root)
        
        # Find verse with embedded footnotes text
        footnotes_data = []
        footnotes_verse = None
        
        for verse in root.findall('.//v'):
            verse_text = ET.tostring(verse, encoding='unicode', method='text')
            if 'Footnotes' in verse_text:
                footnotes_data = extract_footnotes_from_text(verse_text)
                footnotes_verse = verse
                break
        
        if not footnotes_data:
            return False
        
        # Build mapping: verse_num -> list of footnote_ids
        verse_to_fids = defaultdict(list)
        for fid, content in footnotes_data:
            verse_num = get_verse_number_from_footnote(content)
            if verse_num:
                verse_to_fids[verse_num].append(fid)
        
        # Remove footnotes text from the verse
        if footnotes_verse is not None:
            # Get text content and find where "Footnotes" starts
            full_text = ET.tostring(footnotes_verse, encoding='unicode', method='text')
            footnotes_idx = full_text.find('Footnotes')
            
            if footnotes_idx >= 0:
                # Get the text before "Footnotes"
                text_before = full_text[:footnotes_idx].rstrip()
                
                # Reconstruct verse with all XML elements but trimmed text
                verse_xml = ET.tostring(footnotes_verse, encoding='unicode', method='xml')
                
                # Find "Footnotes" in XML and remove everything after it
                footnotes_xml_idx = verse_xml.find('Footnotes')
                if footnotes_xml_idx >= 0:
                    # Keep everything before "Footnotes"
                    clean_xml = verse_xml[:footnotes_xml_idx]
                    # Close the verse tag
                    clean_xml = clean_xml.rstrip() + '</v>'
                    
                    try:
                        new_verse = ET.fromstring(clean_xml)
                        parent = None
                        for p in root.iter():
                            if footnotes_verse in list(p):
                                parent = p
                                break
                        
                        if parent is not None:
                            idx = list(parent).index(footnotes_verse)
                            parent.remove(footnotes_verse)
                            parent.insert(idx, new_verse)
                    except Exception as e:
                        print(f"  Warning: Could not clean verse: {e}")
        
        # Remove all existing <note> tags
        for verse in root.findall('.//v'):
            for note in list(verse.findall('.//note')):
                verse.remove(note)
        
        # Add <note> tags with fid only where markers exist in text
        for verse in root.findall('.//v'):
            verse_num_attr = verse.get('n')
            if not verse_num_attr:
                continue
            
            try:
                verse_num = int(verse_num_attr)
            except:
                continue
            
            # Find footnote markers in this verse
            markers = find_footnote_markers_in_verse(verse)
            
            if markers and verse_num in verse_to_fids:
                fids = verse_to_fids[verse_num]
                
                # Add note tags for each marker
                for i, marker in enumerate(markers):
                    if i < len(fids):
                        note = ET.Element('note')
                        # Create nid from book/chapter/verse
                        chapter = root.find('.//chapter')
                        chapter_num = chapter.get('num') if chapter is not None else '1'
                        book = root.find('.//book')
                        book_num = book.get('num') if book is not None else '1'
                        
                        nid = f"n{book_num}{chapter_num.zfill(3)}{verse_num_attr.zfill(3)}.{i+1}"
                        note.set('nid', nid)
                        note.set('fid', fids[i])
                        verse.append(note)
        
        # Create footnotes section
        footnotes_section = ET.Element('footnotes')
        footnotes_heading = ET.SubElement(footnotes_section, 'footnotes-heading')
        footnotes_heading.text = 'Footnotes'
        
        for fid, content in footnotes_data:
            footnote = ET.SubElement(footnotes_section, 'footnote')
            footnote.set('id', fid)
            footnote.text = content
        
        # Insert footnotes section before the closing chapter/book tags
        chapter = root.find('.//chapter')
        if chapter is not None:
            # Insert before end-paragraph
            chapter.append(footnotes_section)
        
        tree.write(xml_file, encoding='utf-8', xml_declaration=True)
        print(f"  ✓ Processed {len(footnotes_data)} footnotes")
        return True
        
    except Exception as e:
        print(f"  ✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def add_fid_to_existing_notes(xml_file, tree, root):
    """For files with existing footnotes section, just add fid to notes."""
    # This is a simpler version for already-processed files
    return False

def main():
    xml_dir = Path('xml_esv')
    
    print("=" * 80)
    print("STRUCTURING FOOTNOTES - ESV")
    print("=" * 80)
    print()
    
    xml_files = sorted(xml_dir.glob('*.xml'))
    total_files = 0
    total_processed = 0
    total_footnotes = 0
    
    for xml_file in xml_files:
        # Skip non-chapter files
        if xml_file.stem in ['esv', 'esv_old']:
            continue
        
        total_files += 1
        print(f"Processing {xml_file.name}...", end=' ')
        
        result = process_xml_file(xml_file)
        if result:
            total_processed += 1
            # Count footnotes from the file
            try:
                tree = ET.parse(xml_file)
                root = tree.getroot()
                footnotes = root.findall('.//footnote')
                num_footnotes = len(footnotes)
                total_footnotes += num_footnotes
                print(f"✓ ({num_footnotes} footnotes)")
            except:
                print("✓")
        else:
            print("- (no footnotes)")
    
    print()
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Files processed: {total_files}")
    print(f"Files with footnotes: {total_processed}")
    print(f"Total footnotes structured: {total_footnotes}")
    print("=" * 80)

if __name__ == '__main__':
    main()
