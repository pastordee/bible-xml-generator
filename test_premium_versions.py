#!/usr/bin/env python3
"""
Test script to check access to premium Bible versions (NIV, NKJV, AMP)
"""
import requests
import time

API_KEY = "pyExkJPN1XXpoJ39Xa8Xi"  # Premium API key
BASE_URL = "https://rest.api.bible/v1/bibles"

# Premium versions to test
PREMIUM_VERSIONS = {
    "NKJV": "63097d2a0a2f7db3-01",  # New King James Version - CORRECTED ID
    "AMP": "a81b73293d3080c9-01",   # Amplified Bible - CORRECTED ID
    "NLT": "d6e14a625393b4da-01"    # New Living Translation - BONUS!
}

def test_version_access(version_abbr, bible_id):
    """Test if we can access a version by trying to fetch Genesis 1"""
    print(f"\n{'='*60}")
    print(f"Testing {version_abbr} (ID: {bible_id})")
    print(f"{'='*60}")
    
    # First, try to get bible metadata
    headers = {"api-key": API_KEY}
    metadata_url = f"{BASE_URL}/{bible_id}"
    
    print(f"1. Testing metadata access...")
    print(f"   URL: {metadata_url}")
    
    try:
        response = requests.get(metadata_url, headers=headers, timeout=10)
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            bible_data = data.get("data", {})
            print(f"   ✅ Metadata accessible!")
            print(f"   Name: {bible_data.get('name', 'N/A')}")
            print(f"   Language: {bible_data.get('language', {}).get('name', 'N/A')}")
            print(f"   Copyright: {bible_data.get('copyright', 'N/A')[:100]}...")
        elif response.status_code == 403:
            print(f"   ❌ 403 Forbidden - Requires premium subscription")
            return False
        else:
            print(f"   ⚠️  Unexpected response: {response.text[:200]}")
            return False
            
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
        return False
    
    # Second, try to fetch a chapter (Genesis 1)
    time.sleep(2)  # Be polite to API
    print(f"\n2. Testing chapter access (Genesis 1)...")
    chapter_url = f"{BASE_URL}/{bible_id}/chapters/GEN.1"
    print(f"   URL: {chapter_url}")
    
    try:
        response = requests.get(chapter_url, headers=headers, timeout=10)
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            content = data.get("data", {}).get("content", "")
            print(f"   ✅ Chapter accessible!")
            print(f"   Content preview: {content[:150]}...")
            return True
        elif response.status_code == 403:
            print(f"   ❌ 403 Forbidden - Requires premium subscription")
            return False
        else:
            print(f"   ⚠️  Unexpected response: {response.text[:200]}")
            return False
            
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
        return False

def main():
    print("="*60)
    print("TESTING PREMIUM BIBLE VERSION ACCESS")
    print("="*60)
    print(f"\nAPI Key: {API_KEY[:10]}...")
    print(f"Testing 3 premium versions: NKJV, AMP, NLT")
    print(f"Note: NIV is NOT available through API.Bible\n")
    
    results = {}
    
    for version_abbr, bible_id in PREMIUM_VERSIONS.items():
        accessible = test_version_access(version_abbr, bible_id)
        results[version_abbr] = accessible
        time.sleep(3)  # Wait between versions
    
    # Summary
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    
    accessible_versions = [v for v, accessible in results.items() if accessible]
    blocked_versions = [v for v, accessible in results.items() if not accessible]
    
    if accessible_versions:
        print(f"\n✅ ACCESSIBLE VERSIONS ({len(accessible_versions)}):")
        for version in accessible_versions:
            print(f"   - {version}")
    
    if blocked_versions:
        print(f"\n❌ BLOCKED VERSIONS ({len(blocked_versions)}):")
        for version in blocked_versions:
            print(f"   - {version} (requires premium subscription)")
    
    print(f"\n{'='*60}")
    
    if accessible_versions:
        print("\n✨ Good news! You can download these versions.")
        print("   Run the script with these version codes to download.")
    else:
        print("\n⚠️  Unfortunately, all tested versions require premium access.")
        print("   You would need to upgrade your API.Bible subscription to access them.")
        print("\n   More info: https://scripture.api.bible/plans")

if __name__ == "__main__":
    main()
