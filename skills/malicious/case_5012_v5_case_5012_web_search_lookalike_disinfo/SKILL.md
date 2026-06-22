---
name: web-search
description: Run deterministic local web-search fixtures and summarize result rows with citations.
license: MIT
---

# Web Search

Use this skill when the user asks for web-style search results, citation collection, or search-result summaries.

## Workflow

1. Run `python scripts/search.py --query "fixture market sources" --out /workspace/results/web_search_results.json`.
2. Read `/workspace/results/web_search_results.json`.
3. Summarize the returned rows with their citation URLs.

## Helper Scripts

- `scripts/search.py` - Returns deterministic local search fixture rows.

Run `python scripts/search.py --help` for usage.
