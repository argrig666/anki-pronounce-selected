#!/usr/bin/env python3
"""Build anki-pronounce-selected.ankiaddon distributable package."""

import os
import zipfile

ADDON_DIR = os.path.dirname(os.path.abspath(__file__))
DIST_DIR = os.path.join(ADDON_DIR, "dist")
OUTPUT_ZIP = os.path.join(DIST_DIR, "pronounce_selected.ankiaddon")

INCLUDED_ITEMS = [
    "__init__.py",
    "detector.py",
    "config.json",
    "config.md",
    "manifest.json",
    "README.md",
    "LICENSE",
    "vendor",
]

EXCLUDE_PATTERNS = [
    "__pycache__",
    ".pyc",
    ".git",
    "user_files",
    ".so.dSYM",
    ".DS_Store",
]


def build():
    os.makedirs(DIST_DIR, exist_ok=True)
    if os.path.exists(OUTPUT_ZIP):
        os.remove(OUTPUT_ZIP)

    count = 0
    with zipfile.ZipFile(OUTPUT_ZIP, "w", zipfile.ZIP_DEFLATED) as zf:
        for item in INCLUDED_ITEMS:
            full_path = os.path.join(ADDON_DIR, item)
            if not os.path.exists(full_path):
                continue
            if os.path.isfile(full_path):
                zf.write(full_path, item)
                count += 1
            elif os.path.isdir(full_path):
                for root, dirs, files in os.walk(full_path):
                    # Filter directories in place
                    dirs[:] = [d for d in dirs if not any(ex in d for ex in EXCLUDE_PATTERNS)]
                    for f in files:
                        if any(ex in f for ex in EXCLUDE_PATTERNS):
                            continue
                        fpath = os.path.join(root, f)
                        arcname = os.path.relpath(fpath, ADDON_DIR)
                        zf.write(fpath, arcname)
                        count += 1

    size_mb = os.path.getsize(OUTPUT_ZIP) / (1024 * 1024)
    print(f"Created {OUTPUT_ZIP} ({count} files, {size_mb:.2f} MB)")


if __name__ == "__main__":
    build()
