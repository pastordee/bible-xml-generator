#!/bin/bash

# Simple package script for a single version
# Usage: bash package_single.sh <version_name>

if [ -z "$1" ]; then
    echo "Usage: bash package_single.sh <version_name>"
    echo "Example: bash package_single.sh nkjv"
    exit 1
fi

VERSION="$1"
VERSION_DIR="xml_${VERSION}"

if [ ! -d "$VERSION_DIR" ]; then
    echo "Error: Directory $VERSION_DIR not found"
    exit 1
fi

echo "Packaging $VERSION_DIR..."

# Create output directory
mkdir -p readyForServer

# Remove old zip if exists
rm -f "readyForServer/${VERSION_DIR}.zip"

# Count files
FILE_COUNT=$(find "$VERSION_DIR" -name "*.xml" | wc -l | tr -d ' ')
echo "Found $FILE_COUNT XML files"

# Create zip in background and wait for it
echo "Creating zip file (this may take a moment)..."
cd "$VERSION_DIR" && \
zip -r -q "../readyForServer/${VERSION_DIR}.zip" . \
    -x "*.git*" \
    -x "*.DS_Store" \
    -x "__pycache__/*" \
    -x "*.pyc" && \
cd ..

if [ $? -eq 0 ]; then
    echo "✓ Created readyForServer/${VERSION_DIR}.zip"
    
    # Get size
    SIZE=$(du -h "readyForServer/${VERSION_DIR}.zip" | cut -f1)
    echo "  Size: $SIZE"
    
    # Get MD5
    HASH=$(md5 -q "readyForServer/${VERSION_DIR}.zip")
    echo "  MD5: $HASH"
    echo "$HASH" > "readyForServer/${VERSION_DIR}.zip.hash"
    
    echo ""
    echo "✓ Package complete!"
else
    echo "✗ Failed to create zip"
    exit 1
fi
