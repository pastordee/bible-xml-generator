#!/usr/bin/env python3
"""Debug verse extraction."""

import requests
from bs4 import BeautifulSoup

url = "https://www.biblegateway.com/passage/?search=1 Corinthians+1&version=NKJV&interface=print"

headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
}

response = requests.get(url, headers=headers, timeout=10)
soup = BeautifulSoup(response.content, 'html.parser')

passage = soup.find('div', class_='passage-text')

# Look for verse numbers
print("Looking for verse spans...")
verse_spans = passage.find_all('span', class_='versenum')
print(f"Found {len(verse_spans)} verse number spans")
for vs in verse_spans[:5]:
    print(f"  Verse: {vs.get_text()}, Parent: {vs.parent.name}, Parent class: {vs.parent.get('class')}")

print("\n" + "="*80)
print("Checking paragraph structure...")
for i, p in enumerate(passage.find_all('p')[:3]):
    print(f"\nParagraph {i+1}:")
    print(f"  Classes: {p.get('class')}")
    print(f"  Text (first 100 chars): {p.get_text()[:100]}")
