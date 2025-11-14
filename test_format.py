#!/usr/bin/env python3
"""Test the updated formatting."""

import requests
from bs4 import BeautifulSoup
import re

url = "https://www.biblegateway.com/passage/?search=1 Corinthians+1&version=NKJV&interface=print"

headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
}

response = requests.get(url, headers=headers, timeout=10)
soup = BeautifulSoup(response.content, 'html.parser')

passage_div = soup.find('div', class_='passage-text')

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
                    'verse': int(verse_num),
                    'letter': letter_lower,
                    'references': ref_text
                })

# Remove footnotes/crossrefs divs
for div in soup.find_all('div', class_=['footnotes', 'crossrefs']):
    div.decompose()

# Convert crossrefs
for crossref in passage_div.find_all('sup', class_='crossreference'):
    letter_upper = crossref.get_text(strip=True)
    letter_clean = letter_upper.strip('()').lower()
    crossref.replace_with(f' {letter_clean} ')

# Remove footnotes
for footnote in passage_div.find_all('sup', class_='footnote'):
    footnote.decompose()

# Extract verses
verses = []
for para in passage_div.find_all(['p', 'div'], class_=re.compile('.*')):
    for verse_span in para.find_all('span', class_='text'):
        verse_num_elem = verse_span.find('span', class_='versenum')
        if verse_num_elem:
            verse_num = verse_num_elem.get_text(strip=True)
            verse_num_elem.decompose()
            verse_text = verse_span.get_text(separator=' ', strip=True)
            verse_text = re.sub(r'\s+', ' ', verse_text)
            verses.append(f"{verse_num} {verse_text}")

# Format output
output_lines = []
output_lines.extend(verses[:5])  # First 5 verses

if crossrefs_data:
    output_lines.append("\n" + "="*80)
    output_lines.append("CROSS REFERENCES")
    output_lines.append("="*80)
    
    by_verse = {}
    for cr in crossrefs_data:
        verse = cr['verse']
        if verse not in by_verse:
            by_verse[verse] = []
        by_verse[verse].append(f"  {cr['letter']}: {cr['references']}")
    
    for verse in sorted(by_verse.keys())[:3]:  # First 3 verses
        output_lines.append(f"\nVerse {verse}:")
        output_lines.extend(by_verse[verse])

print('\n'.join(output_lines))
