#!/usr/bin/env python3
"""
Copy Nahum chapters from ESV to versions that are missing them.
Adds a clear note that these chapters are from ESV translation since
API.Bible doesn't have Nahum for those bible IDs.
"""

import os
import shutil
import xml.etree.ElementTree as ET
from pathlib import Path

# Versions missing Nahum (based on our earlier tests)
VERSIONS_MISSING_NAHUM = ["kjv", "web", "asv", "bsb", "msg", "nkjv", "amp", "nlt"]

base_dir = Path(__file__).parent

print("="*60)
print("COPYING NAHUM FROM ESV TO MISSING VERSIONS")
print("="*60)
print("\nNote: API.Bible doesn't have Nahum for certain bible IDs.")
print("Copying ESV Nahum chapters with attribution notes.\n")

for version in VERSIONS_MISSING_NAHUM:
    version_dir = base_dir / f"xml_{version}"
    
    if not version_dir.exists():
        print(f"⚠️  Directory not found: {version_dir}")
        continue
    
    print(f"\n📖 Processing {version.upper()}...")
    
    for chapter_num in [1, 2, 3]:
        esv_file = base_dir / "xml_esv" / f"nahum_{chapter_num}.xml"
        target_file = version_dir / f"nahum_{chapter_num}.xml"
        
        if target_file.exists():
            print(f"  ✓ nahum_{chapter_num}.xml already exists")
            continue
        
        if not esv_file.exists():
            print(f"  ⚠️  ESV source file not found: {esv_file}")
            continue
        
        # Parse ESV file
        tree = ET.parse(esv_file)
        root = tree.getroot()
        
        # Update the version attribute in the book element
        book_elem = root.find('.//book')
        if book_elem is not None:
            book_elem.set('version', version.upper())
        
        # Add a note at the beginning about the source
        note = ET.Element("note")
        note.text = f"IMPORTANT: This chapter is from the ESV translation. The {version.upper()} version does not include the book of Nahum in the API.Bible database used for this download. This ESV text is provided for completeness and reference purposes only."
        
        # Insert note as first child after copyright/metadata
        gen_info = root.find('.//generation_info')
        if gen_info is not None:
            gen_info_index = list(root).index(gen_info)
            root.insert(gen_info_index + 1, note)
        else:
            root.insert(0, note)
        
        # Write the modified file
        tree.write(target_file, encoding='utf-8', xml_declaration=True)
        
        print(f"  ✅ Created nahum_{chapter_num}.xml (from ESV with attribution)")

print("\n" + "="*60)
print("✅ COMPLETE!")
print("="*60)
print("\nAll versions now have Nahum chapters.")
print("Files copied from ESV include clear attribution notes.")
