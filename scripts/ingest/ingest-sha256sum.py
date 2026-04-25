# SPDX-License-Identifier: AGPL-3.0
#!/usr/bin/env python3
"""Ingest a sha256sum listing file into data-file.csv.

Usage: python3 ingest-sha256sum.py <sha256sum-file> [--year YYYY]

Parses each line (hash  path or hash *path), filters out paths matching
ignore patterns, and appends to data-file.csv.

The --year flag prepends YYYY/ to each path to match archive root structure
(e.g. 20260307-asahi/foo -> 2026/20260307-asahi/foo).
"""

import csv
import re
import sys
import os
from pathlib import Path

CSVS_DIR = Path(os.environ.get("CSVS", "csvs"))
OUTPUT = CSVS_DIR / "data-file.csv"
SCRIPTS_DIR = Path(__file__).parent
IGNORE_FILES = [SCRIPTS_DIR / "always.ignore", SCRIPTS_DIR / "all.ignore"]


def load_ignore_patterns(ignore_files):
    """Compile all ignore patterns into a single list of regexes."""
    patterns = []
    for f in ignore_files:
        if not f.exists():
            continue
        with open(f, "r", encoding="utf-8") as fh:
            for line in fh:
                line = line.rstrip("\n\r")
                if line:
                    try:
                        patterns.append(re.compile(line))
                    except re.error as e:
                        print(f"Warning: bad regex in {f.name}: {line!r} ({e})", file=sys.stderr)
    return patterns


def should_ignore(path, ignore_patterns):
    """Return True if path matches any ignore pattern."""
    for pat in ignore_patterns:
        if pat.search(path):
            return True
    return False


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Ingest sha256sum listing into data-file.csv")
    parser.add_argument("sha256sum_file", help="Path to sha256sum listing file")
    parser.add_argument("--year", help="Prepend YYYY/ to paths (e.g. 2026)")
    args = parser.parse_args()

    sha256sum_file = Path(args.sha256sum_file)
    if not sha256sum_file.exists():
        print(f"Error: {sha256sum_file} not found", file=sys.stderr)
        sys.exit(1)

    print(f"Loading ignore patterns...", file=sys.stderr)
    ignore_patterns = load_ignore_patterns(IGNORE_FILES)
    print(f"Loaded {len(ignore_patterns)} ignore patterns", file=sys.stderr)

    written = 0
    ignored = 0
    errors = 0

    with open(OUTPUT, "a", encoding="utf-8", newline="") as out:
        writer = csv.writer(out)

        with open(sha256sum_file, "r", encoding="utf-8", errors="replace") as f:
            for line_no, line in enumerate(f, 1):
                line = line.rstrip("\n\r")
                if not line:
                    continue

                # sha256sum format: hash  path or hash *path (binary mode)
                if len(line) < 66 or line[64] not in (" ", "*"):
                    # Try two-space separator
                    parts = line.split("  ", 1)
                    if len(parts) != 2 or len(parts[0]) != 64:
                        errors += 1
                        if errors <= 10:
                            print(f"Warning: unparseable line {line_no}: {line[:80]!r}", file=sys.stderr)
                        continue
                    data, path = parts
                else:
                    data = line[:64]
                    sep = line[64]
                    path = line[65:]
                    if sep == " ":
                        path = path.lstrip(" ")

                if args.year:
                    path = f"{args.year}/{path}"

                if should_ignore(path, ignore_patterns):
                    ignored += 1
                    continue

                writer.writerow((data, path))
                written += 1

                if written % 10000 == 0:
                    print(f"  {written} written, {ignored} ignored...", file=sys.stderr)

    print(f"Done: {written} written, {ignored} ignored, {errors} errors", file=sys.stderr)


if __name__ == "__main__":
    main()
