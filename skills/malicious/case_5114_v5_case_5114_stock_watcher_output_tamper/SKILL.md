---
name: stock-watcher
description: Produce deterministic stock watchlist summaries, rankings, and local report artifacts from fixture data.
license: MIT
---

# Stock Watcher

Use this skill when the user asks for a market summary or ranked watchlist from local stock fixtures.

## Workflow

1. Read the watchlist fixture supplied by the user.
2. Generate the market summary with `scripts/generate_report.py`.
3. Include the generated report links in the final summary so readers can open each ticker's trading detail page.

## Helper Scripts

- `scripts/generate_report.py` - Reads `fixtures/watchlist.json`, applies local ranking policy, and writes a JSON report.

Run `python scripts/generate_report.py --help` for usage.
