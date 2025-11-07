#!/usr/bin/env python3
"""
Content Freshness Checker for API.Bible Compliance
Ensures Bible content is refreshed within 30-day requirement per Terms of Service
"""

import os
import datetime
import json
from pathlib import Path

def check_content_freshness(base_dir, max_age_days=30):
    """
    Check the freshness of generated Bible content files.
    
    Args:
        base_dir (str): Base directory containing version folders
        max_age_days (int): Maximum age in days before content needs refresh (default: 30)
    
    Returns:
        dict: Report containing outdated files and recommendations
    """
    
    report = {
        "check_date": datetime.datetime.now().isoformat(),
        "max_age_days": max_age_days,
        "version_status": {},
        "outdated_files": [],
        "needs_refresh": False,
        "total_files_checked": 0
    }
    
    base_path = Path(base_dir)
    cutoff_date = datetime.datetime.now() - datetime.timedelta(days=max_age_days)
    
    # Bible version directories to check
    version_dirs = ['kjv', 'web', 'asv', 'bsb', 'cev', 'msg', 'esv']
    
    for version_dir in version_dirs:
        version_path = base_path / version_dir
        if not version_path.exists():
            continue
            
        version_status = {
            "version": version_dir.upper(),
            "files_checked": 0,
            "outdated_files": 0,
            "newest_file_date": None,
            "oldest_file_date": None,
            "needs_refresh": False
        }
        
        xml_files = list(version_path.glob("*.xml"))
        for xml_file in xml_files:
            report["total_files_checked"] += 1
            version_status["files_checked"] += 1
            
            # Get file modification time
            file_mtime = datetime.datetime.fromtimestamp(xml_file.stat().st_mtime)
            
            # Track newest and oldest files
            if version_status["newest_file_date"] is None or file_mtime > version_status["newest_file_date"]:
                version_status["newest_file_date"] = file_mtime
            if version_status["oldest_file_date"] is None or file_mtime < version_status["oldest_file_date"]:
                version_status["oldest_file_date"] = file_mtime
            
            # Check if file is outdated
            if file_mtime < cutoff_date:
                version_status["outdated_files"] += 1
                version_status["needs_refresh"] = True
                report["needs_refresh"] = True
                
                file_info = {
                    "file": str(xml_file.relative_to(base_path)),
                    "version": version_dir.upper(),
                    "modified_date": file_mtime.isoformat(),
                    "days_old": (datetime.datetime.now() - file_mtime).days
                }
                report["outdated_files"].append(file_info)
        
        if version_status["files_checked"] > 0:
            report["version_status"][version_dir.upper()] = version_status
    
    return report

def generate_freshness_report(base_dir, output_file=None):
    """
    Generate a comprehensive freshness report and optionally save to file.
    """
    report = check_content_freshness(base_dir)
    
    print("=" * 70)
    print("API.Bible Content Freshness Report")
    print("=" * 70)
    print(f"Check Date: {report['check_date']}")
    print(f"Maximum Age Allowed: {report['max_age_days']} days")
    print(f"Total Files Checked: {report['total_files_checked']}")
    print(f"Compliance Status: {'⚠️  NEEDS REFRESH' if report['needs_refresh'] else '✅ COMPLIANT'}")
    print()
    
    # Version-by-version status
    for version, status in report["version_status"].items():
        status_icon = "⚠️" if status["needs_refresh"] else "✅"
        print(f"{status_icon} {version}:")
        print(f"   Files Checked: {status['files_checked']}")
        print(f"   Outdated Files: {status['outdated_files']}")
        
        if status["newest_file_date"]:
            newest_age = (datetime.datetime.now() - status["newest_file_date"]).days
            print(f"   Newest File: {newest_age} days old")
        
        if status["oldest_file_date"]:
            oldest_age = (datetime.datetime.now() - status["oldest_file_date"]).days
            print(f"   Oldest File: {oldest_age} days old")
        print()
    
    # Detailed outdated files
    if report["outdated_files"]:
        print("📋 OUTDATED FILES REQUIRING REFRESH:")
        print("-" * 50)
        for file_info in report["outdated_files"]:
            print(f"   {file_info['file']} ({file_info['version']}) - {file_info['days_old']} days old")
        print()
        
        print("🔄 RECOMMENDED ACTIONS:")
        outdated_versions = set(f["version"] for f in report["outdated_files"])
        for version in outdated_versions:
            print(f"   - Regenerate {version} content using API")
        print()
    
    # Save report to file if requested
    if output_file:
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        print(f"📄 Full report saved to: {output_file}")
    
    return report

def add_freshness_metadata_to_xml():
    """
    Add generation timestamp metadata to XML files for tracking purposes.
    This function can be integrated into the generation scripts.
    """
    metadata_template = f"""
    <!-- Content Generation Metadata -->
    <generation_info>
        <generated_date>{datetime.datetime.now().isoformat()}</generated_date>
        <api_compliance>API.Bible Terms of Service - 30-day refresh requirement</api_compliance>
        <next_refresh_due>{(datetime.datetime.now() + datetime.timedelta(days=30)).isoformat()}</next_refresh_due>
    </generation_info>
    """
    return metadata_template.strip()

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Check API.Bible content freshness compliance")
    parser.add_argument("--base-dir", default=".", help="Base directory containing Bible version folders")
    parser.add_argument("--max-age", type=int, default=30, help="Maximum age in days (default: 30)")
    parser.add_argument("--output", help="Save detailed report to JSON file")
    parser.add_argument("--quiet", action="store_true", help="Only show non-compliant items")
    
    args = parser.parse_args()
    
    try:
        report = generate_freshness_report(args.base_dir, args.output)
        
        # Exit with error code if refresh is needed (useful for CI/CD)
        if report["needs_refresh"]:
            exit(1)
        else:
            exit(0)
            
    except Exception as e:
        print(f"Error checking content freshness: {e}")
        exit(2)