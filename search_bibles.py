#!/usr/bin/env python3
"""
Search for specific Bible versions by keyword
"""
import requests
import json

API_KEY = "pyExkJPN1XXpoJ39Xa8Xi"
BASE_URL = "https://rest.api.bible/v1/bibles"

def search_bibles(keywords):
    """Search for Bibles matching keywords"""
    headers = {"api-key": API_KEY}
    
    try:
        response = requests.get(BASE_URL, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            bibles = data.get("data", [])
            
            print(f"Searching {len(bibles)} Bibles for keywords: {keywords}")
            print("="*80)
            
            matches = []
            for bible in bibles:
                name = (bible.get('name') or '').lower()
                abbr = (bible.get('abbreviation') or '').lower()
                desc = (bible.get('description') or '').lower()
                
                # Check if any keyword matches
                for keyword in keywords:
                    if keyword.lower() in name or keyword.lower() in abbr or keyword.lower() in desc:
                        matches.append(bible)
                        break
            
            if matches:
                print(f"\nFound {len(matches)} matching versions:\n")
                for bible in matches:
                    print(f"ID: {bible.get('id')}")
                    print(f"  Name: {bible.get('name')}")
                    print(f"  Abbreviation: {bible.get('abbreviation')}")
                    print(f"  Language: {bible.get('language', {}).get('name')}")
                    print(f"  Description: {bible.get('description')}")
                    print()
            else:
                print(f"\n❌ No matches found for: {keywords}")
                print("\nTip: These versions may require special licensing beyond standard premium access.")
                
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    # Search for NIV, NKJV, AMP, and similar versions
    keywords = ["NIV", "International", "NKJV", "New King James", "Amplified", "AMP", 
                "James", "Contemporary", "New Living", "NLT"]
    search_bibles(keywords)
