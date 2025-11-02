import os
import re
import xml.etree.ElementTree as ET
from collections import defaultdict
import argparse

def combine_chapters_to_book(version_id, source_dir, target_dir, book_pattern=None):
    """Combines individual chapter XML files into a single book XML file."""
    
    print(f"Source directory: {source_dir}")
    print(f"Target directory: {target_dir}")
    
    # Verify source directory exists
    if not os.path.exists(source_dir):
        print(f"ERROR: Source directory does not exist: {source_dir}")
        return False
        
    # Create target directory if it doesn't exist
    os.makedirs(target_dir, exist_ok=True)
    
    # ... rest of your function ...

# For command-line use
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Combine Bible chapter files into book files")
    parser.add_argument("version", help="Bible version (e.g., ESV, NIV)")
    parser.add_argument("--source", help="Source directory containing chapter files")
    parser.add_argument("--target", help="Target directory for book files")
    parser.add_argument("--book", help="Optional regex pattern to match specific books")
    
    args = parser.parse_args()
    
    # Set default directories if not provided
    base_dir = os.path.dirname(os.path.abspath(__file__))
    source = args.source or os.path.join(base_dir, "esv")
    target = args.target or os.path.join(base_dir, "books", args.version.lower())
    
    result = combine_chapters_to_book(args.version, source, target, args.book)
    print(f"Script completed - success: {result}")