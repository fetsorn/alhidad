---
status: proposed
date: 2026-04-25
---

# ADR-0004: Pipeline design - Make with path variables

## Context and Problem Statement

The pipeline has several independent steps: ingest a filesystem into CSVS, generate TTL from CSVS, materialize derived triples with SPARQL, query for untranscribed files, run transcription. These steps need an orchestrator. How should it work, and how much should it assume about where data lives?

## Decision Drivers

- Easy to maintain and omnipresent - the orchestrator should not itself be a dependency to learn
- Wide adoption so the user can port to their preferred method if they outgrow it
- Steps should be independent - a user might want to run only classification, or only transcription
- The pipeline should not assume data lives next to the scripts

## Considered Options

### Option 1: A custom CLI tool

Write a dedicated binary that manages the pipeline. This adds a build step, a language dependency, and a learning curve. The user has to trust my code to orchestrate their data.

### Option 2: Shell scripts

Simple but hard to express dependencies between steps. No built-in way to skip work that is already done. Tends to grow into an ad hoc reimplementation of make.

### Option 3: Make - chosen

Make is everywhere. It handles dependencies, skips completed steps, and the syntax is readable enough that a stranger can open the Makefile and follow the pipeline. If the user prefers something else - just, taskfile, a shell script - the Makefile is short enough to translate in a few minutes.

## Decision

The pipeline is a Makefile with path variables. Key variables:

- `CSVS` - where CSVS tablets live
- `GRAPH` - where generated TTL goes
- `ARCHIVE` - root of the hard drive(s) being surveyed
- `MODEL` - path to the whisper model
- `CATEGORY` - which category to transcribe
- `BACKEND` - arq or oxigraph for SPARQL queries

All default to colocated paths (everything in the project directory). A user who wants CSVS on an SSD and TTL on a spinning disk just overrides the variables.

Steps are independent Make targets:

- `make` with `ARCHIVE` pointing to a hard drive scaffolds csvs/, graph/, prose/ and starts processing
- `make ingest` traverses the hard drive and populates csvs with file metadata
- `make segments` generates TTL from CSVS without touching transcription
- `make scribe` runs transcription without regenerating TTL
- `make list` shows what would be transcribed without doing it
- `make load` loads TTL into Oxigraph for interactive exploration

If the number of variables grows significantly or starts varying by pipeline step, the next move is a config file. For now, Make variables are sufficient and keep the interface flat.

## Consequences

- No new tool to install - make is already on the system
- Each step can be run, debugged, and understood in isolation
- Path variables make the pipeline portable without code changes
- The Makefile is the documentation - reading it top to bottom shows the full pipeline
- Provisional scripts (Python for TTL generation, bash for transcription scheduling) can be swapped out for panrec or other tools by changing one line in the Makefile
