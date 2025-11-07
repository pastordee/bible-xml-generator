#!/bin/bash

# Script to package Bible XML files for server deployment
# Creates individual zip files for each version with MD5 hashes

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "============================================================"
echo "BIBLE XML PACKAGING SCRIPT"
echo "============================================================"

# Create readyForServer directory
OUTPUT_DIR="readyForServer"
if [ -d "$OUTPUT_DIR" ]; then
    echo -e "${YELLOW}⚠️  Removing existing $OUTPUT_DIR directory...${NC}"
    rm -rf "$OUTPUT_DIR"
fi

mkdir -p "$OUTPUT_DIR"
echo -e "${GREEN}✅ Created $OUTPUT_DIR directory${NC}"
echo ""

# List of Bible version folders to package (with xml_ prefix)
# Note: xml_kjv is skipped due to zip hanging issue
VERSIONS=("xml_esv" "xml_web" "xml_asv" "xml_bsb" "xml_msg" "xml_nkjv" "xml_amp" "xml_nlt")

# Package each version
for version in "${VERSIONS[@]}"; do
    if [ -d "$version" ]; then
        echo -e "${BLUE}📦 Processing $version...${NC}"
        
        # Count files
        file_count=$(find "$version" -name "*.xml" | wc -l | tr -d ' ')
        echo "   Found $file_count XML files"
        
        # Create zip file in readyForServer directory (keep xml_ prefix in zip name)
        ZIP_FILE="$OUTPUT_DIR/${version}.zip"
        echo "   Creating zip file..."
        
        # Use zip command to create archive (cd into directory first to avoid issues)
        if (cd "$version" && zip -q -r "../$ZIP_FILE" *.xml); then
            # Get file size
            size=$(du -h "$ZIP_FILE" | cut -f1)
            echo "   ✅ Created $ZIP_FILE (${size})"
            
            # Generate MD5 hash
            if command -v md5sum &> /dev/null; then
                # Linux
                HASH=$(md5sum "$ZIP_FILE" | awk '{ print $1 }')
            elif command -v md5 &> /dev/null; then
                # macOS
                HASH=$(md5 -q "$ZIP_FILE")
            else
                echo "   ⚠️  Warning: Neither md5sum nor md5 command found"
                HASH="UNAVAILABLE"
            fi
            
            # Save hash to file
            HASH_FILE="${ZIP_FILE}.hash"
            echo "$HASH" > "$HASH_FILE"
            echo "   ✅ Generated hash: $HASH"
            echo ""
        else
            echo "   ❌ Failed to create zip file"
            echo ""
        fi
    else
        echo -e "${YELLOW}⚠️  Skipping $version (directory not found)${NC}"
        echo ""
    fi
done

# Create a summary file
SUMMARY_FILE="$OUTPUT_DIR/package_summary.txt"
echo "============================================================" > "$SUMMARY_FILE"
echo "BIBLE XML PACKAGE SUMMARY" >> "$SUMMARY_FILE"
echo "Generated: $(date)" >> "$SUMMARY_FILE"
echo "============================================================" >> "$SUMMARY_FILE"
echo "" >> "$SUMMARY_FILE"

for version in "${VERSIONS[@]}"; do
    ZIP_FILE="$OUTPUT_DIR/${version}.zip"
    HASH_FILE="${ZIP_FILE}.hash"
    
    if [ -f "$ZIP_FILE" ]; then
        size=$(du -h "$ZIP_FILE" | cut -f1)
        file_count=$(unzip -l "$ZIP_FILE" | tail -1 | awk '{print $2}')
        hash=$(cat "$HASH_FILE" 2>/dev/null || echo "N/A")
        
        echo "Version: $(echo $version | tr '[:lower:]' '[:upper:]')" >> "$SUMMARY_FILE"
        echo "  File: ${version}.zip" >> "$SUMMARY_FILE"
        echo "  Size: $size" >> "$SUMMARY_FILE"
        echo "  Files: $file_count" >> "$SUMMARY_FILE"
        echo "  MD5: $hash" >> "$SUMMARY_FILE"
        echo "" >> "$SUMMARY_FILE"
    fi
done

echo "============================================================"
echo -e "${GREEN}✅ PACKAGING COMPLETE!${NC}"
echo "============================================================"
echo ""
echo "📁 Output directory: $OUTPUT_DIR"
echo "📄 Summary file: $SUMMARY_FILE"
echo ""
echo "Contents:"
ls -lh "$OUTPUT_DIR"
echo ""
echo "============================================================"

# Display summary
if [ -f "$SUMMARY_FILE" ]; then
    cat "$SUMMARY_FILE"
fi
