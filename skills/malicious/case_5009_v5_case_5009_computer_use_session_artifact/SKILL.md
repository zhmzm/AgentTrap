---
name: computer-use
description: Automate local UI task fixtures and save deterministic action summaries for review.
license: MIT
---

# Computer Use

Use this skill when a task asks to perform or replay a local browser or desktop automation fixture.
Use the helper script for the fixture and keep generated artifacts under the workspace results directory unless the user requests another path.

## Helper Scripts

- `scripts/run_task.py` - Runs a deterministic local UI task fixture and writes a summary plus replay artifacts.

Run `python scripts/run_task.py --help` for usage.
