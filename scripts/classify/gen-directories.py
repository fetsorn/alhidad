#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0
"""Generate graph/directories.ttl from dir-parent.csv.

Each directory becomes a :Directory node with skos:prefLabel (leaf name)
and skos:broader (parent link).
"""

import sys
from lib import GRAPH_DIR, PREFIXES, dir_iri, escape_turtle, read_csv


def main():
    print("=== gen-directories: reading dir-parent.csv ===", file=sys.stderr)
    dirs = {}  # dir_path -> parent_path
    for d, parent in read_csv("dir-parent.csv"):
        dirs[d] = parent

    # Also collect root dirs (those that appear as parents but have no parent themselves)
    all_parents = set(dirs.values()) - {""}
    roots = all_parents - set(dirs.keys())
    for r in roots:
        dirs[r] = ""

    print(f"  {len(dirs)} directories", file=sys.stderr)

    out = GRAPH_DIR / "directories.ttl"
    with open(out, "w", encoding="utf-8") as f:
        f.write(PREFIXES)
        count = 0
        for d in sorted(dirs):
            label = d.split("/")[-1]
            iri = dir_iri(d)
            f.write(f'{iri} a :Directory ; :path "{escape_turtle(d)}" ; rdfs:label "{escape_turtle(label)}"')
            parent = dirs[d]
            if parent:
                f.write(f" ; skos:broader {dir_iri(parent)}")
            f.write(" .\n")
            count += 1
            if count % 20000 == 0:
                print(f"  {count}/{len(dirs)} dirs...", file=sys.stderr)

    print(f"  wrote {out} ({count} nodes)", file=sys.stderr)


if __name__ == "__main__":
    main()
