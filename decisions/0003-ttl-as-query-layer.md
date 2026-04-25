---
status: proposed
date: 2026-04-25
---

# ADR-0003: TTL as query layer

## Context and Problem Statement

CSVS handles storage and retrieval well, but the pipeline needs queries that CSVS cannot express: "find all files under any subcategory of sound," "which directories have no category assigned," "list assets that appear at multiple paths." These require joins, transitive closure, and set operations. How do we get them without complicating the source of truth?

## Decision Drivers

- CSVS must stay concise and optimized for writing - it should not grow features to accommodate query efficiency
- The query layer must work offline
- SPARQL 1.1 is the most expressive graph query language with a mature ecosystem
- The conversion cost must be low enough that regenerating on every build is acceptable

## Considered Options

### Option 1: Add query features to CSVS

CSVS already has a query syntax - `{ _: file, filepath: 2024 }` amounts to `SELECT * FROM file WHERE filepath = 2024`. This covers retrieval. But extending it to handle joins and transitivity would mean reinventing SPARQL with postprocessing of JSON results. That is a lot of work to end up with something worse than what already exists.

### Option 2: Use a purpose-built index

Build a custom query engine over CSVS tablets - maybe an inverted index, maybe SQLite as a query cache. This adds a binary dependency and a new codebase to maintain, for a problem that TTL+SPARQL already solves.

### Option 3: Convert CSVS to TTL, query with SPARQL - chosen

Map each CSVS tablet to TTL triples. Query with SPARQL using existing engines. Both CSVS and TTL are plain text triple stores at heart - the conversion is straightforward and fast. The TTL is a materialized view, regenerated from CSVS on each build.

## Decision

TTL is the query layer. It is derived from CSVS, never hand-edited, and can be deleted and rebuilt at any time.

The pipeline generates TTL in segments (directories.ttl, categories.ttl, files.ttl, assets.ttl, items.ttl) for debugging, then concatenates them into one file for queries. SPARQL CONSTRUCT queries produce additional materialized triples - for example, propagating category assignments down the directory hierarchy via skos:broader*.

Two query backends are supported:

- **Apache Jena ARQ**: runs offline via nix-shell, supports full SPARQL 1.1. A bit heavy to set up but works reliably.
- **Oxigraph + Trifid**: loads TTL into a local store with a web UI for interactive graph exploration. Useful for finding uncategorized directories, browsing the category tree, checking classification coverage.

Both engines load TTL into memory or RocksDB internally - the conversion from plain text to an indexed store is an accepted step in the TTL ecosystem, not something alhidad invented.

TTL is also useful for schema annotation. Categories are already SKOS concepts. The graph can express validation constraints and relationships that would be awkward in CSVS. But TTL is still not worth writing by hand - it is generated, queried, explored, and thrown away.

## Consequences

- CSVS stays concise: if a derived relationship (like dir-parent) can be expressed as a SPARQL CONSTRUCT query, it should be, rather than adding a new tablet that the user must maintain
- Any query need is closed by SPARQL - no ceiling on what can be asked of the data
- The TTL layer is disposable - deleting graph/ and running `make` regenerates it
- Debugging is possible at the segment level: if categories.ttl looks wrong, check category-dir.csv
- Future: once panrec supports CSVS-to-TTL conversion natively, the Python generation scripts can be replaced
