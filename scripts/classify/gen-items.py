#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0
"""Generate graph/items.ttl from item-*.csv and survey-*.csv tablets."""

import sys
from lib import GRAPH_DIR, PREFIXES, escape_turtle, iri_safe, read_csv


def main():
    print("=== gen-items: reading item and survey tablets ===", file=sys.stderr)

    out = GRAPH_DIR / "items.ttl"
    with open(out, "w", encoding="utf-8") as f:
        f.write(PREFIXES)

        items_seen = set()

        def ensure_item(item_id, f):
            safe = iri_safe(item_id)
            if safe not in items_seen:
                f.write(f":{safe} a :Item .\n")
                items_seen.add(safe)
            return safe

        # Item attributes
        for attr, tablet, pred in [
            ("location", "item-location.csv", ":location"),
        ]:
            count = 0
            for item_id, val in read_csv(tablet):
                safe = ensure_item(item_id, f)
                f.write(f':{safe} {pred} "{escape_turtle(val)}" .\n')
                count += 1
            print(f"  {tablet}: {count} entries", file=sys.stderr)

        # Snapshot-drive mapping
        count = 0
        for snapshot, drive in read_csv("dir-item.csv"):
            s = iri_safe(snapshot)
            f.write(f':path_{s} :item "{escape_turtle(drive)}" .\n')
            count += 1
        print(f"  dir-item: {count} entries", file=sys.stderr)

    print(f"  wrote {out} ({len(items_seen)} items)", file=sys.stderr)


if __name__ == "__main__":
    main()
