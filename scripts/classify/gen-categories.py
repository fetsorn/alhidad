#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0
"""Generate graph/categories.ttl from category-dir.csv.

Builds the SKOS concept hierarchy from category names.
Category names use / as hierarchy separator (e.g. "backup/biorg").
"""

import sys
from lib import GRAPH_DIR, PREFIXES, escape_turtle, iri_safe, read_csv


def main():
    print("=== gen-categories: reading category-dir.csv ===", file=sys.stderr)
    categories = set()
    for cat, _path in read_csv("category-dir.csv"):
        categories.add(cat)
    print(f"  {len(categories)} unique categories", file=sys.stderr)

    # Build hierarchy: split each category on / to get parent chain
    all_nodes = set()
    node_parent = {}
    for cat in categories:
        parts = cat.split("/")
        for i in range(1, len(parts) + 1):
            node = "/".join(parts[:i])
            all_nodes.add(node)
            if i > 1:
                node_parent[node] = "/".join(parts[:i - 1])

    out = GRAPH_DIR / "categories.ttl"
    with open(out, "w", encoding="utf-8") as f:
        f.write(PREFIXES)
        for node in sorted(all_nodes):
            safe = iri_safe(node)
            f.write(f'<urn:alhidad:cat/{safe}> a skos:Concept ; skos:prefLabel "{escape_turtle(node)}"')
            if node in node_parent:
                parent_safe = iri_safe(node_parent[node])
                f.write(f" ; skos:broader <urn:alhidad:cat/{parent_safe}>")
            f.write(" .\n")

    print(f"  wrote {out} ({len(all_nodes)} concepts)", file=sys.stderr)


if __name__ == "__main__":
    main()
