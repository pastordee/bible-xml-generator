#!/usr/bin/env python3
"""Test the updated fetch function."""

import requests
from bs4 import BeautifulSoup
import re

url = "https://www.biblegateway.com/passage/?search=Genesis+1&version=NKJV&interface=print"

headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
}

response = requests.get(url, headers=headers, timeout=10)
soup = BeautifulSoup(response.content, 'html.parser')

passage_div = soup.find('div', class_='passage-text')

if passage_div:
    # Convert crossref markers from (A) to lowercase a
    for crossref in passage_div.find_all('sup', class_='crossreference'):
        letter_upper = crossref.get_text(strip=True)
        letter_clean = letter_upper.strip('()').lower()
        crossref.replace_with(f' {letter_clean} ')
    
    # Remove footnotes
    for footnote in passage_div.find_all('sup', class_='footnote'):
        footnote.decompose()
    
    # Get text
    chapter_text = passage_div.get_text(separator=' ', strip=True)
    chapter_text = re.sub(r'\s+', ' ', chapter_text)
    
    # Show first 800 characters
    print("="*80)
    print("GENESIS 1 WITH CROSSREF LETTERS:")
    print("="*80)
    print(chapter_text[:800])
    print("...")
    
    # Count crossref letters
    letters = re.findall(r'\b([a-z])\b', chapter_text)
    print(f"\nFound {len(letters)} single-letter matches (includes crossrefs)")
    print(f"First 20: {letters[:20]}")
