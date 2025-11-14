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

# Extract crossreference data
crossrefs_data = []
crossrefs_section = soup.find('div', class_='crossrefs')
if crossrefs_section:
    for li in crossrefs_section.find_all('li'):
        li_id = li.get('id', '')
        match = re.search(r'cen-NKJV-(\d+)([A-Z]+)', li_id)
        if match:
            verse_num = match.group(1)
            letter_upper = match.group(2)
            letter_lower = letter_upper.lower()
            
            crossref_link = li.find('a', class_='crossref-link')
            if crossref_link:
                ref_text = crossref_link.get_text(strip=True)
                crossrefs_data.append({
                    'verse': verse_num,
                    'letter': letter_lower,
                    'references': ref_text
                })

print("="*80)
print("CROSSREFERENCE DATA EXTRACTED:")
print("="*80)
print(f"\nTotal crossrefs: {len(crossrefs_data)}")
print("\nFirst 10 crossrefs:")
for i, cr in enumerate(crossrefs_data[:10]):
    print(f"  {i+1}. Verse {cr['verse']}, Letter '{cr['letter']}': {cr['references']}")

print("\n" + "="*80)
print("SAMPLE CROSSREF FILE FORMAT:")
print("="*80)
for cr in crossrefs_data[:5]:
    print(f"V {cr['verse']}")
    print(f"L {cr['letter']}")
    print(f"R {cr['references']}")
    print()
