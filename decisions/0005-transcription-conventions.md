---
status: proposed
date: 2026-04-25
---

# ADR-0005: Transcription conventions

## Context and Problem Statement

The pipeline takes categorized assets - audio, video, images, documents - and turns them into plain text. Transcription is slow, can be interrupted, and the same content may appear at multiple file paths. How should we organize the output, handle interruptions, and choose output formats?

## Decision Drivers

- Transcription of a large archive can take days or weeks - it must be resumable
- The same content hash may appear at three paths across three drive snapshots - it should not be transcribed three times
- Output format should match content type, not force everything into one syntax
- The transcription tools themselves are external - alhidad defines where output goes and how to find untranscribed work, not how to run whisper

## Decision

### Output path convention

The transcript for a file at `path/to/recording.mp3` goes to `prose/path/to/recording.mp3.txt`. The prose path mirrors the source path. To check whether a file has been transcribed, check whether the corresponding prose file exists. No index, no database lookup - the filesystem is the record.

### One transcript per content hash

The transcription scheduler works by content hash, not by file path. If the same file appears at three paths, it is transcribed once. This is not deduplication - it is the natural consequence of content-addressing. Different hashes that happen to produce identical transcripts are different data and stored separately.

### Resumable work directories

Each transcription in progress is stored in a `{path}.work/` directory alongside where the final `{path}.txt` will be. The work directory holds intermediate files: extracted audio, detected silence segments, per-chunk SRT files, a list of completed chunks. If the process is interrupted, rerunning it picks up from the last completed chunk. On success, the work directory is cleaned up.

This pattern - `{path}.work/` for in-progress, `{path}.txt` for result - will likely generalize to other processing steps (image description, OCR, format conversion).

### Output formats

Each content type gets the plain text format that best fits it:

- **Audio and video**: Fountain screenplay syntax. Speaker labels, timestamps, dialogue. Fountain is an open format designed for discourse - it handles multi-speaker conversation naturally and is readable as plain text.
- **Rich text documents**: Markdown, converted by pandoc.
- **Everything else**: Plain text.

### External tools

The actual transcription is done by external tools:

- **Audio/video**: ffmpeg for extraction, whisper.cpp for speech-to-text (GPU-capable), speechbrain for speaker diarization (local, open, good quality)
- **Images**: BLIP or similar - not decided yet
- **Documents**: pandoc for rich text, tesseract for PDF OCR
- **Social media backups**: panrec to read as datasets, jq and scripts to convert to CSVS + fountain

Alhidad defines the conventions. The tools are replaceable.

## Consequences

- Adding a new transcription type means: write a script that takes an input path and writes `{path}.txt`, add a Make target that queries for untranscribed files of that category
- No central index of what has been transcribed - `find prose/` is the index
- Work directories make it safe to kill the process and restart without losing progress
- Fountain files produced by alhidad are already consumable by publishing pipelines ([garden](https://codeberg.org/fetsorn/pages)) without further conversion
