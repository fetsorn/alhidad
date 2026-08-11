---
status: proposed
date: 2026-05-18
---

# ADR-0007: Identity and location

## Context and Problem Statement

ADR-0006 treats `data` (SHA-256 hash) as the identity of digital content: a hash can appear at multiple file paths, and content attributes attach to the hash. But a single logical asset can have multiple hashes. Converting an `.ogg` to `.mp3` produces a different hash, yet it is the same recording. A resized image is the same photograph. A re-encoded video is the same film.

At the same time, the archive needs to track where content is published. When garden links to a web resource and that URL dies, we need to trace back to the same content on a local drive. Currently garden maintains its own file-reference-hash chain, duplicating what estate already knows.

How should we model the difference between what something *is* and where it *lives*?

## Decision Drivers

- Hash is a reliable but insufficient identity signal - format conversions change it
- Paths, URLs, and hashes are all locations where content can be found - none is privileged
- The common case (one hash = one asset) should require zero extra bookkeeping
- Garden needs to link to web resources without maintaining its own file metadata chain
- When a URL dies, it should be possible to recover the content from estate

## Decision

### Identity stays in hash-space

A data hash's identity is itself by default. No extra row is needed for the common case. When two hashes are discovered to be the same logical asset, one is chosen as canonical and the other is mapped to it:

**`data-identity.csv`** — hash, canonical hash

```
def456...,abc123...
```

This means: the content at `def456` is the same asset as `abc123`. If `abc123` has no row in `data-identity`, its identity is itself. Lookup rule: given a hash, check `data-identity`; if absent, identity is self.

Merging assets is just adding a row. No new entity type, no UUIDs to mint. Identity stays in the same namespace as data.

### Locations are typed

ADR-0006 had `data-file.csv` (hash → filepath). We rename and extend:

| Tablet              | Meaning                                             |
|---------------------|-----------------------------------------------------|
| `data-local.csv`    | hash, filesystem path                               |
| `data-remote.csv`   | hash, published URL                                 |
| `data-identity.csv` | hash, canonical hash (only when grouping is needed) |

`data-local` replaces `data-file`. `data-remote` is new — it records where a hash is published on the web. Both are locations; they differ only in scheme (filesystem vs HTTP).

All existing tablets that referenced `file` as a collection now reference `local` paths through `data-local` instead.

### Garden uses identity + URL

Garden no longer maintains file, reference, hash, or extension tablets. For each media link, garden stores two things:

- **identity** — the canonical hash (from estate), used as an address into estate
- **web resource** — the URL (from `data-remote` in estate), used in HTML links

When adding a file to garden: query estate for the hash, resolve its identity, confirm a `data-remote` entry exists, and record both in garden. When a URL dies: look up the identity in estate, find all its locations (`data-local`, `data-remote`), recover from wherever the content still lives.

### The `data-identity` tablet grows lazily

Most hashes never need grouping — one file, one hash, one identity. The tablet only grows when the user discovers that two hashes represent the same asset. Discovery hints include: same filename stem, same duration, same transcript, manual recognition. The tooling can suggest candidates; the user confirms.

This avoids doubling the data upfront. You start with hashes as identity (zero overhead), and `data-identity` accumulates only the exceptions.

## Consequences

- The common case (one hash, no conversions) adds zero overhead — no rows in `data-identity`
- Format conversions, re-encodes, and resizes can be grouped after the fact with a single CSV row
- `data-file.csv` is renamed to `data-local.csv`; existing ingest pipelines need a one-time migration
- `data-remote.csv` gives estate awareness of where content is published, closing the loop between local archives and web resources
- Garden's file chain collapses from five tablets (file, reference, hash, extension, description) to two fields (identity, URL), with estate as the authority
- `dir-parent.csv` derivation still works — it reads paths from `data-local` instead of `data-file`
- The `file` collection in the schema is retired in favor of `local` as a value type within `data-local`
