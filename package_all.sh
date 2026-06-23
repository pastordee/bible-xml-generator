#!/bin/bash

# Package all Bible versions for server deployment
# Creates zip files with MD5 hashes for each version

OUTPUT_DIR="readyForServer"
mkdir -p "$OUTPUT_DIR"

echo "========================================"
echo "  PACKAGING ALL BIBLE VERSIONS"
echo "========================================"
echo ""

# List of all versions to package
VERSIONS=("amp" "asv" "bbe" "bsb" "esv" "kjv" "msg" "nkjv" "nlt" "web")

for VERSION in "${VERSIONS[@]}"; do
    SOURCE_DIR="xml_${VERSION}"
    
    # Check if source directory exists
    if [ ! -d "$SOURCE_DIR" ]; then
        echo "⚠ Skipping $VERSION (directory not found)"
        continue
    fi
    
    echo "Packaging $VERSION..."
    ZIP_FILE="${OUTPUT_DIR}/xml_${VERSION}.zip"
    
    # Count XML files
    FILE_COUNT=$(find "$SOURCE_DIR" -name "*.xml" -type f | wc -l | tr -d ' ')

    # Normalize word-boundary spacing around inline <crossref> markers so the
    # published data never ships with glued words (idempotent; no-op if clean).
    python3 fix_crossref_spacing.py --apply "$SOURCE_DIR"

    # Create zip file
    cd "$SOURCE_DIR" && zip -q -r "../${ZIP_FILE}" *.xml cross_refs/ 2>/dev/null
    cd ..
    
    # Generate MD5 hash
    if [ -f "$ZIP_FILE" ]; then
        SIZE=$(du -h "$ZIP_FILE" | cut -f1)
        MD5=$(md5 -q "$ZIP_FILE")
        echo "$MD5" > "${ZIP_FILE}.hash"
        
        echo "  ✓ xml_${VERSION}.zip ($SIZE, $FILE_COUNT files)"
    else
        echo "  ✗ Failed to create xml_${VERSION}.zip"
    fi
    
    echo ""
done

echo "========================================"
echo "  PACKAGING COMPLETE"
echo "========================================"
echo ""
echo "All packages saved to: $OUTPUT_DIR/"
ls -lh "$OUTPUT_DIR"/*.zip | awk '{print "  " $9 " - " $5}'
