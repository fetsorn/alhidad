#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0
"""Load all segment TTL files into Oxigraph."""

import os
import sys
from pathlib import Path

import requests

GRAPH_DIR = Path(os.environ.get("GRAPH", "graph"))
OXI_STORE = "http://localhost:7878/store?default"
OXI_UPDATE = "http://localhost:7878/update"
OXI_QUERY = "http://localhost:7878/query"

SEGMENTS = [
    "directories.ttl",
    "categories.ttl",
    "classification.ttl",
    "files.ttl",
    "assets.ttl",
    "items.ttl",
    "inferred.ttl",
]


def main():
    if "--no-clear" not in sys.argv:
        print("=== Clearing Oxigraph ===", file=sys.stderr)
        resp = requests.post(
            OXI_UPDATE,
            headers={"Content-Type": "application/sparql-update"},
            data="CLEAR ALL",
        )
        print(f"  clear: {resp.status_code}", file=sys.stderr)

    for seg in SEGMENTS:
        path = GRAPH_DIR / seg
        if not path.exists():
            print(f"  SKIP {seg} (not found)", file=sys.stderr)
            continue
        size_mb = path.stat().st_size / (1024 * 1024)
        print(f"=== Loading {seg} ({size_mb:.1f} MB) ===", file=sys.stderr)
        with open(path, "rb") as f:
            resp = requests.post(
                OXI_STORE,
                headers={"Content-Type": "text/turtle"},
                data=f,
            )
        if resp.status_code >= 400:
            print(f"  ERROR {resp.status_code}: {resp.text[:500]}", file=sys.stderr)
            sys.exit(1)
        print(f"  loaded: {resp.status_code}", file=sys.stderr)

    # Stats
    resp = requests.post(
        OXI_QUERY,
        headers={
            "Content-Type": "application/sparql-query",
            "Accept": "text/tab-separated-values",
        },
        data="""PREFIX : <urn:alhidad:>
SELECT
  (COUNT(DISTINCT ?d) AS ?dirs)
  (COUNT(DISTINCT ?cd) AS ?classified_dirs)
  (COUNT(DISTINCT ?a) AS ?assets)
WHERE {
  { ?d a :Directory } UNION
  { ?cd a :Directory ; :category ?c } UNION
  { ?a a :Data }
}""",
    )
    print(f"\n=== Done ===", file=sys.stderr)
    print(f"Stats: {resp.text.strip()}", file=sys.stderr)


if __name__ == "__main__":
    main()
