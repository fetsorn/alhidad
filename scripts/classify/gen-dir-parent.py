#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0
"""Generate dir-parent.csv from data-file.csv.

Reads all file paths, decomposes into directory components,
and outputs (dir, parent) pairs to csvs/dir-parent.csv.
"""

import csv
import sys
from lib import CSVS_DIR, read_csv


def main():
    print("=== gen-dir-parent: reading data-file.csv ===", file=sys.stderr)
    all_dirs = {}  # dir_path -> parent_path (None for roots)
    count = 0

    for _h, p in read_csv("data-file.csv"):
        parts = p.split("/")
        for j in range(1, len(parts)):  # all prefixes except filename
            dir_path = "/".join(parts[:j])
            if dir_path not in all_dirs:
                parent = "/".join(parts[:j - 1]) if j > 1 else ""
                all_dirs[dir_path] = parent
        count += 1
        if count % 100000 == 0:
            print(f"  {count} paths...", file=sys.stderr)

    print(f"  {count} paths -> {len(all_dirs)} directories", file=sys.stderr)

    out_path = CSVS_DIR / "dir-parent.csv"
    with open(out_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        for d in sorted(all_dirs):
            parent = all_dirs[d]
            if parent:
                writer.writerow([d, parent])
    print(f"  wrote {out_path} ({len(all_dirs)} entries)", file=sys.stderr)


if __name__ == "__main__":
    main()
