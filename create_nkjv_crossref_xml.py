#!/usr/bin/env python3
"""
Convert NKJV cross-reference data from scraped text format to XML format.
Matches the ESV cross-ref structure with 'r' lines for references.
"""

import re
from pathlib import Path

# Bible book information with USFM book codes
BIBLE_BOOKS = {
    # Old Testament
    'genesis': ('01', 50), 'exodus': ('02', 40), 'leviticus': ('03', 27),
    'numbers': ('04', 36), 'deuteronomy': ('05', 34), 'joshua': ('06', 24),
    'judges': ('07', 21), 'ruth': ('08', 4), '1_samuel': ('09', 31),
    '2_samuel': ('10', 24), '1_kings': ('11', 22), '2_kings': ('12', 25),
    '1_chronicles': ('13', 29), '2_chronicles': ('14', 36), 'ezra': ('15', 10),
    'nehemiah': ('16', 13), 'esther': ('17', 10), 'job': ('18', 42),
    'psalms': ('19', 150), 'proverbs': ('20', 31), 'ecclesiastes': ('21', 12),
    'song_of_solomon': ('22', 8), 'isaiah': ('23', 66), 'jeremiah': ('24', 52),
    'lamentations': ('25', 5), 'ezekiel': ('26', 48), 'daniel': ('27', 12),
    'hosea': ('28', 14), 'joel': ('29', 3), 'amos': ('30', 9),
    'obadiah': ('31', 1), 'jonah': ('32', 4), 'micah': ('33', 7),
    'nahum': ('34', 3), 'habakkuk': ('35', 3), 'zephaniah': ('36', 3),
    'haggai': ('37', 2), 'zechariah': ('38', 14), 'malachi': ('39', 4),
    # New Testament
    'matthew': ('40', 28), 'mark': ('41', 16), 'luke': ('42', 24),
    'john': ('43', 21), 'acts': ('44', 28), 'romans': ('45', 16),
    '1_corinthians': ('46', 16), '2_corinthians': ('47', 13),
    'galatians': ('48', 6), 'ephesians': ('49', 6), 'philippians': ('50', 4),
    'colossians': ('51', 4), '1_thessalonians': ('52', 5),
    '2_thessalonians': ('53', 3), '1_timothy': ('54', 6), '2_timothy': ('55', 4),
    'titus': ('56', 3), 'philemon': ('57', 1), 'hebrews': ('58', 13),
    'james': ('59', 5), '1_peter': ('60', 5), '2_peter': ('61', 3),
    '1_john': ('62', 5), '2_john': ('63', 1), '3_john': ('64', 1),
    'jude': ('65', 1), 'revelation': ('66', 22)
}

# Book name mappings for parsing references
BOOK_NAME_MAP = {
    'Gen.': '01', 'Ex.': '02', 'Lev.': '03', 'Num.': '04', 'Deut.': '05',
    'Josh.': '06', 'Judg.': '07', 'Ruth': '08', '1 Sam.': '09', '2 Sam.': '10',
    '1 Kin.': '11', '2 Kin.': '12', '1 Chr.': '13', '2 Chr.': '14', 'Ezra': '15',
    'Neh.': '16', 'Esth.': '17', 'Job': '18', 'Ps.': '19', 'Prov.': '20',
    'Eccl.': '21', 'Song': '22', 'Is.': '23', 'Jer.': '24', 'Lam.': '25',
    'Ezek.': '26', 'Dan.': '27', 'Hos.': '28', 'Joel': '29', 'Amos': '30',
    'Obad.': '31', 'Jon.': '32', 'Mic.': '33', 'Nah.': '34', 'Hab.': '35',
    'Zeph.': '36', 'Hag.': '37', 'Zech.': '38', 'Mal.': '39',
    'Matt.': '40', 'Mark': '41', 'Luke': '42', 'John': '43', 'Acts': '44',
    'Rom.': '45', '1 Cor.': '46', '2 Cor.': '47', 'Gal.': '48', 'Eph.': '49',
    'Phil.': '50', 'Col.': '51', '1 Thess.': '52', '2 Thess.': '53',
    '1 Tim.': '54', '2 Tim.': '55', 'Titus': '56', 'Philem.': '57',
    'Heb.': '58', 'James': '59', '1 Pet.': '60', '2 Pet.': '61',
    '1 John': '62', '2 John': '63', '3 John': '64', 'Jude': '65', 'Rev.': '66'
}

def parse_reference(ref_text):
    """
    Parse a reference like 'Gen. 1:27; 2:7; 5:1,2,5' into structured verse ranges.
    Returns list of (book_code, chapter, start_verse, end_verse, display_text) tuples.
    """
    refs = []
    
    # Handle brackets and special characters
    ref_text = ref_text.strip()
    has_brackets = ref_text.startswith('[') and ref_text.endswith(']')
    if has_brackets:
        ref_text = ref_text[1:-1]
    
    # Handle special cases like "cf. Isaiah 29:14"
    ref_text = ref_text.replace('cf. ', '')
    
    # Split by semicolons for different chapter references
    parts = [p.strip() for p in ref_text.split(';')]
    
    current_book = None
    current_chapter = None
    
    for part in parts:
        # Skip empty parts
        if not part:
            continue
            
        # Check if this part has a book name
        book_match = None
        for book_name, book_code in BOOK_NAME_MAP.items():
            if part.startswith(book_name):
                book_match = (book_name, book_code)
                break
        
        if book_match:
            current_book = book_match[1]
            book_name = book_match[0]
            # Remove book name from part
            part = part[len(book_name):].strip()
        
        if not current_book:
            continue
        
        # Skip if part is empty after removing book name
        if not part:
            continue
        
        try:
            # Parse chapter:verse or just chapter
            if ':' in part:
                # Has verse numbers - split only on first colon
                first_colon = part.index(':')
                chapter = part[:first_colon].strip()
                verse_part = part[first_colon+1:].strip()
                
                if chapter:
                    current_chapter = chapter.zfill(3)
            
                # First split by comma to handle cases like "8-10, 13"
                verse_groups = [v.strip() for v in verse_part.split(',')]
                
                for verse_group in verse_groups:
                    # Handle ranges like "1-5" or "2–4" (with em-dash) or "28—10:1" (chapter spanning)
                    if '-' in verse_group or '—' in verse_group or '–' in verse_group:
                        verse_group = verse_group.replace('—', '-').replace('–', '-')
                        verse_range = verse_group.split('-')
                        start_verse_str = verse_range[0].strip()
                        end_part = verse_range[1].strip() if len(verse_range) > 1 else start_verse_str
                        
                        # Check if end_part has a chapter number (e.g., "10:1")
                        if ':' in end_part:
                            end_chap_verse = end_part.split(':')
                            end_chapter = end_chap_verse[0].strip().zfill(3)
                            end_verse_str = end_chap_verse[1].strip()
                            end_verse = end_verse_str.zfill(3)
                            
                            # Build reference code for chapter-spanning range
                            start_verse = start_verse_str.zfill(3)
                            ref_code = f"{current_book}{current_chapter}{start_verse}-{current_book}{end_chapter}{end_verse}"
                            
                            # Build display text
                            display = f"{get_book_name(current_book)} {int(current_chapter)}:{int(start_verse_str)}-{int(end_chapter)}:{int(end_verse_str)}"
                            refs.append((ref_code, display))
                        else:
                            # Regular verse range within same chapter
                            end_verse_str = end_part
                            start_verse = start_verse_str.zfill(3)
                            end_verse = end_verse_str.zfill(3)
                            
                            # Build reference code
                            ref_code = f"{current_book}{current_chapter}{start_verse}"
                            if start_verse != end_verse:
                                ref_code += f"-{current_book}{current_chapter}{end_verse}"
                            
                            # Build display text
                            display = f"{get_book_name(current_book)} {int(current_chapter)}:{int(start_verse_str)}"
                            if start_verse != end_verse:
                                display += f"-{int(end_verse_str)}"
                            
                            refs.append((ref_code, display))
                    
                    # Single verse
                    else:
                        verse_num = verse_group.zfill(3)
                        ref_code = f"{current_book}{current_chapter}{verse_num}"
                        display = f"{get_book_name(current_book)} {int(current_chapter)}:{int(verse_group)}"
                        refs.append((ref_code, display))
            
            else:
                # Just chapter number (reference to whole chapter)
                chapter = part.strip()
                if chapter and current_book:
                    current_chapter = chapter.zfill(3)
                    ref_code = f"{current_book}{current_chapter}001"
                    display = f"{get_book_name(current_book)} {int(current_chapter)}"
                    refs.append((ref_code, display))
        
        except (ValueError, IndexError) as e:
            # If parsing fails, skip this reference
            continue
    
    return refs

def get_book_name(book_code):
    """Get display book name from code."""
    book_names = {
        '01': 'Gen.', '02': 'Ex.', '03': 'Lev.', '04': 'Num.', '05': 'Deut.',
        '06': 'Josh.', '07': 'Judg.', '08': 'Ruth', '09': '1 Sam.', '10': '2 Sam.',
        '11': '1 Kin.', '12': '2 Kin.', '13': '1 Chr.', '14': '2 Chr.', '15': 'Ezra',
        '16': 'Neh.', '17': 'Esth.', '18': 'Job', '19': 'Ps.', '20': 'Prov.',
        '21': 'Eccl.', '22': 'Song', '23': 'Is.', '24': 'Jer.', '25': 'Lam.',
        '26': 'Ezek.', '27': 'Dan.', '28': 'Hos.', '29': 'Joel', '30': 'Amos',
        '31': 'Obad.', '32': 'Jon.', '33': 'Mic.', '34': 'Nah.', '35': 'Hab.',
        '36': 'Zeph.', '37': 'Hag.', '38': 'Zech.', '39': 'Mal.',
        '40': 'Matt.', '41': 'Mark', '42': 'Luke', '43': 'John', '44': 'Acts',
        '45': 'Rom.', '46': '1 Cor.', '47': '2 Cor.', '48': 'Gal.', '49': 'Eph.',
        '50': 'Phil.', '51': 'Col.', '52': '1 Thess.', '53': '2 Thess.',
        '54': '1 Tim.', '55': '2 Tim.', '56': 'Titus', '57': 'Philem.',
        '58': 'Heb.', '59': 'James', '60': '1 Pet.', '61': '2 Pet.',
        '62': '1 John', '63': '2 John', '64': '3 John', '65': 'Jude', '66': 'Rev.'
    }
    return book_names.get(book_code, '')

def parse_crossref_file(file_path):
    """Parse NKJV crossref text file and extract structured data."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find the Cross references section
    if 'Cross references' not in content:
        return {}
    
    crossref_section = content.split('Cross references')[1]
    
    # Parse by verse
    crossrefs = {}
    current_verse = None
    
    for line in crossref_section.split('\n'):
        line = line.strip()
        if not line:
            continue
        
        # Check if it's a verse header like "Verse 1:"
        verse_match = re.match(r'Verse (\d+):', line)
        if verse_match:
            current_verse = int(verse_match.group(1))
            continue
        
        # Check if it's a reference line like "  a: Gen. 1:27; 2:7"
        ref_match = re.match(r'([a-z]+):\s*(.+)', line)
        if ref_match and current_verse:
            letter = ref_match.group(1)
            ref_text = ref_match.group(2).strip()
            
            if current_verse not in crossrefs:
                crossrefs[current_verse] = []
            
            crossrefs[current_verse].append({
                'letter': letter,
                'ref_text': ref_text
            })
    
    return crossrefs

def generate_xml_crossrefs(book_name, chapter_num, crossrefs_data):
    """Generate XML format crossref data matching ESV structure."""
    
    book_code = BIBLE_BOOKS[book_name][0]
    chapter_code = str(chapter_num).zfill(3)
    
    lines = []
    lines.append(f"C Chapter {chapter_num}")
    
    crossref_id = 1
    
    for verse_num in sorted(crossrefs_data.keys()):
        verse_code = str(verse_num).zfill(3)
        verse_id = f"{book_code}{chapter_code}{verse_code}"
        
        lines.append(f"V {verse_id}")
        
        for ref_data in crossrefs_data[verse_num]:
            letter = ref_data['letter']
            ref_text = ref_data['ref_text']
            
            # Parse the reference text into structured references
            parsed_refs = parse_reference(ref_text)
            
            # Write the crossref letter marker
            lines.append(f"c {letter}")
            lines.append(f"i c{verse_id}.{crossref_id}")
            
            # Write each reference as an 'r' line with 'm ;' separators
            if parsed_refs:
                for i, (ref_code, display_text) in enumerate(parsed_refs):
                    lines.append(f"r {ref_code} {display_text}")
                    # Add separator between references (but not after the last one)
                    if i < len(parsed_refs) - 1:
                        lines.append("m ;")
            else:
                # If parsing failed, write as plain text
                lines.append(f"m {ref_text}")
            
            crossref_id += 1
    
    return '\n'.join(lines)

def process_chapter(book_name, chapter_num, testament):
    """Process a single chapter's crossrefs."""
    # Input path
    input_dir = Path(f'raw/nkjv_crossrefs_{testament}')
    input_file = input_dir / f"{book_name}_{chapter_num}.txt"
    
    if not input_file.exists():
        print(f"  ✗ Input file not found: {input_file}")
        return False
    
    # Parse crossrefs
    crossrefs = parse_crossref_file(input_file)
    
    if not crossrefs:
        print(f"  ⚠ No crossrefs found in {book_name} {chapter_num}")
        return False
    
    # Generate XML
    xml_content = generate_xml_crossrefs(book_name, chapter_num, crossrefs)
    
    # Output path
    output_dir = Path(f'xml_nkjv/cross_refs/{book_name}')
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / f"{chapter_num}.txt"
    
    # Write output
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(xml_content)
    
    return True

def main():
    print("=" * 80)
    print("CREATING NKJV CROSSREF XML FILES")
    print("=" * 80)
    print()
    
    total_chapters = 0
    success_count = 0
    
    for book_name, (book_code, num_chapters) in BIBLE_BOOKS.items():
        testament = 'ot' if int(book_code) <= 39 else 'nt'
        
        print(f"Processing {book_name}...")
        
        for chapter_num in range(1, num_chapters + 1):
            if process_chapter(book_name, chapter_num, testament):
                success_count += 1
            total_chapters += 1
    
    print()
    print("=" * 80)
    print(f"✓ Successfully processed {success_count}/{total_chapters} chapters")
    print("=" * 80)

if __name__ == '__main__':
    main()
