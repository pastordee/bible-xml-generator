#!/usr/bin/env python3
"""Check whether API.Bible bible IDs include the book NAH (Nahum).
"""
import requests

bible_ids = {
    "KJV": "de4e12af7f28f599-02",
    "NKJV": "63097d2a0a2f7db3-01",
    "AMP": "a81b73293d3080c9-01",
    "NLT": "d6e14a625393b4da-01",
    "MSG": "65eec8e0b60e656b-01",
    "WEB": "9879dbb7cfe39e4d-01",
    "ASV": "06125adad2d5898a-01",
    "BSB": "bba9f40183526463-01",
    "CEV": "555fef9a6cb31151-01",
    "FBV": "65eec8e0b60e656b-01",
    "GNV": "c315fa9f71d4af3a-01",
    "DRA": "179568874c45066f-01",
    "BRS": "6bab4d6c61b31b80-01",
    "LSV": "01b29f4b342acc35-01",
}

API_KEY = "pyExkJPN1XXpoJ39Xa8Xi"

for v, bid in bible_ids.items():
    url = f"https://rest.api.bible/v1/bibles/{bid}/books"
    headers = {"api-key": API_KEY}
    print(f"\nChecking {v} ({bid}) -> {url}")
    r = requests.get(url, headers=headers)
    if r.status_code != 200:
        print(f"  Error {r.status_code}: {r.text[:200]}")
        continue
    data = r.json().get('data', [])
    ids = [b.get('id') for b in data]
    # Book id for Nahum should be 'NAH'
    if 'NAH' in ids:
        print("  NAH is present")
    else:
        # Try matching by name too
        names = [b.get('name','').lower() for b in data]
        if any('nahum' in n for n in names):
            print("  NAH present by name")
        else:
            print("  NAH is NOT present")

print('\nDone')
