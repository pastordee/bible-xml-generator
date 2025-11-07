#!/usr/bin/env python3
"""Re-download the book of Ruth for all versions with updated copyright format."""

import os
import time
from create_other_version_chapters import (
    fetch_bible_metadata, 
    fetch_api_bible_chapter_content, 
    create_detailed_chapter_xml, 
    save_xml_file
)

API_KEY = "pyExkJPN1XXpoJ39Xa8Xi"

# All versions to update
VERSIONS = ["KJV", "WEB", "ASV", "BSB", "MSG", "NKJV", "AMP", "NLT"]

# Ruth book info
RUTH_BOOK = {"id": 8, "num": 8, "title": "Ruth", "testament": "old", "abbr": "rut", "chapters": 4}

def main():
    print("="*60)
    print("RE-DOWNLOADING RUTH WITH COPYRIGHT INFO")
    print("="*60)
    
    total_chapters = 0
    
    for version in VERSIONS:
        print(f"\n📖 Processing {version}...")
        
        # Fetch metadata
        bible_metadata = fetch_bible_metadata(version, API_KEY)
        if not bible_metadata:
            print(f"  ⚠️  Could not fetch metadata for {version}, skipping...")
            continue
        
        print(f"  ✅ Metadata: {bible_metadata.get('name')}")
        
        # Create directory if needed
        version_dir = version.lower()
        os.makedirs(version_dir, exist_ok=True)
        
        # Download all 4 chapters of Ruth
        for chapter_num in range(1, RUTH_BOOK['chapters'] + 1):
            print(f"    📥 Ruth {chapter_num}...", end='', flush=True)
            
            # Download chapter
            content = fetch_api_bible_chapter_content(version, RUTH_BOOK['abbr'], chapter_num, API_KEY)
            
            if content:
                # Create XML with copyright info
                xml_tree = create_detailed_chapter_xml(version, RUTH_BOOK, chapter_num, content, bible_metadata)
                
                # Save file (will overwrite old version)
                safe_title = RUTH_BOOK['title'].lower()
                output_file = os.path.join(version_dir, f"{safe_title}_{chapter_num}.xml")
                save_xml_file(xml_tree, output_file)
                
                print(" ✅")
                total_chapters += 1
                time.sleep(2)  # 2 second delay
            else:
                print(" ❌ Failed")
    
    print("\n" + "="*60)
    print(f"✅ COMPLETE! Re-downloaded {total_chapters} Ruth chapters")
    print("="*60)

if __name__ == "__main__":
    main()
