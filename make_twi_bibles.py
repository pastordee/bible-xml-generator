#!/usr/bin/env python3
"""
Build per-chapter Bible XML (app format) for the two Ghanaian Twi translations
published by Biblica under CC BY-SA 4.0, from eBible.org USFX sources:

  - Akuapem Twi Nkwa Asem  (eBible id: twi)       -> xml_twi/
  - Asante Twi Nkwa Asem   (eBible id: twiasante) -> xml_twiasante/

Source zips: https://ebible.org/Scriptures/twi_usfx.zip
             https://ebible.org/Scriptures/twiasante_usfx.zip

Usage:
    python3 make_twi_bibles.py <path-to-twi_usfx.xml> twi
    python3 make_twi_bibles.py <path-to-twiasante_usfx.xml> twiasante

Output matches the existing xml_<version> folders (see xml_web) so
package_single.sh can zip it for the server as-is.

License note (CC BY-SA 4.0): this is a reformatted derivative work, so per
Biblica's terms the Biblica(R) trademark is NOT used, and the required
attribution line is included in the <copyright> element of every file.
"""
import os
import re
import sys
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta

# usfx code -> (book num, English title, filename slug, bookAbbr, testament)
BOOKS = {
    "GEN": (1, "Genesis", "genesis", "gen", "old"),
    "EXO": (2, "Exodus", "exodus", "exo", "old"),
    "LEV": (3, "Leviticus", "leviticus", "lev", "old"),
    "NUM": (4, "Numbers", "numbers", "num", "old"),
    "DEU": (5, "Deuteronomy", "deuteronomy", "deu", "old"),
    "JOS": (6, "Joshua", "joshua", "jos", "old"),
    "JDG": (7, "Judges", "judges", "jdg", "old"),
    "RUT": (8, "Ruth", "ruth", "rut", "old"),
    "1SA": (9, "1 Samuel", "1_samuel", "1sa", "old"),
    "2SA": (10, "2 Samuel", "2_samuel", "2sa", "old"),
    "1KI": (11, "1 Kings", "1_kings", "1ki", "old"),
    "2KI": (12, "2 Kings", "2_kings", "2ki", "old"),
    "1CH": (13, "1 Chronicles", "1_chronicles", "1ch", "old"),
    "2CH": (14, "2 Chronicles", "2_chronicles", "2ch", "old"),
    "EZR": (15, "Ezra", "ezra", "ezr", "old"),
    "NEH": (16, "Nehemiah", "nehemiah", "neh", "old"),
    "EST": (17, "Esther", "esther", "est", "old"),
    "JOB": (18, "Job", "job", "job", "old"),
    "PSA": (19, "Psalms", "psalms", "psa", "old"),
    "PRO": (20, "Proverbs", "proverbs", "pro", "old"),
    "ECC": (21, "Ecclesiastes", "ecclesiastes", "ecc", "old"),
    "SNG": (22, "Song of Solomon", "song_of_solomon", "sng", "old"),
    "ISA": (23, "Isaiah", "isaiah", "isa", "old"),
    "JER": (24, "Jeremiah", "jeremiah", "jer", "old"),
    "LAM": (25, "Lamentations", "lamentations", "lam", "old"),
    "EZK": (26, "Ezekiel", "ezekiel", "ezk", "old"),
    "DAN": (27, "Daniel", "daniel", "dan", "old"),
    "HOS": (28, "Hosea", "hosea", "hos", "old"),
    "JOL": (29, "Joel", "joel", "jol", "old"),
    "AMO": (30, "Amos", "amos", "amo", "old"),
    "OBA": (31, "Obadiah", "obadiah", "oba", "old"),
    "JON": (32, "Jonah", "jonah", "jon", "old"),
    "MIC": (33, "Micah", "micah", "mic", "old"),
    "NAM": (34, "Nahum", "nahum", "nah", "old"),  # eBible uses NAM, not NAH
    "HAB": (35, "Habakkuk", "habakkuk", "hab", "old"),
    "ZEP": (36, "Zephaniah", "zephaniah", "zep", "old"),
    "HAG": (37, "Haggai", "haggai", "hag", "old"),
    "ZEC": (38, "Zechariah", "zechariah", "zec", "old"),
    "MAL": (39, "Malachi", "malachi", "mal", "old"),
    "MAT": (40, "Matthew", "matthew", "mat", "new"),
    "MRK": (41, "Mark", "mark", "mrk", "new"),
    "LUK": (42, "Luke", "luke", "luk", "new"),
    "JHN": (43, "John", "john", "jhn", "new"),
    "ACT": (44, "Acts", "acts", "act", "new"),
    "ROM": (45, "Romans", "romans", "rom", "new"),
    "1CO": (46, "1 Corinthians", "1_corinthians", "1co", "new"),
    "2CO": (47, "2 Corinthians", "2_corinthians", "2co", "new"),
    "GAL": (48, "Galatians", "galatians", "gal", "new"),
    "EPH": (49, "Ephesians", "ephesians", "eph", "new"),
    "PHP": (50, "Philippians", "philippians", "php", "new"),
    "COL": (51, "Colossians", "colossians", "col", "new"),
    "1TH": (52, "1 Thessalonians", "1_thessalonians", "1th", "new"),
    "2TH": (53, "2 Thessalonians", "2_thessalonians", "2th", "new"),
    "1TI": (54, "1 Timothy", "1_timothy", "1ti", "new"),
    "2TI": (55, "2 Timothy", "2_timothy", "2ti", "new"),
    "TIT": (56, "Titus", "titus", "tit", "new"),
    "PHM": (57, "Philemon", "philemon", "phm", "new"),
    "HEB": (58, "Hebrews", "hebrews", "heb", "new"),
    "JAS": (59, "James", "james", "jas", "new"),
    "1PE": (60, "1 Peter", "1_peter", "1pe", "new"),
    "2PE": (61, "2 Peter", "2_peter", "2pe", "new"),
    "1JN": (62, "1 John", "1_john", "1jn", "new"),
    "2JN": (63, "2 John", "2_john", "2jn", "new"),
    "3JN": (64, "3 John", "3_john", "3jn", "new"),
    "JUD": (65, "Jude", "jude", "jud", "new"),
    "REV": (66, "Revelation", "revelation", "rev", "new"),
}

VERSIONS = {
    "twi": {
        "version": "AKNA",
        "name": "Akuapem Twi Nkwa Asem (Akuapem Twi Contemporary Bible)",
        "abbreviation": "AKNA",
        "copyright": (
            "Akuapem Twi Nkwa Asem (Akuapem Twi Contemporary Bible) "
            "Copyright © 1996, 2020 Biblica, Inc. Released under the Creative Commons "
            "Attribution-ShareAlike 4.0 International License (CC BY-SA 4.0). "
            "Reformatted from the eBible.org USFX edition; content unchanged, trademark removed "
            "per license terms. The original work by Biblica, Inc. is available for free at "
            "www.biblica.com and open.bible."
        ),
    },
    "twiasante": {
        "version": "ASNA",
        "name": "Asante Twi Nkwa Asem (Asante Twi Contemporary Bible)",
        "abbreviation": "ASNA",
        "copyright": (
            "Asante Twi Nkwa Asem (Asante Twi Contemporary Bible) "
            "Copyright © 1996, 2020 Biblica, Inc. Released under the Creative Commons "
            "Attribution-ShareAlike 4.0 International License (CC BY-SA 4.0). "
            "Reformatted from the eBible.org USFX edition; content unchanged, trademark removed "
            "per license terms. The original work by Biblica, Inc. is available for free at "
            "www.biblica.com and open.bible."
        ),
    },
}

# USFX subtrees that are not scripture text: footnotes, cross-references,
# figures, metadata. Their text (and children's) is dropped entirely.
SKIP_TAGS = {"f", "fe", "x", "note", "fig", "id", "h", "toc", "rem", "cl", "ca", "va", "vp"}


def clean(text_parts):
    return re.sub(r"\s+", " ", "".join(text_parts)).strip()


def gather_text(elem):
    """All scripture-visible text inside elem (skipping footnote-like subtrees)."""
    parts = []
    if elem.text:
        parts.append(elem.text)
    for child in elem:
        if child.tag not in SKIP_TAGS:
            parts.append(gather_text(child))
        if child.tail:
            parts.append(child.tail)
    return "".join(parts)


class BookParser:
    """Linear walk over a USFX <book>, splitting content into chapters.

    Each chapter is a list of items:
      ("heading", text)          section heading or psalm descriptor
      ("verse", n, text)         n is the first number of a bridge like "19-22"
    """

    def __init__(self):
        self.chapters = {}  # chapter num -> items
        self.cur_chapter = None
        self.verse_n = None
        self.verse_parts = []

    def flush_verse(self):
        if self.verse_n is not None:
            text = clean(self.verse_parts)
            if text:
                self.chapters[self.cur_chapter].append(("verse", self.verse_n, text))
            self.verse_n = None
            self.verse_parts = []

    def add_text(self, s):
        if s and self.verse_n is not None:
            self.verse_parts.append(s)

    def walk(self, elem):
        tag = elem.tag
        if tag == "c":
            self.flush_verse()
            self.cur_chapter = int(elem.get("id"))
            self.chapters.setdefault(self.cur_chapter, [])
        elif tag == "v":
            self.flush_verse()
            vid = elem.get("id", "")
            m = re.match(r"(\d+)", vid)
            self.verse_n = int(m.group(1)) if m else None
        elif tag == "ve":
            self.flush_verse()
        elif tag in ("s", "d"):
            # headings/psalm descriptors sit between verses
            self.flush_verse()
            text = clean([gather_text(elem)])
            if text and self.cur_chapter is not None:
                self.chapters[self.cur_chapter].append(("heading", text))
            if elem.tail:
                self.add_text(elem.tail)
            return
        elif tag in SKIP_TAGS:
            if elem.tail:
                self.add_text(elem.tail)
            return
        if elem.text:
            self.add_text(elem.text)
        for child in elem:
            self.walk(child)
        if elem.tail:
            self.add_text(elem.tail)


def build_chapter_xml(cfg, book_code, chapter_num, items, now):
    num, title, slug, abbr, testament = BOOKS[book_code]

    bible = ET.Element("bible")
    copyright_el = ET.SubElement(bible, "copyright")
    copyright_el.text = cfg["copyright"]
    metadata = ET.SubElement(bible, "metadata")
    ET.SubElement(metadata, "name").text = cfg["name"]
    ET.SubElement(metadata, "abbreviation").text = cfg["abbreviation"]
    ET.SubElement(metadata, "last_updated").text = "2020-01-01T00:00:00.000Z"
    gen = ET.SubElement(bible, "generation_info")
    ET.SubElement(gen, "generated_date").text = now.isoformat()
    ET.SubElement(gen, "source").text = "eBible.org USFX (CC BY-SA 4.0, no refresh requirement)"

    book_el = ET.SubElement(
        bible, "book",
        title=title, num=str(num), testament=testament,
        version=cfg["version"], bookAbbr=abbr,
    )

    chapter_el = None
    last_verse = 0
    for kind, *rest in items:
        if chapter_el is None:
            # marker for the first verse precedes <chapter>, matching existing files
            ET.SubElement(book_el, "marker", {"class": "begin-verse",
                                              "mid": f"v{num:02d}{chapter_num:03d}001"})
            chapter_el = ET.SubElement(book_el, "chapter", num=str(chapter_num))
        if kind == "heading":
            ET.SubElement(chapter_el, "heading").text = rest[0]
            continue
        n, text = rest
        if last_verse == 0:
            ET.SubElement(chapter_el, "begin-paragraph")
        else:
            ET.SubElement(chapter_el, "marker", {"class": "begin-verse",
                                                 "mid": f"v{num:02d}{chapter_num:03d}{n:03d}"})
        v = ET.SubElement(chapter_el, "v", n=str(n))
        v.text = text
        last_verse = n

    # trailing next-verse marker + end-paragraph, matching existing files
    ET.SubElement(chapter_el, "marker", {"class": "begin-verse",
                                         "mid": f"v{num:02d}{chapter_num:03d}{last_verse + 1:03d}"})
    ET.SubElement(chapter_el, "end-paragraph")

    tree = ET.ElementTree(bible)
    ET.indent(tree, space="\t")
    return tree


def load_book_names(src_path):
    """Twi book names from the BookNames.xml sitting next to the USFX file."""
    path = os.path.join(os.path.dirname(src_path), "BookNames.xml")
    names = {}
    if os.path.exists(path):
        for b in ET.parse(path).getroot():
            names[b.get("code")] = b.get("short", "")
    return names


def build_books_xml(cfg, chapter_counts, local_names):
    root = ET.Element("bible", version=cfg["version"].lower())
    for code, (num, title, slug, abbr, testament) in sorted(BOOKS.items(), key=lambda kv: kv[1][0]):
        attrs = {
            "title": title,
            "bookAbbr": abbr.capitalize() if not abbr[0].isdigit() else abbr,
            "number": str(num),
            "testament": testament,
            "version": cfg["version"],
        }
        local = local_names.get(code)
        if local:
            attrs["localTitle"] = local
        book_el = ET.SubElement(root, "book", attrs)
        for ch in range(1, chapter_counts[code] + 1):
            ET.SubElement(book_el, "chapter", number=str(ch),
                          resourceName=f"{slug}_{ch}", referenceName=f"{slug}_{ch}")
    tree = ET.ElementTree(root)
    ET.indent(tree, space="\t")
    return tree


def main():
    if len(sys.argv) != 3 or sys.argv[2] not in VERSIONS:
        print(__doc__)
        sys.exit(1)
    src, key = sys.argv[1], sys.argv[2]
    cfg = VERSIONS[key]
    out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), f"xml_{key}")
    os.makedirs(out_dir, exist_ok=True)

    now = datetime.now()
    root = ET.parse(src).getroot()
    local_names = load_book_names(src)

    chapter_counts = {}
    total_chapters = total_verses = 0
    for book_el in root.iter("book"):
        code = book_el.get("id")
        if code not in BOOKS:
            print(f"  ! Skipping unknown book {code}")
            continue
        parser = BookParser()
        parser.walk(book_el)
        parser.flush_verse()
        slug = BOOKS[code][2]
        chapter_counts[code] = max(parser.chapters)
        for ch, items in sorted(parser.chapters.items()):
            verses = [i for i in items if i[0] == "verse"]
            if not verses:
                print(f"  ! {code} {ch}: no verses, skipping file")
                continue
            tree = build_chapter_xml(cfg, code, ch, items, now)
            tree.write(os.path.join(out_dir, f"{slug}_{ch}.xml"),
                       encoding="utf-8", xml_declaration=True)
            total_chapters += 1
            total_verses += len(verses)
        print(f"  {code}: {chapter_counts[code]} chapters")

    books_tree = build_books_xml(cfg, chapter_counts, local_names)
    books_tree.write(os.path.join(out_dir, "books.xml"),
                     encoding="utf-8", xml_declaration=True)

    print(f"\n{cfg['name']}")
    print(f"  Books: {len(chapter_counts)}  Chapters: {total_chapters}  Verses: {total_verses}")
    print(f"  Output: {out_dir}")


if __name__ == "__main__":
    main()
