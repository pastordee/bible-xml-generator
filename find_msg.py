#!/usr/bin/env python3
"""
Search for The Message Bible
"""
import requests

API_KEY = "pyExkJPN1XXpoJ39Xa8Xi"
BASE_URL = "https://rest.api.bible/v1/bibles"

headers = {"api-key": API_KEY}
response = requests.get(BASE_URL, headers=headers, timeout=10)

if response.status_code == 200:
    data = response.json()
    bibles = data.get("data", [])
    
    print("Searching for 'The Message'...")
    print("="*80)
    
    for bible in bibles:
        name = (bible.get('name') or '').lower()
        abbr = (bible.get('abbreviation') or '').lower()
        
        if 'message' in name or 'msg' in abbr:
            print(f"\nID: {bible.get('id')}")
            print(f"  Name: {bible.get('name')}")
            print(f"  Abbreviation: {bible.get('abbreviation')}")
            print(f"  Language: {bible.get('language', {}).get('name')}")
            print(f"  Description: {bible.get('description')}")
            print(f"  Copyright: {(bible.get('copyright') or 'N/A')[:100]}")
