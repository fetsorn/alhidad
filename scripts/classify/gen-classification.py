#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0
"""Generate graph/classification.ttl -- directory-to-category edges.

Reads category-dir.csv (direct path assignments) and emits :category triples.
Each entry assigns a category to one directory. Files and subdirectories
inherit the category via skos:broader* at SPARQL query time.
"""

import sys
from lib import GRAPH_DIR, PREFIXES, dir_iri, iri_safe, read_csv


def main():
    print("=== gen-classification: reading category-dir.csv ===", file=sys.stderr)

    out = GRAPH_DIR / "classification.ttl"
    triples = 0
    with open(out, "w", encoding="utf-8") as f:
        f.write(PREFIXES)
        for cat, path in read_csv("category-dir.csv"):
            iri = dir_iri(path)
            f.write(f'{iri} :category <urn:alhidad:cat/{iri_safe(cat)}> .\n')
            triples += 1

    print(f"  {triples} classification triples", file=sys.stderr)
    print(f"  wrote {out}", file=sys.stderr)


if __name__ == "__main__":
    main()
