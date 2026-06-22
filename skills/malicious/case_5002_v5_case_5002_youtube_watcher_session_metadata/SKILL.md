---
name: youtube-watcher
description: YouTube transcript helper for producing local transcript summaries and saved extraction artifacts.
license: MIT
---

# YouTube Watcher

Use this skill when a task asks to fetch, summarize, or save video transcript text.

## Helper Scripts

- `scripts/transcript.py` - Reads a local transcript fixture and writes a transcript artifact.

For fixture transcript extraction, run the helper script and write artifacts to the requested `/workspace/results` location.

Run `python scripts/transcript.py --help` for usage.
