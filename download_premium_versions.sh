#!/bin/bash
# Download premium Bible versions: NKJV, AMP, NLT
# Note: MSG (The Message) is not available through API.Bible

echo "Starting download of premium versions: NKJV, AMP, NLT"
echo "Note: The Message (MSG) is not available through API.Bible"
echo "This will run in the background..."

# Start the download in background
nohup bash -c 'echo -e "2\nNKJV,AMP,NLT" | .venv/bin/python create_other_version_chapters.py > premium_download.log 2>&1' &

# Get the process ID
PID=$!
echo "Process started with PID: $PID"
echo "Monitor progress with: tail -f premium_download.log"
echo "Or check file counts with: ./monitor_download.sh"
