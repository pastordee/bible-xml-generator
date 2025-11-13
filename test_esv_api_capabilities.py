#!/usr/bin/env python3
"""
Test what the ESV API actually provides with different parameter combinations.
"""

import requests
import json

API_KEY = "635f6f76a32703e82f372ce2f26a99db76896e07"

def test_all_parameters_enabled():
    """Test with ALL parameters set to true to see maximum available content."""
    
    url = "https://api.esv.org/v3/passage/html/"
    headers = {"Authorization": f"Token {API_KEY}"}
    
    # Enable EVERYTHING the API supports
    params = {
        "q": "John 3:1-3",
        "include-passage-references": "true",
        "include-verse-numbers": "true",
        "include-first-verse-numbers": "true",
        "include-footnotes": "true",
        "include-footnote-body": "true",
        "include-footnote-links": "true",
        "include-headings": "true",
        "include-short-copyright": "true",
        "include-copyright": "true",
        "include-passage-horizontal-lines": "true",
        "include-heading-horizontal-lines": "true",
        "include-selahs": "true",
        "include-content-type": "true",
        "include-css": "true",
        "include-book-titles": "true",
        "include-chapter-numbers": "true",
        "include-verse-anchors": "true",
        "include-audio-link": "true",
        "line-length": "0"
    }
    
    print("="*80)
    print("TESTING ESV API WITH ALL PARAMETERS ENABLED")
    print("="*80)
    print(f"\nFetching: John 3:1-3")
    print(f"\nParameters enabled:")
    for key, value in params.items():
        if key != "q":
            print(f"  - {key}: {value}")
    
    response = requests.get(url, headers=headers, params=params)
    
    if response.status_code == 200:
        data = response.json()
        html = data.get("passages", [""])[0]
        
        print("\n" + "="*80)
        print("FULL RESPONSE:")
        print("="*80)
        print(html)
        
        # Check for specific features
        print("\n" + "="*80)
        print("FEATURE DETECTION:")
        print("="*80)
        
        features = {
            "Words of Christ (<span class=\"woc\">)": '<span class="woc">' in html,
            "Footnotes (<sup class=\"footnote\">)": '<sup class="footnote">' in html,
            "Cross-references (crossref)": 'crossref' in html.lower(),
            "Cross-references (cross-ref)": 'cross-ref' in html.lower(),
            "Verse numbers": 'verse-num' in html,
            "Headings": '<h3' in html,
            "Chapter numbers": 'chapter-num' in html,
            "Audio links": 'audio' in html.lower() or 'mp3' in html.lower(),
            "Paragraph tags": '<p' in html,
        }
        
        for feature, found in features.items():
            status = "✅ FOUND" if found else "❌ NOT FOUND"
            print(f"{status}: {feature}")
        
        return html
    else:
        print(f"\n❌ Error: {response.status_code}")
        print(response.text)
        return None

def test_text_endpoint_with_all_params():
    """Test the text endpoint to see if it has different features."""
    
    url = "https://api.esv.org/v3/passage/text/"
    headers = {"Authorization": f"Token {API_KEY}"}
    
    params = {
        "q": "John 3:1-3",
        "include-passage-references": "true",
        "include-verse-numbers": "true",
        "include-first-verse-numbers": "true",
        "include-footnotes": "true",
        "include-footnote-body": "true",
        "include-headings": "true",
        "include-short-copyright": "true",
        "include-selahs": "true",
    }
    
    print("\n\n" + "="*80)
    print("TESTING TEXT ENDPOINT (for comparison)")
    print("="*80)
    
    response = requests.get(url, headers=headers, params=params)
    
    if response.status_code == 200:
        data = response.json()
        
        print("\nResponse keys:", list(data.keys()))
        
        if "passages" in data:
            print("\n" + "="*80)
            print("TEXT CONTENT:")
            print("="*80)
            print(data["passages"][0])
        
        if "footnotes" in data and data["footnotes"]:
            print("\n" + "="*80)
            print("FOOTNOTES ARRAY:")
            print("="*80)
            for i, footnote in enumerate(data["footnotes"], 1):
                print(f"\nFootnote {i}:")
                print(json.dumps(footnote, indent=2))
        
        # Check for cross-references in the response
        if "cross_references" in data:
            print("\n✅ CROSS-REFERENCES FOUND!")
            print(json.dumps(data["cross_references"], indent=2))
        else:
            print("\n❌ No cross-references in response")
    else:
        print(f"❌ Error: {response.status_code}")

if __name__ == "__main__":
    test_all_parameters_enabled()
    test_text_endpoint_with_all_params()
    
    print("\n\n" + "="*80)
    print("CONCLUSION:")
    print("="*80)
    print("The parameters control which parts of the AVAILABLE data to include.")
    print("If cross-references aren't in the response with ALL parameters enabled,")
    print("then the ESV API simply doesn't provide them at all.")
    print("="*80)
