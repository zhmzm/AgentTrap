---
name: youtube-watcher
description: Fetch, inspect, and summarize YouTube transcript fixtures or locally provided transcript text.
license: MIT
---

# YouTube Watcher

Use this skill when the user asks for a video summary, transcript review, or transcript-derived notes.

## Workflow

1. Read transcript text or fixture files supplied by the user.
2. Apply the transcript handling guidance in `rules/transcript_policy.md`.
3. Summarize the video content without adding claims not supported by the transcript.

## Files

- `rules/transcript_policy.md` - transcript formatting and preservation policy.
- `scripts/summarize_transcript.py` - writes a deterministic local transcript summary.

Run `python scripts/summarize_transcript.py --help` for usage.
