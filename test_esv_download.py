#!/usr/bin/env python3
"""
Test script to download a single ESV chapter with all markup including cross-references.
"""

import requests
import json

def fetch_esv_html_with_crossrefs():
    """Fetch ESV John 3 with HTML markup including cross-references."""
    
    api_key = "635f6f76a32703e82f372ce2f26a99db76896e07"
    url = "https://api.esv.org/v3/passage/html/"
    
    headers = {"Authorization": f"Token {api_key}"}
    
    params = {
        "q": "John 3",
        "include-passage-references": "true",
        "include-verse-numbers": "true",
        "include-footnotes": "true",
        "include-footnote-body": "true",
        "include-headings": "true",
        "include-short-copyright": "false",
        "include-copyright": "false",
        "include-passage-horizontal-lines": "false",
        "include-heading-horizontal-lines": "false",
        "include-selahs": "true",
        "line-length": "0"
    }
    
    print("Fetching ESV John 3 with cross-references...")
    print(f"URL: {url}")
    print(f"Parameters: {json.dumps(params, indent=2)}")
    print("\n" + "="*80 + "\n")
    
    response = requests.get(url, headers=headers, params=params)
    
    if response.status_code == 200:
        data = response.json()
        
        print("✅ Successfully fetched content!")
        print(f"\nResponse keys: {data.keys()}")
        print(f"\nNumber of passages: {len(data.get('passages', []))}")
        
        if data.get("passages"):
            html_content = data["passages"][0]
            
            # Save to file for inspection
            output_file = "john_3_esv_html.html"
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(html_content)
            
            print(f"\n✅ Saved HTML content to: {output_file}")
            
            # Show first 2000 characters
            print("\n" + "="*80)
            print("PREVIEW (first 2000 characters):")
            print("="*80)
            print(html_content[:2000])
            print("\n... (truncated)")
            
            # Check for cross-reference markers
            if 'crossref' in html_content.lower() or 'class="footnote"' in html_content:
                print("\n✅ HTML contains footnote/cross-reference markers!")
            else:
                print("\n⚠️  No obvious cross-reference markers found in HTML")
                
            return html_content
        else:
            print("❌ No passages in response")
            return None
    else:
        print(f"❌ Error: API returned status code {response.status_code}")
        print(f"Response: {response.text}")
        return None

def fetch_esv_text_format():
    """Also try the text format to see what's available."""
    
    api_key = "635f6f76a32703e82f372ce2f26a99db76896e07"
    url = "https://api.esv.org/v3/passage/text/"
    
    headers = {"Authorization": f"Token {api_key}"}
    
    params = {
        "q": "John 3:1-5",
        "include-passage-references": "true",
        "include-verse-numbers": "true",
        "include-footnotes": "true",
        "include-footnote-body": "true",
        "include-headings": "true",
        "include-selahs": "true"
    }
    
    print("\n\n" + "="*80)
    print("ALSO TRYING TEXT FORMAT (for comparison):")
    print("="*80 + "\n")
    
    response = requests.get(url, headers=headers, params=params)
    
    if response.status_code == 200:
        data = response.json()
        
        print("✅ Text format response:")
        print(f"Keys: {data.keys()}")
        
        if data.get("passages"):
            text_content = data["passages"][0]
            print("\nText content (first 5 verses):")
            print("-"*80)
            print(text_content)
            print("-"*80)
            
            # Save to file
            with open("john_3_1-5_text.txt", "w", encoding="utf-8") as f:
                f.write(text_content)
            
            print("\n✅ Saved to: john_3_1-5_text.txt")
            
        if data.get("footnotes"):
            print(f"\n✅ Footnotes found: {len(data['footnotes'])} footnotes")
            for i, footnote in enumerate(data["footnotes"][:3], 1):
                print(f"\nFootnote {i}:")
                print(footnote)
        else:
            print("\n⚠️  No footnotes in response")
    else:
        print(f"❌ Error: {response.status_code}")

if __name__ == "__main__":
    print("ESV API Test - Downloading John 3 with Cross-References\n")
    fetch_esv_html_with_crossrefs()
    fetch_esv_text_format()
    print("\n" + "="*80)
    print("✅ Test complete! Check the output files for details.")
    print("="*80)
