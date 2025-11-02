# Bible XML Generator

A Python-based tool for fetching and generating Bible chapter files in XML format from various translations.

## Features

- Fetch Bible content from multiple translations (ESV, KJV, NIV, NKJV, AMP, MSG)
- Generate properly structured XML files for each chapter
- Support for all 66 books of the Bible (1,189 chapters)
- Detailed XML structure with verse markers, headings, and cross-references

## Project Structure

```
bible/
├── create_esv_version_chapters.py      # Script to fetch ESV Bible
├── create_other_version_chapters.py    # Script to fetch other versions via API.Bible
├── check_missing_chapters.py           # Utility to check for missing chapters
├── versions.xml                        # Master list of Bible versions
├── esv/                               # ESV chapter files
├── kjv/                               # KJV chapter files
├── niv/                               # NIV chapter files
├── nkjv/                              # NKJV chapter files
├── amp/                               # Amplified Bible chapter files
└── msg/                               # Message Bible chapter files
```

## Setup

1. Install required dependencies:
```bash
python3 -m pip install requests beautifulsoup4 html5lib
```

2. Get API Keys:
   - **ESV API**: Register at https://api.esv.org/
   - **API.Bible**: Register at https://scripture.api.bible/

3. Add your API keys to the scripts:
   - Update `esv_api_key` in `create_esv_version_chapters.py`
   - Update `api_bible_key` in `create_other_version_chapters.py`

## Usage

### Generate ESV Bible Chapters

```bash
python3 create_esv_version_chapters.py
```

Options:
1. Process test books (Acts and Romans)
2. Process full Bible (all 66 books)
3. Process specific book

### Generate Other Version Chapters

```bash
python3 create_other_version_chapters.py
```

Select versions from: KJV, NIV, NKJV, AMP, MSG

### Check for Missing Chapters

```bash
python3 check_missing_chapters.py
```

## XML Structure

Each chapter file follows this structure:

```xml
<?xml version="1.0" encoding="utf-8"?>
<bible version="ESV">
    <book title="Acts" num="44" testament="new" version="ESV" bookAbbr="act">
        <marker class="begin-verse" mid="v44001001"></marker>
        <chapter num="1">
            <heading>Heading Text</heading>
            <begin-paragraph></begin-paragraph>
            <v n="1">Verse text...</v>
            <marker class="begin-verse" mid="v44001002"></marker>
            <!-- more verses -->
            <end-paragraph></end-paragraph>
        </chapter>
    </book>
</bible>
```

## Bible Books

The Bible contains 66 books (1,189 total chapters):
- **Old Testament**: 39 books (929 chapters)
- **New Testament**: 27 books (260 chapters)

## Notes

- The scripts include a 1-second delay between API requests to respect rate limits
- API.Bible free tier: 5,000 calls/day, 250 calls/hour
- Generated XML files are excluded from version control due to their size

## License

This project is for personal and educational use. Bible translations have their own copyright restrictions - please respect the terms of use for each translation.
