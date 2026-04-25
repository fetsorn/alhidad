#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0
"""Generate graph/files.ttl from data-file.csv and file-* tablets.

One :File node per path. Path-based identity (hashed).
Attributes of the path: directory, sha256, moddate, item.
"""

import sys
from lib import GRAPH_DIR, PREFIXES, dir_iri, path_hash, escape_turtle, read_csv


def main():
    print("=== gen-files: reading data-file.csv ===", file=sys.stderr)
    # (hash, path) pairs
    entries = []
    count = 0
    for h, p in read_csv("data-file.csv"):
        entries.append((h, p))
        count += 1
        if count % 100000 == 0:
            print(f"  {count} path entries...", file=sys.stderr)
    print(f"  {count} paths", file=sys.stderr)

    # Path-keyed metadata
    print("  reading file-* tablets...", file=sys.stderr)
    path_moddate = dict(read_csv("file-moddate.csv"))
    print(f"  moddates: {len(path_moddate)}", file=sys.stderr)

    # Write TTL
    out = GRAPH_DIR / "files.ttl"
    print(f"  writing {out}...", file=sys.stderr)
    emitted = 0
    with open(out, "w", encoding="utf-8") as f:
        f.write(PREFIXES)
        for h, p in entries:
            file_iri = f"<urn:alhidad:file/{path_hash(p)}>"
            f.write(f"{file_iri} a :File")
            f.write(f' ;\n  :path "{escape_turtle(p)}"')
            f.write(f" ;\n  :sha256 <urn:sha256:{h}>")

            # Leaf directory
            parts = p.split("/")
            if len(parts) > 1:
                leaf = "/".join(parts[:-1])
                f.write(f" ;\n  :directory {dir_iri(leaf)}")

            # rdfs:label - filename
            f.write(f' ;\n  rdfs:label "{escape_turtle(parts[-1])}"')

            if p in path_moddate:
                f.write(f' ;\n  :moddate "{escape_turtle(path_moddate[p])}"')

            f.write(" .\n")
            emitted += 1
            if emitted % 100000 == 0:
                print(f"  {emitted}/{count} files...", file=sys.stderr)

    print(f"  wrote {out} ({emitted} files)", file=sys.stderr)


if __name__ == "__main__":
    main()
