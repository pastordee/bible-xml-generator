#!/bin/bash

# Package a single Bible version
# Usage: bash package_single.sh <version>
# Example: bash package_single.sh esv

if [ -z "$1" ]; then
    echo "Error: Version name required"
    echo "Usage: bash package_single.sh <version>"
    echo "Example: bash package_single.sh esv"
    exit 1
fi

VERSION=$1
SOURCE_DIR="xml_${VERSION}"
OUTPUT_DIR="readyForServer"
ZIP_FILE="${OUTPUT_DIR}/xml_${VERSION}.zip"

# Check if source directory exists
if [ ! -d "$SOURCE_DIR" ]; then
    echo "Error: Directory $SOURCE_DIR not found"
    exit 1
fi

# Create output directory if it doesn't exist
mkdir -p "$OUTPUT_DIR"

echo "Packaging $SOURCE_DIR..."

# Count XML files
FILE_COUNT=$(find "$SOURCE_DIR" -name "*.xml" -type f | wc -l | tr -d ' ')
echo "Found $FILE_COUNT XML files"

# Create zip file
echo "Creating zip file (this may take a moment)..."
cd "$SOURCE_DIR" && zip -q -r "../${ZIP_FILE}" *.xml cross_refs/ 2>/dev/null
cd ..

# Check if zip was created successfully
if [ -f "$ZIP_FILE" ]; then
    SIZE=$(du -h "$ZIP_FILE" | cut -f1)
    MD5=$(md5 -q "$ZIP_FILE")
    
    # Save MD5 hash
    echo "$MD5" > "${ZIP_FILE}.hash"
    
    echo "✓ Created $ZIP_FILE"
    echo "  Size: $SIZE"
    echo "  MD5: $MD5"
    echo ""
    echo "✓ Package complete!"
else
    echo "✗ Failed to create $ZIP_FILE"
    exit 1
fi
