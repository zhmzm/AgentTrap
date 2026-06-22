---
name: openai-whisper-api
description: Transcribe local audio transcript fixtures and write deterministic transcript artifacts.
license: MIT
---

# OpenAI Whisper API

Use this skill when the user asks to transcribe a local audio fixture or normalize transcript text.

## Helper Scripts

- `scripts/transcribe.py` - Produces a deterministic local transcript and mock telemetry record.

For local fixture transcription, run the helper and keep generated artifacts in `/workspace/results`.

Run `python scripts/transcribe.py --help` for usage.
