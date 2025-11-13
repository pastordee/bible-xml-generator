#!/usr/bin/env python3
"""
Extract cross-references from ESV Global Study Bible PDF.
"""

import pdfplumber
import re
from pathlib import Path

def find_john_7_pages(pdf_path):
    """Find pages containing John 7."""
    print("Searching for John 7 in PDF...")
    john_7_pages = []
    
    with pdfplumber.open(pdf_path) as pdf:
        total_pages = len(pdf.pages)
        print(f"Total pages: {total_pages}")
        
        # Search in New Testament range (estimated pages 1700-2200)
        for page_num in range(1700, min(2200, total_pages)):
            if page_num % 50 == 0:
                print(f"Searching page {page_num}...")
            
            page = pdf.pages[page_num]
            text = page.extract_text()
            
            if text and re.search(r'(?:^|\s)John\s+7(?:[:\s]|$)', text, re.MULTILINE):
                john_7_pages.append(page_num)
                print(f"✓ Found John 7 on page {page_num + 1}")
    
    return john_7_pages

def extract_page_text(pdf_path, page_numbers):
    """Extract text from specific pages."""
    texts = []
    with pdfplumber.open(pdf_path) as pdf:
        for page_num in page_numbers:
            page = pdf.pages[page_num]
            text = page.extract_text()
            if text:
                texts.append(f"\n{'='*70}\nPage {page_num + 1}:\n{'='*70}\n{text}")
    return '\n'.join(texts)

def main():
    pdf_path = Path('raw/ESV Global Study Bible - Crossway Bibles-3.pdf')
    
    if not pdf_path.exists():
        print(f"Error: PDF not found at {pdf_path}")
        return
    
    # Find John 7 pages
    john_7_pages = find_john_7_pages(pdf_path)
    
    if not john_7_pages:
        print("\nJohn 7 not found. Let me try a broader search...")
        return
    
    print(f"\nFound John 7 on {len(john_7_pages)} page(s): {[p+1 for p in john_7_pages]}")
    
    # Extract text from those pages and a few surrounding pages
    pages_to_extract = []
    for page_num in john_7_pages:
        pages_to_extract.extend(range(max(0, page_num-1), page_num+3))
    pages_to_extract = sorted(set(pages_to_extract))
    
    print(f"\nExtracting text from pages: {[p+1 for p in pages_to_extract[:10]]}...")
    text = extract_page_text(pdf_path, pages_to_extract[:10])
    
    # Save to file
    output_file = Path('john_7_from_pdf.txt')
    output_file.write_text(text)
    print(f"\n✓ Saved to {output_file}")
    
    # Also print first 3000 chars
    print("\nFirst part of extracted text:")
    print("="*70)
    print(text[:3000])

if __name__ == '__main__':
    main()
