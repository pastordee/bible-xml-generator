#!/usr/bin/env python3
"""
Test API.Bible versions to see if they provide cross-references.
"""

import requests
import json

# API.Bible key (Premium key with access to NKJV, AMP, NLT)
API_KEY = "pyExkJPN1XXpoJ39Xa8Xi"

# Version IDs from API.Bible (corrected from create_other_version_chapters.py)
VERSIONS = {
    "NKJV": "63097d2a0a2f7db3-01",  # New King James Version
    "KJV": "de4e12af7f28f599-02",   # King James Version (Authorized)
    "WEB": "9879dbb7cfe39e4d-01",   # World English Bible
    "ASV": "06125adad2d5898a-01",   # American Standard Version
}

def test_apibible_version(version_name, bible_id):
    """Test if an API.Bible version provides cross-references."""
    
    print("\n" + "="*80)
    print(f"TESTING: {version_name} (ID: {bible_id})")
    print("="*80)
    
    # Get book info for John
    books_url = f"https://api.scripture.api.bible/v1/bibles/{bible_id}/books"
    headers = {"api-key": API_KEY}
    
    response = requests.get(books_url, headers=headers)
    
    if response.status_code != 200:
        print(f"❌ Error getting books: {response.status_code}")
        return
    
    books_data = response.json()
    john_book = None
    
    for book in books_data.get("data", []):
        if book["id"].upper() == "JHN" or book["name"] == "John":
            john_book = book
            break
    
    if not john_book:
        print("❌ Book of John not found")
        return
    
    book_id = john_book["id"]
    print(f"✅ Found John with ID: {book_id}")
    
    # Get chapter 3 with all possible parameters
    chapter_url = f"https://api.scripture.api.bible/v1/bibles/{bible_id}/chapters/{book_id}.3"
    
    params = {
        "content-type": "json",
        "include-notes": "true",
        "include-titles": "true",
        "include-chapter-numbers": "true",
        "include-verse-numbers": "true",
        "include-verse-spans": "true",
    }
    
    print(f"\nFetching John 3 with parameters: {params}")
    
    response = requests.get(chapter_url, headers=headers, params=params)
    
    if response.status_code != 200:
        print(f"❌ Error: {response.status_code}")
        print(response.text)
        return
    
    data = response.json()
    
    # Save raw response
    filename = f"apibible_{version_name.lower()}_john3_raw.json"
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    print(f"✅ Saved raw JSON to: {filename}")
    
    # Analyze the response structure
    print(f"\n📊 Response structure:")
    print(f"   Top-level keys: {list(data.keys())}")
    
    if "data" in data:
        print(f"   Data keys: {list(data['data'].keys())}")
        
        content = data['data'].get('content', '')
        
        # Check for various cross-reference patterns
        patterns = {
            'crossref': 'crossref' in content.lower(),
            'cross-ref': 'cross-ref' in content.lower(),
            'xref': 'xref' in content.lower(),
            'reference': 'class="reference"' in content or 'class=\\"reference\\"' in content,
            'note': '<note' in content or 'class="note"' in content,
            'footnote': 'footnote' in content.lower(),
        }
        
        print(f"\n🔍 Feature detection in content:")
        for feature, found in patterns.items():
            status = "✅ FOUND" if found else "❌ NOT FOUND"
            print(f"   {status}: {feature}")
        
        # Show first 1000 characters of content
        print(f"\n📄 Content preview (first 1000 chars):")
        print("-" * 80)
        print(content[:1000])
        print("-" * 80)
        
        # Check if there are any verse objects with cross-references
        if "verse" in str(data).lower() and "reference" in str(data).lower():
            print("\n⚠️  Found 'verse' and 'reference' keywords in response - checking structure...")
    
    # Also try getting individual verses to see if they have cross-ref data
    print(f"\n🔬 Testing individual verse endpoint (John 3:1)...")
    verse_url = f"https://api.scripture.api.bible/v1/bibles/{bible_id}/verses/{book_id}.3.1"
    verse_params = {
        "content-type": "json",
        "include-notes": "true",
    }
    
    verse_response = requests.get(verse_url, headers=headers, params=verse_params)
    
    if verse_response.status_code == 200:
        verse_data = verse_response.json()
        
        # Save verse response
        verse_filename = f"apibible_{version_name.lower()}_john3v1_raw.json"
        with open(verse_filename, "w", encoding="utf-8") as f:
            json.dump(verse_data, f, indent=2)
        print(f"   ✅ Saved verse JSON to: {verse_filename}")
        
        # Check verse structure
        if "data" in verse_data:
            print(f"   Verse data keys: {list(verse_data['data'].keys())}")
            
            if "next" in verse_data['data']:
                print(f"   Has 'next' field: {verse_data['data']['next']}")
            if "previous" in verse_data['data']:
                print(f"   Has 'previous' field: {verse_data['data']['previous']}")
    else:
        print(f"   ❌ Verse endpoint error: {verse_response.status_code}")

if __name__ == "__main__":
    print("Testing API.Bible versions for cross-reference support")
    print("Checking: John Chapter 3")
    
    # Test NKJV first (user requested)
    test_apibible_version("NKJV", VERSIONS["NKJV"])
    
    # Test other versions for comparison
    for version_name, bible_id in VERSIONS.items():
        if version_name != "NKJV":  # Already tested
            test_apibible_version(version_name, bible_id)
    
    print("\n\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    print("Check the saved JSON files to see the full structure.")
    print("If cross-references exist, they would likely be in:")
    print("  - data.content (as HTML/XML markup)")
    print("  - data.notes (as separate note objects)")
    print("  - data.crossReferences (as a dedicated field)")
    print("="*80)
