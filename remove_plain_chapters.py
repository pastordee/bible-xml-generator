#!/usr/bin/env python3
"""
Remove plain text chapter files from the raw directory.
This script deletes all files matching the pattern plain_*.txt
"""

import os
from pathlib import Path

def remove_plain_chapters():
    """Remove all plain text chapter files from raw directory."""
    raw_dir = Path(__file__).parent / "raw"
    
    if not raw_dir.exists():
        print(f"❌ Raw directory not found: {raw_dir}")
        return
    
    # Find all plain text chapter files
    plain_files = list(raw_dir.glob("plain_*.txt"))
    
    if not plain_files:
        print("No plain text chapter files found.")
        return
    
    print(f"Found {len(plain_files)} plain text chapter files to remove.")
    print(f"Directory: {raw_dir}")
    
    # Ask for confirmation
    response = input(f"\n⚠️  Are you sure you want to delete {len(plain_files)} files? (yes/no): ")
    
    if response.lower() != 'yes':
        print("❌ Operation cancelled.")
        return
    
    # Remove files
    removed_count = 0
    failed_count = 0
    
    for file_path in plain_files:
        try:
            file_path.unlink()
            removed_count += 1
            if removed_count % 100 == 0:
                print(f"  Removed {removed_count} files...")
        except Exception as e:
            print(f"❌ Failed to remove {file_path.name}: {e}")
            failed_count += 1
    
    print(f"\n✅ Removal complete!")
    print(f"   Removed: {removed_count} files")
    if failed_count > 0:
        print(f"   Failed: {failed_count} files")
    
    # Show remaining file count
    remaining_files = list(raw_dir.glob("*.txt"))
    print(f"   Remaining .txt files in raw/: {len(remaining_files)}")

if __name__ == "__main__":
    remove_plain_chapters()
