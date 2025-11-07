#!/usr/bin/env python3
"""
Automated Content Freshness Monitor for API.Bible Compliance
This script can be run as a cron job to monitor content freshness
and trigger regeneration when needed.
"""

import os
import sys
import subprocess
import datetime
from pathlib import Path

# Add the current directory to Python path to import our modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from check_content_freshness import check_content_freshness

def should_regenerate_content(base_dir, warning_days=25, max_age_days=30):
    """
    Check if content should be regenerated based on age.
    
    Args:
        base_dir (str): Base directory containing version folders
        warning_days (int): Days before expiry to start warning (default: 25)
        max_age_days (int): Maximum age before content must be refreshed (default: 30)
    
    Returns:
        dict: Status and recommendations
    """
    report = check_content_freshness(base_dir, max_age_days)
    
    # Check for files approaching expiry
    warning_cutoff = datetime.datetime.now() - datetime.timedelta(days=warning_days)
    approaching_expiry = []
    
    for version, status in report["version_status"].items():
        if status["oldest_file_date"] and status["oldest_file_date"] < warning_cutoff:
            days_until_expiry = max_age_days - (datetime.datetime.now() - status["oldest_file_date"]).days
            approaching_expiry.append({
                "version": version,
                "days_until_expiry": days_until_expiry,
                "action_needed": "warning" if days_until_expiry > 0 else "urgent"
            })
    
    return {
        "needs_immediate_refresh": report["needs_refresh"],
        "approaching_expiry": approaching_expiry,
        "full_report": report
    }

def regenerate_bible_content(versions_to_regenerate):
    """
    Automatically regenerate content for specified Bible versions.
    
    Args:
        versions_to_regenerate (list): List of version abbreviations to regenerate
    """
    
    print("🔄 Starting automatic content regeneration...")
    
    # Books to regenerate (you can customize this list)
    books_to_regenerate = ["rut", "rom", "jhn", "psa"]  # Start with key books
    
    for version in versions_to_regenerate:
        for book in books_to_regenerate:
            print(f"   Regenerating {version} - {book.upper()}...")
            
            try:
                # Prepare input for the generation script
                script_input = f"3\n{book}\n{version}\n"
                
                # Run the generation script
                result = subprocess.run(
                    [sys.executable, "create_other_version_chapters.py"],
                    input=script_input,
                    text=True,
                    capture_output=True,
                    timeout=300  # 5 minute timeout per book
                )
                
                if result.returncode == 0:
                    print(f"   ✅ Successfully regenerated {version} - {book.upper()}")
                else:
                    print(f"   ❌ Failed to regenerate {version} - {book.upper()}")
                    print(f"      Error: {result.stderr}")
                    
            except subprocess.TimeoutExpired:
                print(f"   ⏰ Timeout regenerating {version} - {book.upper()}")
            except Exception as e:
                print(f"   ❌ Exception regenerating {version} - {book.upper()}: {e}")

def send_notification(status):
    """
    Send notification about content status (placeholder for email/Slack/etc.)
    """
    if status["needs_immediate_refresh"]:
        message = "🚨 URGENT: Bible content has exceeded 30-day freshness requirement!"
        print(message)
    elif status["approaching_expiry"]:
        approaching = [v for v in status["approaching_expiry"] if v["days_until_expiry"] <= 5]
        if approaching:
            versions = ", ".join([v["version"] for v in approaching])
            message = f"⚠️  WARNING: Bible content approaching expiry in {len(approaching)} versions: {versions}"
            print(message)

def main():
    """Main automation function"""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    print("=" * 50)
    print("Bible Content Freshness Monitor")
    print(f"Check Time: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)
    
    # Check content status
    status = should_regenerate_content(base_dir)
    
    # Send notifications
    send_notification(status)
    
    # Handle urgent refresh needs
    if status["needs_immediate_refresh"]:
        expired_versions = [
            v for v in status["full_report"]["version_status"].keys()
            if status["full_report"]["version_status"][v]["needs_refresh"]
        ]
        
        print(f"\n🔄 Auto-regenerating expired versions: {', '.join(expired_versions)}")
        regenerate_bible_content(expired_versions)
        
    # Handle approaching expiry (within 5 days)
    elif status["approaching_expiry"]:
        urgent_versions = [
            v["version"] for v in status["approaching_expiry"] 
            if v["days_until_expiry"] <= 5
        ]
        
        if urgent_versions:
            print(f"\n⚠️  Pre-emptive regeneration for versions expiring soon: {', '.join(urgent_versions)}")
            regenerate_bible_content(urgent_versions)
    
    # Summary
    total_versions = len(status["full_report"]["version_status"])
    compliant_versions = sum(1 for v in status["full_report"]["version_status"].values() if not v["needs_refresh"])
    
    print(f"\n📊 Summary:")
    print(f"   Total versions monitored: {total_versions}")
    print(f"   Compliant versions: {compliant_versions}/{total_versions}")
    print(f"   Files checked: {status['full_report']['total_files_checked']}")
    
    if status["needs_immediate_refresh"]:
        print("   Status: ❌ NON-COMPLIANT")
        return 1
    elif status["approaching_expiry"]:
        print("   Status: ⚠️  WARNING")
        return 0
    else:
        print("   Status: ✅ COMPLIANT")
        return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)