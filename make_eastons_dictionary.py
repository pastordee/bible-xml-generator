#!/usr/bin/env python3
"""Generate a clean, well-formed Easton's Bible Dictionary for the app.

The ThML file that was previously published to the server was saved from a
browser's XML viewer, so it was NOT well-formed:

  1. It began with a stray text line
     ("This XML file does not appear to have any style information...") sitting
     before the root element.
  2. Its index section contained ~23k bare ``&`` characters inside
     ``href="?scrBook=Gen&scrCh=1&scrV=1..."`` links.

Either one makes a strict XML parser (the app uses Dart's ``xml`` package, and
this script uses ElementTree) reject the whole document, so a downloaded
dictionary parsed to zero entries and the app kept reporting "not downloaded".

This script normalises the source into a valid ``eastons_dictionary.xml``,
validates that all dictionary terms survive, then packages it exactly the way
the app expects to fetch it:

    readyForServer/eastons_dictionary.zip        (contains eastons_dictionary.xml at the root)
    readyForServer/eastons_dictionary.zip.hash   (md5 of the zip + newline)

Upload both files to MinIO at:
    https://media.prayercircle.co.uk/prayer-circle/app_assets/

Usage:
    python3 make_eastons_dictionary.py
    python3 make_eastons_dictionary.py --source path/to/raw.xml
"""

import argparse
import hashlib
import os
import re
import sys
import xml.etree.ElementTree as ET
import zipfile

REPO = os.path.dirname(os.path.abspath(__file__))
DEFAULT_SOURCE = os.path.join(REPO, "dictionaries", "eastons_dictionary.source.xml")
CLEAN_XML = os.path.join(REPO, "dictionaries", "eastons_dictionary.xml")
OUTPUT_DIR = os.path.join(REPO, "readyForServer")
ZIP_PATH = os.path.join(OUTPUT_DIR, "eastons_dictionary.zip")
HASH_PATH = ZIP_PATH + ".hash"

# Inner name MUST stay "eastons_dictionary.xml": the app extracts the zip into a
# folder named after the zip and then reads <that folder>/eastons_dictionary.xml.
ARCNAME = "eastons_dictionary.xml"

# An ampersand that is NOT already the start of a valid XML/numeric entity.
BARE_AMP = re.compile(r"&(?!(?:amp|lt|gt|quot|apos|#\d+|#x[0-9a-fA-F]+);)")

MIN_EXPECTED_TERMS = 3900  # the dictionary has ~3,964 entries


def sanitize(raw: str) -> str:
    """Strip the leading viewer junk and escape bare ampersands."""
    start = raw.find("<")
    if start > 0:
        raw = raw[start:]
    raw = BARE_AMP.sub("&amp;", raw)
    return raw


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--source",
        default=DEFAULT_SOURCE,
        help="Raw Easton's ThML file (default: %(default)s)",
    )
    args = ap.parse_args()

    if not os.path.exists(args.source):
        print(f"✗ Source not found: {args.source}")
        return 1

    print(f"Reading {args.source}...")
    with open(args.source, "r", encoding="utf-8") as fh:
        raw = fh.read()

    cleaned = sanitize(raw)

    # Validate: it must parse, be rooted at <ThML>, and keep every term.
    try:
        root = ET.fromstring(cleaned)
    except ET.ParseError as exc:
        print(f"✗ Cleaned XML still does not parse: {exc}")
        return 1

    terms = len(root.findall(".//term"))
    defs = len(root.findall(".//def"))
    print(f"Parsed OK — root <{root.tag}>, {terms} terms, {defs} definitions")
    if terms < MIN_EXPECTED_TERMS:
        print(
            f"✗ Only {terms} terms found (expected >= {MIN_EXPECTED_TERMS}); aborting."
        )
        return 1

    os.makedirs(os.path.dirname(CLEAN_XML), exist_ok=True)
    with open(CLEAN_XML, "w", encoding="utf-8") as fh:
        fh.write(cleaned)
    print(f"✓ Wrote clean XML: {CLEAN_XML} ({os.path.getsize(CLEAN_XML):,} bytes)")

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    if os.path.exists(ZIP_PATH):
        os.remove(ZIP_PATH)
    with zipfile.ZipFile(ZIP_PATH, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.write(CLEAN_XML, arcname=ARCNAME)
    print(f"✓ Wrote zip: {ZIP_PATH} ({os.path.getsize(ZIP_PATH):,} bytes)")

    md5 = hashlib.md5()
    with open(ZIP_PATH, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            md5.update(chunk)
    digest = md5.hexdigest()
    with open(HASH_PATH, "w", encoding="utf-8") as fh:
        fh.write(digest + "\n")
    print(f"✓ Wrote hash: {HASH_PATH} ({digest})")

    print("\n✓ Done. Upload these to MinIO app_assets/:")
    print(f"    {ZIP_PATH}")
    print(f"    {HASH_PATH}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
