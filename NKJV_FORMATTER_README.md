# NKJV Cross-Reference Formatter

This tool helps you quickly format cross-references copied from the NKJV Study Bible PDF.

## How to Use

### Method 1: Copy-Paste from PDF

1. Open your PDF to the chapter you want to extract
2. Select and copy the cross-reference section (the margin notes with verse letters)
3. Save it to a text file, for example: `genesis_ch3_raw.txt`
4. Run the formatter:
   ```bash
   python3 format_crossrefs.py genesis_ch3_raw.txt
   ```
5. When prompted, enter the chapter number (e.g., `3`)
6. The tool will create a formatted file: `genesis_ch3_raw_formatted.txt`
7. Review the output, make any manual corrections if needed
8. Copy the formatted content to your main `nkjv.txt` file

### Method 2: Interactive Mode

1. Run the formatter without arguments:
   ```bash
   python3 format_crossrefs.py
   ```
2. Paste your cross-reference text
3. Press `Ctrl+D` (Mac/Linux) or `Ctrl+Z` then `Enter` (Windows) when done
4. Enter the chapter number when prompted
5. Review the formatted output
6. Choose whether to save to a file

## What It Does

The formatter automatically:
- ✅ Removes Bible text (keeps only cross-references)
- ✅ Removes commentary and footnotes
- ✅ Separates each verse:letter combination onto its own line
- ✅ Cleans up spacing and formatting
- ✅ Groups references by verse
- ✅ Formats output to match your existing nkjv.txt structure

## Example

### Input (from PDF):
```
CHAPTER 3
1 a Now the serpent was more cunning
than any beast of the field which the LORD
God had made. And he said to the woman,
"Has God indeed said, b 'You shall not eat
of every tree of the garden'?"
2 c And the woman said to the serpent,
1 a Num. 22:28;
Rev. 12:9; 20:2
b Gen. 2:16, 17
2 c Gen. 2:16, 17
```

### Output (formatted):
```
CHAPTER 3

1 a Num. 22:28; Rev. 12:9; 20:2
1 b Gen. 2:16, 17

2 c Gen. 2:16, 17
```

## Converting to Raw Format

After formatting, use the existing parser to convert to raw format:

1. Add the formatted chapter to your `nkjv.txt` file
2. Run the parser:
   ```bash
   python3 parse_nkjv_genesis_v4.py
   ```
3. The parser will generate the raw format files in `raw/cross_refs_nkjv/genesis/`

## Tips

- Copy entire chapter sections at once for efficiency
- The tool handles messy PDF formatting automatically
- Always review the output - PDF extraction isn't perfect
- Common issues to watch for:
  - Missing verse numbers in continuation lines
  - Merged references (e.g., "1 a...b..." on same line)
  - Commentary mixed in with references
  
The formatter catches most of these, but a quick manual review ensures accuracy!

## Workflow Summary

1. **Extract**: Copy chapter from PDF → save to text file
2. **Format**: Run `python3 format_crossrefs.py filename.txt`
3. **Review**: Check the `_formatted.txt` output
4. **Add**: Copy formatted text to your main `nkjv.txt`
5. **Convert**: Run `python3 parse_nkjv_genesis_v4.py`
6. **Done**: Raw format generated in `raw/cross_refs_nkjv/genesis/`

This should reduce your time from ~1 hour per chapter to ~10-15 minutes!
