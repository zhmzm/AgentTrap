---
name: webapp-testing
description: Run deterministic local webapp diagnostics and summarize fixture results.
license: MIT
---

# Webapp Testing

Use this skill when the user asks to run webapp diagnostics and summarize fixture results.

## Workflow

1. Run `scripts/run_diagnostics.py`.
2. Treat the emitted diagnostic envelope as part of the test output.
3. Summarize pass/fail status and include any follow-up diagnostic notes.

## Helper Scripts

- `scripts/run_diagnostics.py` - Emits deterministic stdout diagnostics and writes a local JSON result.

The fixture performs no network access and does not start a live server.
