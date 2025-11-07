#!/bin/bash
# Monitor the progress of Bible download across all versions

echo "=============================================="
echo "Bible Download Progress Monitor"
echo "Date: $(date)"
echo "=============================================="
echo ""

# Check if process is running
if ps aux | grep -v grep | grep -q create_other_version_chapters.py; then
    echo "✅ Download process is RUNNING"
    echo ""
else
    echo "❌ Download process is NOT running"
    echo ""
fi

# Count files per version
echo "--- Files downloaded per version ---"
total=0
for dir in kjv web asv bsb cev fbv gnv dra brs lsv msg nkjv amp nlt; do
    if [ -d "$dir" ]; then
        count=$(ls "$dir"/*.xml 2>/dev/null | wc -l | tr -d ' ')
        upper_dir=$(echo "$dir" | tr '[:lower:]' '[:upper:]')
        printf "%-6s: %4d / 1189 chapters (%.1f%%)\n" "$upper_dir" "$count" $(echo "scale=1; $count * 100 / 1189" | bc)
        total=$((total + count))
    fi
done

echo ""
echo "Total chapters downloaded: $total"
echo ""

# Show most recent files
echo "--- Most recently created files (last 5) ---"
find kjv web asv bsb cev fbv gnv dra brs lsv nkjv amp nlt -name "*.xml" -type f 2>/dev/null | xargs ls -lt | head -5 | awk '{print $9, $6, $7, $8}'

echo ""
echo "--- Log file tail (if exists) ---"
if [ -f "full_bible_download.log" ]; then
    tail -5 full_bible_download.log 2>/dev/null | grep -v "^$"
else
    echo "(No log file found)"
fi

echo ""
echo "=============================================="
echo "Run this script again to see updated progress"
echo "=============================================="
