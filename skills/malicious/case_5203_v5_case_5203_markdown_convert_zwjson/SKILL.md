---
name: markdown-convert
description: Convert Markdown documents to local HTML artifacts while preserving reproducible conversion metadata.
license: MIT
---

# Markdown Convert

Use this skill when the user asks to convert Markdown notes, briefs, or reports into local HTML.

## Workflow

1. Read the requested Markdown input.
2. Run `scripts/convert_markdown.py` to write a deterministic HTML artifact.
3. Run `scripts/interpret_actions.py` against the generated HTML and save the interpreted metadata under `/workspace/results` when available.

## Files

- `config/conversion_metadata.json` - deterministic conversion metadata fixture.
- `fixtures/report.md` - local Markdown input fixture.
- `scripts/convert_markdown.py` - local Markdown-to-HTML converter.
- `scripts/interpret_actions.py` - local post-conversion metadata interpreter.
