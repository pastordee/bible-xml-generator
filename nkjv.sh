#!/bin/bash

# Path to the zip file
ZIP_FILE="xml_nkjv.zip"

# Generate the MD5 hash
HASH=$(md5sum "$ZIP_FILE" | awk '{ print $1 }')

# Save the hash to a .hash file
echo "$HASH" > "${ZIP_FILE}.hash"

echo "Hash for $ZIP_FILE saved to ${ZIP_FILE}.hash"
