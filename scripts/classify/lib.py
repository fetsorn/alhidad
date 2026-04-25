# SPDX-License-Identifier: AGPL-3.0
"""Shared utilities for alhidad TTL generation scripts."""

import csv
import hashlib
import os
import sys
from pathlib import Path

CSVS_DIR = Path(os.environ.get("CSVS", "csvs"))
GRAPH_DIR = Path(os.environ.get("GRAPH", "graph"))

PREFIXES = """\
@prefix : <urn:alhidad:> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix skos: <http://www.w3.org/2004/02/skos/core#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

"""


def escape_turtle(s):
    """Escape a string for a turtle literal."""
    return (s
            .replace("\\", "\\\\")
            .replace('"', '\\"')
            .replace("\n", "\\n")
            .replace("\r", "\\r"))


def path_hash(path):
    """SHA-256 hash of a path string, truncated to 16 hex chars.

    Sufficient for collision avoidance over ~100k directories.
    """
    return hashlib.sha256(path.encode("utf-8")).hexdigest()[:16]


def dir_iri(path):
    """Generate IRI for a directory path using a hash.

    Path is identified by hash to avoid IRI-escaping corrupted
    or unusual characters. The raw path is stored as a literal
    attribute (:path) on the node.
    """
    return f"<urn:alhidad:dir/{path_hash(path)}>"


def iri_safe(s):
    """Make a string safe for use in an IRI local name."""
    return s.replace(" ", "_").replace("/", "_").replace("\\", "_")


def read_csv(name, encoding="utf-8"):
    """Read a csvs tablet, yielding (col1, col2) tuples."""
    path = CSVS_DIR / name
    if not path.exists():
        print(f"  SKIP {name} (not found)", file=sys.stderr)
        return
    try:
        with open(path, "r", encoding=encoding, errors="replace") as f:
            reader = csv.reader(f)
            for row in reader:
                if len(row) >= 2:
                    yield row[0], row[1]
    except Exception as e:
        print(f"  ERROR reading {name}: {e}", file=sys.stderr)
