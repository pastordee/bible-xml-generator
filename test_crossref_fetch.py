#!/usr/bin/env python3
"""Test fetching one chapter with crossrefs."""

import requests
from bs4 import BeautifulSoup
import re

url = "https://www.biblegateway.com/passage/?search=Genesis+1&version=NKJV&interface=print"

headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
}

response = requests.get(url, headers=headers, timeout=10)
soup = BeautifulSoup(response.content, 'html.parser')

# Save HTML for inspection
with open('test_genesis_1.html', 'w', encoding='utf-8') as f:
    f.write(soup.prettify())

print("Saved HTML to test_genesis_1.html")

# Find passage
passage = soup.find('div', class_='passage-text')
if passage:
    # Look for crossref letters
    crossrefs = passage.find_all('sup', class_='crossreference')
    print(f"\nFound {len(crossrefs)} crossreference markers")
    
    if crossrefs:
        print("\nFirst 5 crossrefs:")
        for cr in crossrefs[:5]:
            print(f"  {cr.get_text()}")
    
    print("\n" + "="*60)
    print("Sample text (first 500 chars):")
    print("="*60)
    print(passage.get_text()[:500])
else:
    print("No passage text found!")
