# Chapter Text Files for Cross-Reference Insertion

This directory contains text files extracted from the ESV Study Bible PDF with embedded cross-reference letters.

## File Naming Convention

Files should be named: `bookname_chapter.txt`

Examples:
- `john_7.txt` ✓
- `acts_7.txt` ✓
- `genesis_1.txt` ✓
- `psalms_119.txt` ✓
- `1_samuel_17.txt` ✓ (use underscore for numbers)

## How to Create Text Files

1. Open the ESV Study Bible PDF
2. Navigate to the chapter you need
3. Select and copy the entire chapter text (including verse numbers and cross-reference letters)
4. Paste into a new text file in this directory
5. Save with the correct filename format

## Text Format Requirements

The text must include:
- Verse numbers with [†] markers: `7[†]`
- Embedded cross-reference letters: `accord. f He who sent me is true, g and`
- Complete verse text

Example format (see `john_7.txt`):
```
1[†]After this Jesus went about in Galilee. He would not go about in Judea, because 
the Jews p were seeking to kill him.
```

## Running the Batch Script

Once you have created text files for the chapters you want to process:

```bash
python3 batch_add_crossrefs.py
```

The script will:
1. Find all text files in this directory
2. Load missing cross-references from `missing_crossrefs.json`
3. Parse word positions from your text files
4. Insert cross-references at the correct locations in XML
5. Report success/failure for each chapter

## Priority Chapters

Based on the analysis, these chapters have the most missing cross-references:

- Acts 7 (33 missing)
- Lamentations 2 (33 missing)
- Acts 13 (31 missing)
- Acts 8 (30 missing)
- Ezekiel 16 (29 missing)
- Revelation 21 (28 missing)
- Acts 10 (28 missing)
- Acts 2 (27 missing)
- Psalms 78 (27 missing)
- Acts 26 (26 missing)

## Troubleshooting

**"Could not parse verse from text file"**
- Check verse number format: must be `7[†]` not just `7`
- Ensure verse text is complete
- Check for section headings that might interfere with parsing

**"Word not found in XML"**
- The word from the text file doesn't match XML exactly
- Check for punctuation differences
- Manual review may be needed for that verse

**"Text file not found"**
- Check filename format matches exactly
- Use underscores for book names with numbers (e.g., `1_john_1.txt`)

## Template

Use `john_7.txt` as a reference for the correct format.
