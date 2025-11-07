#!/bin/bash
# Resume API.Bible downloads intelligently (skips completed versions and existing files)

echo "Resuming Bible downloads with smart skip..."
echo "This will:"
echo "  ✓ Skip versions that are 100% complete"
echo "  ✓ Skip files that already exist"
echo "  ✓ Continue from the last incomplete version"
echo ""

# Show current status
.venv/bin/python download_api_bible_smart.py 2>&1 | head -20

echo ""
read -p "Press Enter to start/resume downloads, or Ctrl+C to cancel..."

# Start the smart download in background
nohup .venv/bin/python download_api_bible_smart.py > smart_download.log 2>&1 &

PID=$!
echo ""
echo "✅ Smart download started with PID: $PID"
echo "📊 Monitor progress: ./monitor_download.sh"
echo "📄 Check logs: tail -f smart_download.log"
echo "🛑 To stop: pkill -f download_api_bible_smart.py"
