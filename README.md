<div align="center">

part of the [ontonomy](https://norcivilianlabs.org) software suite

AGPL-3.0. Anton Davydov.

</div>

# alhidad

Turns a hard drive into plain text you can search, query, and read.

You point it at a drive full of files. It builds a metadata dataset in [CSVS](https://norcivilianlabs.org/csvs/specs/comma_separated_value_store.html) - plain text, two-column CSV files you can open in any editor. It converts that dataset to [TTL](https://www.w3.org/TR/turtle/) so you can query it with SPARQL. Then it finds audio and video files and transcribes them into [Fountain](https://fountain.io/) screenplays - speaker labels, timestamps, plain text.

The name comes from the alhidad of a theodolite - the sighting instrument used in land surveying. The project treats your files as terrain to be mapped: first you record what exists, then you classify it, then you render it legible.

## How it works

The pipeline has four steps. Each one narrows the previous:

1. **Ingest** - run `sha256sum` on a drive, feed the listing to alhidad. It produces `data-file.csv`: one row per file, hash and path.
2. **Classify** - assign categories to directories by editing `category-dir.csv`. Alhidad generates TTL with SKOS concept hierarchies and materializes category inheritance with SPARQL CONSTRUCT queries.
3. **Transcribe** - alhidad queries the graph for files in a given category, checks which ones already have a transcript, and runs whisper.cpp + speechbrain on the rest. Output goes to `prose/` mirroring the source path.
4. **Explore** - load the TTL into Oxigraph and browse with Trifid. Find uncategorized directories, check coverage, refine.

Each step is independent. You can classify without transcribing, or transcribe without exploring. You can use only the CSVS dataset and ignore TTL entirely.

## Quick start

```sh
git clone https://codeberg.org/norcivilianlabs/alhidad
cd alhidad

# Point CSVS at your data directory, or let it default to csvs/
# Ingest files into CSVS:
make CSVS=/path/to/csvs ARCHIVE=/path/to/drive ingest 

# Generate TTL from CSVS:
make CSVS=/path/to/csvs GRAPH=graph segments

# See what would be transcribed:
make CSVS=/path/to/csvs GRAPH=graph ARCHIVE=/path/to/drive CATEGORY=sound/recording list

# Transcribe:
make CSVS=/path/to/csvs GRAPH=graph ARCHIVE=/path/to/drive PROSE=prose CATEGORY=sound/recording scribe
```

If all your data is colocated (csvs/, graph/, prose/ in the project directory), you can just run `make` and override only what differs.

## Make targets

| Target          | What it does                                       |
|-----------------|----------------------------------------------------|
| `make ingest`   | Read filesystem and populate CSVS                  |
| `make`          | Generate all TTL from CSVS                         |
| `make segments` | Generate TTL segment files without concatenating   |
| `make scribe`   | Transcribe untranscribed files in CATEGORY         |
| `make list`     | Show what would be transcribed                     |
| `make load`     | Load TTL into Oxigraph for interactive exploration |
| `make clean`    | Remove generated TTL and derived CSVS              |

## Variables

| Variable   | Default                                        | Meaning                             |
|------------|------------------------------------------------|-------------------------------------|
| `CSVS`     | `csvs`                                         | Directory containing CSVS tablets   |
| `GRAPH`    | `graph`                                        | Directory for generated TTL         |
| `PROSE`    | `prose`                                        | Directory for transcripts           |
| `ARCHIVE`  | `archive`                                      | Root of the drive(s) being surveyed |
| `MODEL`    | `~/whisper.cpp/models/ggml-large-v3-turbo.bin` | Whisper model path                  |
| `CATEGORY` | `sound/recording`                              | Category to transcribe              |
| `LIMIT`    | `1`                                            | Max files to transcribe per run     |
| `BACKEND`  | `arq`                                          | SPARQL backend: `arq` or `oxi`      |

## CSVS schema

The dataset is a set of two-column CSV files. The filename tells you the relation. Core tablets:

| Tablet              | Meaning                               |
|---------------------|---------------------------------------|
| `data-file.csv`     | content hash, file path               |
| `dir-parent.csv`    | directory, parent directory (derived) |
| `category-dir.csv`  | category name, directory path         |
| `item-location.csv` | item ID, location                     |
| `path-item.csv`     | file path, item ID                    |
| `survey-ok.csv`     | date, item ID                         |

Items use 8-character UUIDs with a human slug: `00c116d2-tshirt`. Categories and locations use `/` for hierarchy: `sound/recording`, `closet/shelf-3`. These map to SKOS broader relations in TTL.

You author `category-dir.csv` and `item-location.csv`. Everything else is derived or ingested. See [ADR-0006](decisions/0006-schema-conventions.md) for the full schema.

## Transcription conventions

Transcripts go to `prose/{path}.txt`, mirroring the source file path. In-progress work lives in `prose/{path}.work/` and resumes on interruption. One transcript per content hash - if the same file appears at three paths, it is transcribed once.

Audio and video become Fountain screenplay syntax with speaker diarization. Rich text becomes Markdown via pandoc. Everything else becomes plain text.

## Dependencies

Alhidad orchestrates existing tools. You need some subset of:

- **make** - pipeline orchestration
- **python3** - CSVS-to-TTL generation scripts (provisional, to be replaced by panrec)
- **[Apache Jena ARQ](https://jena.apache.org/)** - offline SPARQL queries (available with [Nix](https://nixos.org/) via `nix-shell -p apache-jena`)
- **[whisper.cpp](https://github.com/ggerganov/whisper.cpp)** - speech-to-text (GPU-capable)
- **[speechbrain](https://speechbrain.readthedocs.io/)** - speaker diarization
- **ffmpeg** - audio extraction
- **[Oxigraph](https://github.com/oxigraph/oxigraph)** + **[Trifid](https://github.com/zazuko/trifid)** - interactive graph exploration (optional)

## Design decisions

The reasoning behind each design choice is documented as [MADRs](https://adr.github.io/madr/) in `decisions/`:

- [ADR-0001: Project scope and name](decisions/0001-scope-and-name.md) - alhidad is an orchestration layer that teaches a heuristic
- [ADR-0002: CSVS as source of truth](decisions/0002-csvs-as-source-of-truth.md) - why plain text two-column CSV, not SQLite or TTL
- [ADR-0003: TTL as query layer](decisions/0003-ttl-as-query-layer.md) - TTL as a disposable materialized view
- [ADR-0004: Pipeline design](decisions/0004-pipeline-design.md) - Make with path variables, independent steps
- [ADR-0005: Transcription conventions](decisions/0005-transcription-conventions.md) - output paths, resumable work, format choices
- [ADR-0006: Schema conventions](decisions/0006-schema-conventions.md) - entity types, tablet naming, emergent categories

## Status

Early and opinionated. The Python scripts are provisional - CSVS-to-TTL conversion and filesystem ingestion will eventually be handled by [panrec](https://codeberg.org/norcivilianlabs/panrec). Transcription scripts will mature into an independent tool. What remains in alhidad is the Makefile, the schema conventions, the SPARQL queries, and the documentation of why things are the way they are.

## Source

- Codeberg: [norcivilianlabs/alhidad](https://codeberg.org/norcivilianlabs/alhidad)
- GitHub: [fetsorn/alhidad](https://github.com/fetsorn/alhidad)
