#!/usr/bin/env python3
"""
List all Bible versions available with your current API key
"""
import requests
import json

API_KEY = "pyExkJPN1XXpoJ39Xa8Xi"  # Your premium API key
BASE_URL = "https://rest.api.bible/v1/bibles"

def list_all_bibles():
    """Fetch and display all available Bible versions"""
    print("="*80)
    print("LISTING ALL AVAILABLE BIBLE VERSIONS")
    print("="*80)
    
    headers = {"api-key": API_KEY}
    
    try:
        response = requests.get(BASE_URL, headers=headers, timeout=10)
        print(f"\nAPI Response Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            bibles = data.get("data", [])
            
            print(f"\nTotal Bibles Available: {len(bibles)}")
            print("\n" + "="*80)
            
            # Group by language
            by_language = {}
            for bible in bibles:
                lang = bible.get("language", {}).get("name", "Unknown")
                if lang not in by_language:
                    by_language[lang] = []
                by_language[lang].append(bible)
            
            # Display English versions first
            if "English" in by_language:
                print(f"\n{'='*80}")
                print(f"ENGLISH VERSIONS ({len(by_language['English'])} available)")
                print(f"{'='*80}\n")
                
                for bible in sorted(by_language['English'], key=lambda x: x.get('abbreviation', '')):
                    print(f"ID: {bible.get('id', 'N/A')}")
                    print(f"  Name: {bible.get('name', 'N/A')}")
                    print(f"  Abbreviation: {bible.get('abbreviation', 'N/A')}")
                    print(f"  Description: {bible.get('description', 'N/A')[:100]}")
                    
                    # Check if it has copyright (usually indicates commercial version)
                    copyright_info = bible.get('copyright', '')
                    if copyright_info:
                        print(f"  Copyright: {copyright_info[:80]}...")
                    
                    print()
            
            # List other languages briefly
            other_languages = {k: v for k, v in by_language.items() if k != "English"}
            if other_languages:
                print(f"\n{'='*80}")
                print(f"OTHER LANGUAGES ({sum(len(v) for v in other_languages.values())} versions)")
                print(f"{'='*80}\n")
                for lang, versions in sorted(other_languages.items()):
                    print(f"{lang}: {len(versions)} version(s)")
            
        elif response.status_code == 401:
            print("\n❌ ERROR: Invalid API key (401 Unauthorized)")
            print("Please check your API key at https://scripture.api.bible")
        elif response.status_code == 403:
            print("\n❌ ERROR: Access forbidden (403)")
            print("Your API key may not have the necessary permissions")
        else:
            print(f"\n❌ ERROR: {response.status_code}")
            print(f"Response: {response.text[:500]}")
            
    except Exception as e:
        print(f"\n❌ Exception occurred: {str(e)}")

if __name__ == "__main__":
    list_all_bibles()
