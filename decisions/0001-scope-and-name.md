---
status: proposed
date: 2026-04-25
---

# ADR-0001: Project scope and name

## Context and Problem Statement

I have a personal pipeline that turns hard drives full of files into plain text - categorized, queryable, transcribed. It works, but the code lives tangled with my private data. I want to separate the method from the data so that someone else could use it for their own files without inheriting my schema, my paths, or my life.

The question is: what exactly gets carried out, and what stays behind?

## Decision Drivers

- The method should be useful to someone who has never seen my data
- Tools that already do one job well (transcription, format conversion, filesystem ingestion) should not be reimplemented
- The project should teach a heuristic, not impose a workflow - someone might use only part of it

## Considered Options

### Option 1: Ship a complete application

Bundle transcription, ingestion, CSVS tooling, TTL generation, and query into one monolithic tool. The user installs it and it handles everything.

Rejected because every attempt to make transcription self-contained ends up reproducing the inventory system. And bundling whisper, speechbrain, pandoc, BLIP into one project means maintaining dependencies that have nothing to do with the core problem.

### Option 2: Ship only documentation

Write up the method and let people build their own pipelines from scratch.

Rejected because the glue is the hard part. Knowing that you should use CSVS and TTL together is not enough - you need the Makefile targets, the SPARQL queries, the schema conventions. Without them you are starting from zero.

### Option 3: Ship the orchestration layer - chosen

Carry out the Makefile, schema conventions, SPARQL queries, and just enough glue to connect independent tools. The heavy lifting - transcription (whisper, speechbrain), format conversion (pandoc, jq), filesystem ingestion (panrec) - stays in external dependencies. Alhidad is the place where I wire things together and make sure as little wiring as possible is needed.

## Decision

Alhidad is an orchestration layer. It ships:

- A Makefile that connects independent pipeline steps
- CSVS schema conventions (what tablets to create, how to name them)
- SPARQL queries for materialization and work queues
- Conventions for output paths and resumable processing

It does not ship:

- Transcription engines (whisper.cpp, speechbrain, BLIP, tesseract)
- Format converters (pandoc, jq)
- The CSVS library or panrec (these are separate projects)
- A publishing pipeline (garden depends on fountain, which can be authored by hand)

A user who clones alhidad and runs `make` with a variable pointing to a hard drive gets scaffolded csvs/, graph/, and prose/ directories. It starts transcribing audio files it finds and tells you: if you want this to go faster, assign categories to your folders so there is less to search through.

### The name

Alhidad is the sighting component of a theodolite - the instrument used in surveying to take a bearing on a point in the landscape. The earth science metaphor runs through the whole project: the pipeline is a survey of terrain, each layer a different scale of description. Alhidad is the tool that takes the measurement.

| Project | Discipline | Data it creates                          | Data it references     |
|---------|------------|------------------------------------------|------------------------|
| archive | sediment   | files on hard drives, items in wardrobes | real world             |
| estate  | topology   | hashes, paths, categories                | real world + files     |
| scribe  | geography  | entities, referents, transcripts         | files + categories     |
| garden  | ecology    | navigable hypertext landscape            | entities + transcripts |

```
real world ⊃ archive (hard drives) ⊃ estate (categories) ⊃ scribe (plain text) ⊃ garden (public hypertext)
```

Each transition loses coverage:

- **real world → archive**: not all physical items have digital representations. The archive captures what was digitized - photos taken, audio recorded, documents scanned. The real world is the superset.
- **archive → estate**: not all files in the archive have structured annotations. csvs stores hashes, paths, categories, metadata. Files that haven't been categorized or annotated exist on the drives but not in the structured layer.
- **estate → scribe**: not all annotated assets have plain text renderings. Audio not yet transcribed, images not yet described, PDFs not yet OCR'd - they have entries in csvs but no corresponding file in prose/.
- **scribe → garden**: not all transcriptions are published as html.

Each layer is independently useful. A person with just the hard drives has the archive - browsable, copyable, complete. A person with just csvs can grep for files by hash, path, category. A person with just prose/ can read transcripts, search text, publish. Nothing depends downward. Losing an inner layer doesn't destroy the outer ones.

## Consequences

- Transcription code will mature and move to its own repository. What remains in alhidad is the convention that output goes at `{path}.txt` and the query that finds untranscribed files.
- CSVS-to-TTL conversion and filesystem-to-CSVS ingestion will be done by panrec. Until panrec reaches feature parity, alhidad carries provisional scripts.
- The project is a recipe, not a product. Someone can take the schema conventions and ignore the Makefile, or use the SPARQL queries with their own TTL, or skip transcription entirely and just organize their files.
