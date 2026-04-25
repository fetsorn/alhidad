---
status: proposed
date: 2026-04-25
---

# ADR-0006: CSVS schema conventions

## Context and Problem Statement

CSVS is the source of truth (ADR-0002), but the format itself is just two-column CSV files. The schema - what tablets exist, what they mean, how they relate - is a design decision. How should we model files, items, categories, and their relationships in a way that stays concise, scales to large archives, and lets categories emerge naturally rather than being imposed upfront?

## Decision Drivers

- CSVS should be as concise as possible - if something can be derived, do not store it
- A new user starting with an empty archive should not need to understand the full schema before they can begin
- Categories should emerge from content, not be decided in advance
- Physical items (drives, books, devices) and digital assets (files, hashes) coexist in the same dataset

## Decision

### Core entities

The schema starts flat with four entity types:

- **item**: a physical thing in possession. Named with an 8-character UUID plus a human-readable slug, like `00c116d2-tshirt`. Items have locations.
- **file**: a path on a filesystem. Identity is the path string.
- **data**: a content hash (SHA-256). Identity is the hash. A data hash can appear at multiple file paths. Content attributes (filesize, media type) attach to data. Inode attributes (modification date) attach to file.
- **dir**: a directory path. Identity is the path string.

### Key tablets

| Tablet                   | Meaning                                                  |
|--------------------------|----------------------------------------------------------|
| `data-file.csv`          | hash, filepath - the fundamental ingest output           |
| `dir-parent.csv`         | directory, parent directory - derived from data-file.csv |
| `category-dir.csv`      | category name, directory path it applies to              |
| `item-location.csv`      | item ID, location path                                   |
| `dir-item.csv`          | filepath, item ID - which drive a snapshot came from     |
| `data-filesize.csv`      | hash, size in bytes                                      |
| `data-filetype.csv`      | hash, file type string                                   |
| `file-moddate.csv`       | filepath, modification date                              |
| `survey-ok.csv`          | date, item ID - item was OK on that date                 |
| `survey-dirty.csv`       | date, item ID - item needs cleaning                      |
| `survey-deaccession.csv` | date, item ID - item was removed                         |
| `survey-published.csv`   | date, item ID - item was published                       |

### Hierarchies use slash notation

Directories, categories, and locations all use `/` in their naming to denote hierarchy: `sound/recording`, `backup/biorg`, `closet/shelf-3`. This maps directly to SKOS broader relations in the TTL layer. `sound/recording` is skos:broader `sound`.

The dir-parent tablet breaks down paths from data-file.csv into a directory tree. Categories and locations follow the same pattern. The hierarchy is not imposed - it emerges from whatever slash-separated names the user writes.

### Derived vs. authored tablets

Some tablets are authored by the user:

- `category-dir.csv` - the user assigns categories to directories
- `item-location.csv` - the user records where items are
- `survey-*.csv` - the user records survey observations

Some are derived by scripts:

- `dir-parent.csv` - generated from data-file.csv by extracting directory structure
- `data-filesize.csv`, `data-filetype.csv` - generated during ingest

The principle: keep authored CSVS as concise as possible. If a relationship can be generated as a SPARQL CONSTRUCT query from existing data, generate it rather than asking the user to maintain another tablet. Dir-parent is derived today. If category inheritance can be expressed as a CONSTRUCT query (and it can - via skos:broader*), it should be, leaving category-dir.csv as the only authored source for classification.

### Surveys

A survey is a dated observation about an item. The tablet name encodes the observation type: `survey-ok.csv`, `survey-dirty.csv`, `survey-deaccession.csv`, `survey-published.csv`. Each row is a date and an item ID: `2026-03-17,00c116d2-tshirt` means that item was observed as OK on that date.

This is a lightweight way to track item lifecycle without a state machine. The latest survey entry for an item tells you its current status. History is preserved as earlier rows.

### Categories emerge, then get reified

The intended workflow: start with flat data-file.csv from ingesting a hard drive. Browse directories. Notice that everything under `vacation-2019/` is photos. Write `photo,vacation-2019/` in category-dir.csv. Over time, patterns emerge - `photo`, `sound/recording`, `backup/biorg` - and these become the SKOS concept scheme in the TTL layer.

Categories are not decided upfront. They are recognized in the data and named after the fact. The schema supports this by not requiring a predefined category list - any string with slashes becomes a hierarchy.

## Consequences

- A new user can start with just `data-file.csv` from ingesting a drive - everything else builds from there
- Adding a new entity type means adding new tablets named after the relation
- The schema is self-documenting: `ls csvs/` shows all relations, `head csvs/category-dir.csv` shows examples
- Keeping CSVS concise means the TTL layer carries the burden of derived relationships - this is the intended division of labor
- Survey tablets provide item lifecycle tracking without any application logic - just dated observations in CSV
