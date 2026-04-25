# SPDX-License-Identifier: AGPL-3.0
#!/usr/bin/env python3
"""Ingest all sha256sum files from an archive directory.

For each drive directory, finds all *-sha256sum files (excluding checksums
of checksums), extracts the year from the snapshot name, runs the ingest
script, and updates snapshot-drive.csv.

Expects CSVS and ARCHIVE environment variables.
"""

import csv
import os
import re
import subprocess
import sys
from pathlib import Path

ARCHIVE_DIR = Path(os.environ.get("ARCHIVE", "archive"))
CSVS_DIR = Path(os.environ.get("CSVS", "csvs"))
SCRIPTS_DIR = Path(__file__).parent
INGEST_SCRIPT = SCRIPTS_DIR / "ingest-sha256sum.py"
SNAPSHOT_DRIVE = CSVS_DIR / "snapshot-drive.csv"


def extract_year(snapshot_name):
    """Extract 4-digit year from snapshot name."""
    m = re.match(r"(\d{4})", snapshot_name)
    if m:
        return m.group(1)
    return None


def load_existing_snapshots():
    """Load already-ingested snapshots from snapshot-drive.csv."""
    existing = set()
    if SNAPSHOT_DRIVE.exists():
        with open(SNAPSHOT_DRIVE, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            for row in reader:
                if row:
                    existing.add(row[0])
    return existing


def main():
    existing = load_existing_snapshots()
    print(f"Already ingested: {len(existing)} snapshots", file=sys.stderr)

    new_snapshot_drive_rows = []

    for drive_dir in sorted(ARCHIVE_DIR.iterdir()):
        if not drive_dir.is_dir():
            continue
        drive_name = drive_dir.name

        sha_files = sorted([
            f for f in drive_dir.iterdir()
            if f.name.endswith("-sha256sum")
            and not f.name.endswith("-sha256sum-sha256sum")
        ])

        for sha_file in sha_files:
            snapshot = sha_file.name.replace("-sha256sum", "")

            if snapshot in existing:
                print(f"SKIP {snapshot} (already ingested)", file=sys.stderr)
                continue

            year = extract_year(snapshot)
            if not year:
                print(f"SKIP {snapshot} (can't extract year)", file=sys.stderr)
                continue

            # Detect if paths already have year prefix (older consolidated listings)
            # by checking the first parseable line
            needs_year = True
            with open(sha_file, "r", encoding="utf-8", errors="replace") as fh:
                for test_line in fh:
                    test_line = test_line.rstrip("\n\r")
                    if len(test_line) >= 66:
                        test_path = test_line[66:] if test_line[64] == " " else test_line[65:]
                        test_path = test_path.lstrip(" ")
                        if re.match(r"^\d{4}/", test_path):
                            needs_year = False
                        break

            print(f"\n{'='*60}", file=sys.stderr)
            print(f"INGEST {snapshot} (drive: {drive_name}, year: {year}, prepend_year: {needs_year})", file=sys.stderr)
            print(f"  file: {sha_file}", file=sys.stderr)

            env = {**os.environ, "CSVS": str(CSVS_DIR)}
            cmd = ["python3", str(INGEST_SCRIPT), str(sha_file)]
            if needs_year:
                cmd += ["--year", year]
            result = subprocess.run(cmd, capture_output=False, env=env)

            if result.returncode != 0:
                print(f"  ERROR: ingest failed for {snapshot}", file=sys.stderr)
                continue

            new_snapshot_drive_rows.append((snapshot, drive_name))

    # Append new rows to snapshot-drive.csv
    if new_snapshot_drive_rows:
        with open(SNAPSHOT_DRIVE, "a", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            for row in new_snapshot_drive_rows:
                writer.writerow(row)
        print(f"\nAdded {len(new_snapshot_drive_rows)} new snapshots to snapshot-drive.csv", file=sys.stderr)
    else:
        print(f"\nNo new snapshots to ingest", file=sys.stderr)


if __name__ == "__main__":
    main()
