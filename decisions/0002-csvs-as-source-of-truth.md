---
status: proposed
date: 2026-04-25
---

# ADR-0002: CSVS as source of truth

## Context and Problem Statement

The pipeline needs a database for metadata - file hashes, paths, categories, item inventories, survey records. The database must be the source of truth that everything else is derived from. What format should it use?

## Decision Drivers

- A layperson should be able to find the file on their computer, open it in a text editor, and understand what they are looking at
- It must handle millions of entries without special tooling
- It must be durable - no binary format that can corrupt silently or require a specific program to open
- Grep should work as a query tool. Bash should work for appending records. Emacs should work for editing.
- Complex queries (joins, transitivity, set algebra) are out of scope for this layer - a separate query layer handles those

## Considered Options

### Option 1: SQLite

Binary format. Easy to corrupt. A layperson does not know how to open it. Requires sqlite3 or a GUI tool to inspect. Powerful queries built in, but the source of truth becomes opaque.

### Option 2: TSV or YAML

TSV does not scale well to millions of entries across many relation types. YAML is verbose and fragile to whitespace errors. Neither encodes schema in a way that is self-describing without documentation.

### Option 3: TTL / RDF

Expressive and has a mature query ecosystem. But a gigabyte of RDF is not something a person can open and grok. Writing it by hand is error-prone. The source of truth would silently slip away from the user into cognitive difficulty. TTL is good as a derived view, not as the thing you edit.

### Option 4: CSVS (Comma-Separated Value Store) - chosen

Two-column CSV files where each file represents one relation. The filename encodes the schema: `data-file.csv` means "for each data hash, a file path." `category-dir.csv` means "for each category, a directory path it applies to." The format is specified at https://norcivilianlabs.org/csvs/specs/comma_separated_value_store.html.

A person can open any tablet in a text editor and see rows of pairs. Grep queries it. Bash appends to it. The csvs-js and csvs-rs libraries stream tablets for programmatic access at reasonable speed even at millions of rows - something TTL engines typically achieve only by loading into RocksDB or memory.

## Decision

CSVS is the source of truth for all structured metadata. Every other representation - TTL, SPARQL results, materialized views - is derived from CSVS and can be regenerated.

The tradeoff is explicit: CSVS does not support complex queries. The moment you need joins, transitivity, or anything beyond "give me all rows where column A equals X," you convert to TTL and use SPARQL. This is by design. Pushing query efficiency into CSVS would dilute its value proposition of being concise and transparent.

I authored CSVS. It has low adoption. But that is part of the point - the source of truth must remain something the user can fully understand and control. If the format is simple enough that you could reimplement the parser in an afternoon, you are never locked in.

## Consequences

- All pipeline steps that modify structured data write to CSVS tablets, not to TTL or any other format
- TTL is regenerated from CSVS on each build - it is a cache, not an authority
- Schema changes are visible in csvs/_-_.csv and as new files appearing in the csvs/ directory, named after the relation they encode
- A user who loses everything except the csvs/ directory can reconstruct the full pipeline state
- panrec already converts between CSVS, JSON, and other formats - alhidad leans on this for interop
