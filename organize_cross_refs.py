#!/usr/bin/env python3
"""
Organize cross-reference files into individual book folders.
Creates a subfolder for each book and moves all chapter files into that folder.
"""

import os
import re
from pathlib import Path
from collections import defaultdict

def extract_book_name(filename):
    """Extract book name from filename like refs_genesis_1.txt -> genesis"""
    # Remove refs_ prefix and .txt suffix
    name = filename.replace('refs_', '').replace('.txt', '')
    
    # Remove chapter number at the end
    # Handle cases like genesis_1, 1_samuel_1, song_of_solomon_1
    parts = name.split('_')
    
    # If last part is a number, remove it
    if parts[-1].isdigit():
        parts = parts[:-1]
    
    # Join back the book name
    book_name = '_'.join(parts)
    return book_name

def extract_chapter_number(filename, book_name):
    """Extract chapter number from filename like refs_genesis_1.txt -> 1"""
    # Remove refs_ prefix and .txt suffix
    name = filename.replace('refs_', '').replace('.txt', '')
    
    # Remove the book name prefix
    # For genesis_1 -> remove genesis_ -> 1
    # For 1_samuel_1 -> remove 1_samuel_ -> 1
    chapter_part = name.replace(book_name + '_', '')
    
    return chapter_part

def organize_cross_refs():
    """Organize cross-reference files into book folders."""
    cross_refs_dir = Path(__file__).parent / "raw" / "cross_refs"
    
    if not cross_refs_dir.exists():
        print(f"❌ Cross-refs directory not found: {cross_refs_dir}")
        return
    
    # Find all reference files
    ref_files = list(cross_refs_dir.glob("refs_*.txt"))
    
    if not ref_files:
        print("No reference files found.")
        return
    
    print(f"Found {len(ref_files)} reference files to organize.")
    
    # Group files by book
    books = defaultdict(list)
    for file_path in ref_files:
        book_name = extract_book_name(file_path.name)
        books[book_name].append(file_path)
    
    print(f"\nFound {len(books)} unique books:")
    for book, files in sorted(books.items()):
        print(f"  {book}: {len(files)} chapters")
    
    # Ask for confirmation
    response = input(f"\n⚠️  Create {len(books)} book folders and organize files? (yes/no): ")
    
    if response.lower() != 'yes':
        print("❌ Operation cancelled.")
        return
    
    print("\nOrganizing files...")
    
    # Create folders and move files
    folders_created = 0
    files_moved = 0
    failed_count = 0
    
    for book_name, file_list in sorted(books.items()):
        # Create book folder
        book_folder = cross_refs_dir / book_name
        try:
            book_folder.mkdir(exist_ok=True)
            folders_created += 1
            
            # Move and rename files into folder
            for file_path in file_list:
                try:
                    # Extract chapter number and create simple filename
                    chapter_num = extract_chapter_number(file_path.name, book_name)
                    new_filename = f"{chapter_num}.txt"
                    new_path = book_folder / new_filename
                    
                    file_path.rename(new_path)
                    files_moved += 1
                except Exception as e:
                    print(f"❌ Failed to move {file_path.name}: {e}")
                    failed_count += 1
            
            if files_moved % 100 == 0 and files_moved > 0:
                print(f"  Moved {files_moved} files...")
                
        except Exception as e:
            print(f"❌ Failed to create folder {book_name}: {e}")
            failed_count += 1
    
    print(f"\n✅ Organization complete!")
    print(f"   Folders created: {folders_created}")
    print(f"   Files moved: {files_moved}")
    if failed_count > 0:
        print(f"   Failed: {failed_count}")
    
    # Show final structure
    print(f"\n📁 Final structure:")
    print(f"   {cross_refs_dir}")
    for book_folder in sorted(cross_refs_dir.iterdir()):
        if book_folder.is_dir():
            file_count = len(list(book_folder.glob("*.txt")))
            print(f"     ├── {book_folder.name}/ ({file_count} files)")

if __name__ == "__main__":
    organize_cross_refs()
