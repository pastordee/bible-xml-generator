#!/usr/bin/env python3
"""
Create a priority list of chapters closest to 100% completion.
"""

import sys
import re

priority_list = []

for line in sys.stdin:
    line = line.strip()
    if '%' in line and 'missing' in line:
        # Use regex to parse the line
        match = re.search(r'(\S+)\s+(\d+)\s+-\s+(\d+\.\d+)%.*?(\d+)\s+missing', line)
        if match:
            book = match.group(1)
            chapter = match.group(2)
            pct = float(match.group(3))
            missing = int(match.group(4))
            
            if 90 <= pct < 100:
                priority_list.append((missing, pct, book, chapter))

# Sort by missing count (lowest first) then by percentage (highest first)
priority_list.sort(key=lambda x: (x[0], -x[1]))

print('TOP 50 PRIORITY CHAPTERS (Closest to 100%)')
print('=' * 80)
print(f"Rank  Book                  Ch    %      Missing")
print('-' * 80)

for i, (missing, pct, book, chapter) in enumerate(priority_list[:50], 1):
    print(f"{i:<5} {book:<20} {chapter:<5} {pct:>5.1f}%  {missing}")

print()
print(f'Total chapters at 90-99%: {len(priority_list)}')
print(f'Total missing refs for top 50: {sum(x[0] for x in priority_list[:50])}')
print(f'Total missing refs for all 90-99%: {sum(x[0] for x in priority_list)}')
