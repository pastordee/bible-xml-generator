#!/usr/bin/env python3
"""Check if crossreference data is in the HTML."""

import requests
from bs4 import BeautifulSoup

url = "https://www.biblegateway.com/passage/?search=Genesis+1&version=NKJV&interface=print"

headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
}

response = requests.get(url, headers=headers, timeout=10)
soup = BeautifulSoup(response.content, 'html.parser')

# Look for crossreference data
print("="*80)
print("LOOKING FOR CROSSREFERENCE DATA")
print("="*80)

# Check for crossref notes section
crossref_section = soup.find('div', class_='crossrefs')
if crossref_section:
    print("\nFound crossrefs section!")
    print(crossref_section.prettify()[:500])
else:
    print("\nNo dedicated crossrefs section found.")

# Check footnotes section (crossrefs might be there)
footnotes = soup.find('div', class_='footnotes')
if footnotes:
    print("\nFound footnotes section!")
    print(footnotes.prettify()[:1000])
else:
    print("\nNo footnotes section.")

# Check for any data attributes on crossref sup elements
passage = soup.find('div', class_='passage-text')
if passage:
    crossrefs = passage.find_all('sup', class_='crossreference')
    if crossrefs:
        print(f"\nFound {len(crossrefs)} crossref markers")
        print("\nFirst crossref element details:")
        cr = crossrefs[0]
        print(f"  Text: {cr.get_text()}")
        print(f"  Attributes: {cr.attrs}")
        print(f"  HTML: {cr}")
        
        # Check if there's a link
        link = cr.find('a')
        if link:
            print(f"  Link href: {link.get('href')}")
            print(f"  Link text: {link.get_text()}")

# Try to find any elements with 'data-' attributes that might contain references
print("\n" + "="*80)
print("Looking for data attributes...")
print("="*80)
for elem in soup.find_all(attrs={"data-cr": True}):
    print(f"Found element with data-cr: {elem.get('data-cr')}")
    
for elem in soup.find_all(attrs={"data-ref": True}):
    print(f"Found element with data-ref: {elem.get('data-ref')}")

# Save full HTML for manual inspection
with open('test_crossref_data.html', 'w', encoding='utf-8') as f:
    f.write(soup.prettify())
print("\nFull HTML saved to test_crossref_data.html")
