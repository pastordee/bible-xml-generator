#!/usr/bin/env python3
"""
Rename BBE files to use standard naming convention:
- samuel_1_1.xml -> 1_samuel_1.xml
- samuel_2_1.xml -> 2_samuel_1.xml
- kings_1_1.xml -> 1_kings_1.xml
- kings_2_1.xml -> 2_kings_1.xml
- chronicles_1_1.xml -> 1_chronicles_1.xml
- chronicles_2_1.xml -> 2_chronicles_2.xml
- corinthians_1_1.xml -> 1_corinthians_1.xml
- corinthians_2_1.xml -> 2_corinthians_1.xml
- thessalonians_1_1.xml -> 1_thessalonians_1.xml
- thessalonians_2_1.xml -> 2_thessalonians_1.xml
- timothy_1_1.xml -> 1_timothy_1.xml
- timothy_2_1.xml -> 2_timothy_1.xml
- peter_1_1.xml -> 1_peter_1.xml
- peter_2_1.xml -> 2_peter_1.xml
- john_1_1.xml -> 1_john_1.xml
- john_2_1.xml -> 2_john_1.xml
- john_3_1.xml -> 3_john_1.xml
"""

import os
from pathlib import Path
import re

bbe_dir = Path("/Users/prayercircle/Documents/bible/bible-xml-generator/xml_bbe")

# Define the mappings
mappings = [
    ("samuel", "samuel"),
    ("kings", "kings"),
    ("chronicles", "chronicles"),
    ("corinthians", "corinthians"),
    ("thessalonians", "thessalonians"),
    ("timothy", "timothy"),
    ("peter", "peter"),
    ("john", "john"),
]

print("="*60)
print("RENAMING BBE FILES TO STANDARD CONVENTION")
print("="*60)

renamed_count = 0

for book_name in mappings:
    # Pattern: book_N_chapter.xml where N is 1, 2, or 3
    pattern = re.compile(rf"^{book_name[0]}_([123])_(\d+)\.xml$")
    
    for file in bbe_dir.glob(f"{book_name[0]}_*_*.xml"):
        match = pattern.match(file.name)
        if match:
            number = match.group(1)
            chapter = match.group(2)
            
            # New name: N_book_chapter.xml
            new_name = f"{number}_{book_name[1]}_{chapter}.xml"
            new_path = bbe_dir / new_name
            
            if not new_path.exists():
                print(f"  {file.name} -> {new_name}")
                file.rename(new_path)
                renamed_count += 1
            else:
                print(f"  ⚠️  {new_name} already exists, skipping {file.name}")

print("\n" + "="*60)
print(f"✅ Renamed {renamed_count} files")
print("="*60)
