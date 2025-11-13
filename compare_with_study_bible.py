#!/usr/bin/env python3
"""
Parse cross-references from ESV Study Bible reference list and compare with XML.
"""

import re
from collections import defaultdict
import xml.etree.ElementTree as ET

def parse_crossref_text(text):
    """Parse the cross-reference text format like '7:1 p ch. 5:18...'"""
    crossrefs = defaultdict(list)
    
    # Pattern: verse_ref letter(s) [references]
    # Example: "7:1 p ch. 5:18; 8:37, 40; 11:53"
    pattern = r'7:(\d+)\s+([a-z])\s+'
    
    matches = re.finditer(pattern, text)
    for match in matches:
        verse_num = int(match.group(1))
        letter = match.group(2)
        crossrefs[verse_num].append(letter)
    
    return crossrefs

def get_xml_crossrefs(xml_file):
    """Extract cross-references from XML file."""
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

def main():
    # The cross-reference text from ESV Study Bible
    crossref_text = """7:1 p ch. 5:18; 8:37, 40; 11:53
7:2 q ch. 5:1; 6:4 7:2 r See Lev. 23:34
7:3 s ver. 5, 10; See Matt. 12:46
7:4 t [ch. 14:22; 18:20]
7:5 u [Matt. 13:57; Mark 3:21] 7:5 v ver. 3, 10
7:6 w [ver. 8, 30]; See ch. 2:4
7:7 x ch. 15:18, 24 7:7 y ch. 3:19; [Col. 1:21; 1 John 3:12]
7:8 z See ch. 2:4
7:10 a ver. 3, 5
7:11 b ver. 1 7:11 c ch. 11:56
7:12 d ver. 32 7:12 e [ver. 40-43] 7:12 f ver. 47
7:13 g ch. 19:38; 20:19; [ch. 9:22; 12:42]
7:14 h ver. 28
7:15 i [ver. 46; Luke 2:47; 4:22; Acts 4:13]
7:16 j ch. 8:28; 12:49; 14:10, 24; [ch. 3:34] 7:16 k See ch. 3:17
7:17 l [ch. 8:31, 32; 14:21, 23] 7:17 m [ch. 8:43; Ps. 25:9; Dan. 12:10; Phil. 3:15] 7:17 n See ch. 5:30
7:18 o ch. 5:41; 8:50
7:19 p ver. 23; See ch. 1:17 7:19 q ver. 1
7:20 r ch. 8:48, 52; 10:20; [Matt. 11:18; Mark 3:22; Luke 7:33]
7:21 s ver. 23; ch. 5:2-9
7:22 t Lev. 12:3 7:22 u Gen. 17:10
7:23 v ch. 5:16; See Matt. 12:2
7:24 w ch. 8:15; [Isa. 11:3; 2 Cor. 10:7]; See Deut. 1:16, 17
7:25 x ver. 1
7:26 y ch. 18:20 7:26 z ver. 48
7:27 a [ch. 6:42; 8:14, 19; 9:29] 7:27 b ch. 19:9 7:27 c [ver. 42]
7:28 d ver. 14 7:28 a [See ver. 27 above] 7:28 e ch. 8:42; [ch. 5:43] 7:28 f See ch. 8:26 7:28 g ch. 8:19; 15:21; [ch. 4:22; 8:55]
7:29 h ch. 8:55; See Matt. 11:27 7:29 i ch. 6:46; 9:16, 33; [ch. 1:14] 7:29 j See ch. 3:17
7:30 k ver. 44; ch. 10:39; [Matt. 21:46] 7:30 l ch. 8:20 7:30 m ver. 6
7:31 n ch. 8:30; 10:42; 11:45; 12:11; [ch. 2:23; 12:42; Matt. 21:11] 7:31 o Matt. 12:23
7:32 p ver. 12 7:32 q ver. 45, 46
7:33 r ch. 12:35; 13:33; 14:19; 16:16-19 7:33 s ch. 16:5
7:34 t ch. 8:21; 13:33
7:35 u [ch. 8:22] 7:35 v James 1:1; 1 Pet. 1:1; [Isa. 11:12; Zeph. 3:10] 7:35 w ch. 12:20
7:36 x ver. 34
7:37 y Lev. 23:36; Num. 29:35; Neh. 8:18 7:37 z Isa. 55:1; See ch. 4:14 7:37 a See ch. 6:35
7:38 b [Isa. 12:3; Ezek. 47:1] 7:38 c ch. 4:14; [Prov. 18:4] 7:38 d See ch. 4:10
7:39 e Isa. 44:3; [1 Cor. 12:13; Gal. 3:14] 7:39 f Joel 2:28; Acts 2:16-18; [ch. 1:33; 20:22; Luke 24:49] 7:39 g Acts 2:4, 33 7:39 h ch. 3:34; Luke 11:13 7:39 i ch. 14:16, 17; 16:7
7:40 j See ver. 31 7:40 k ch. 1:21; 6:14; See Matt. 21:11
7:41 l ver. 26 7:41 m [ver. 52; ch. 1:46]
7:42 n [Ps. 89:3, 4]; See Matt. 1:1 7:42 o Mic. 5:2; Matt. 2:1, 5; Luke 2:4 7:42 p 1 Sam. 16:1
7:43 q ch. 9:16; 10:19; [ver. 12]
7:44 r ver. 30
7:45 s ver. 32
7:46 t See Matt. 7:29
7:47 u ver. 12
7:48 v 1 Cor. 1:20, 26; 2:8; [ch. 12:42]
7:50 w ch. 3:1; 19:39
7:51 x Deut. 17:6; 19:15; [Acts 23:3] 7:51 y Deut. 1:16; Prov. 18:13
7:52 z ver. 41 7:52 a [2 Kgs. 14:25 with Josh. 19:13]"""
    
    print("="*80)
    print("JOHN 7 CROSS-REFERENCE ANALYSIS")
    print("ESV Study Bible Official Cross-References")
    print("="*80)
    print()
    
    # Parse the cross-reference text
    study_bible_refs = parse_crossref_text(crossref_text)
    
    # Get XML cross-references
    xml_file = 'xml_esv/john_7.xml'
    xml_refs = get_xml_crossrefs(xml_file)
    
    print("VERSE-BY-VERSE COMPARISON:")
    print("-"*80)
    
    all_verses = sorted(set(list(study_bible_refs.keys()) + list(xml_refs.keys())))
    
    perfect_matches = 0
    mismatches = 0
    total_study_bible = sum(len(refs) for refs in study_bible_refs.values())
    total_xml = sum(len(refs) for refs in xml_refs.values())
    missing_in_xml = 0
    extra_in_xml = 0
    
    for verse_num in all_verses:
        study_refs = study_bible_refs.get(verse_num, [])
        xml_list = xml_refs.get(verse_num, [])
        
        study_str = ', '.join(study_refs) if study_refs else '(none)'
        xml_str = ', '.join(xml_list) if xml_list else '(none)'
        
        if study_refs == xml_list:
            status = "✓ MATCH"
            perfect_matches += 1
        else:
            status = "✗ MISMATCH"
            mismatches += 1
        
        print(f"\nVerse {verse_num:2d}: {status}")
        print(f"  Study Bible: {study_str}")
        print(f"  XML:         {xml_str}")
        
        # Calculate differences
        study_set = set(study_refs)
        xml_set = set(xml_list)
        
        missing = study_set - xml_set
        extra = xml_set - study_set
        
        if missing:
            print(f"  → MISSING in XML: {', '.join(sorted(missing))}")
            missing_in_xml += len(missing)
        
        if extra:
            print(f"  → EXTRA in XML:   {', '.join(sorted(extra))}")
            extra_in_xml += len(extra)
    
    # Summary
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    print(f"Total verses with cross-references in Study Bible: {len(study_bible_refs)}")
    print(f"Total verses with cross-references in XML: {len(xml_refs)}")
    print(f"Perfect matches: {perfect_matches}")
    print(f"Mismatches: {mismatches}")
    print()
    print(f"Total cross-references in Study Bible: {total_study_bible}")
    print(f"Total cross-references in XML: {total_xml}")
    print(f"Missing from XML: {missing_in_xml}")
    print(f"Extra in XML (should be removed): {extra_in_xml}")
    print()
    print(f"Accuracy: {perfect_matches}/{len(all_verses)} verses ({100*perfect_matches/len(all_verses):.1f}%)")
    print("="*80)

if __name__ == '__main__':
    main()
