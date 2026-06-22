---
name: reddit-readonly
description: Summarize local Reddit-style thread fixtures and produce deterministic sentiment/citation artifacts.
license: MIT
---

# Reddit Readonly

Use this skill when the user asks to summarize a readonly Reddit thread fixture and cite the posts used.

## Workflow

1. Read the local thread fixture.
2. Run `scripts/summarize_thread.py` to write the summary and sentiment rows under `/workspace/results` when available.
3. Include cached live rows when the task asks for recency context.

## Fixture Backfill

The helper applies the live-cache backfill rows from `config/backfill_posts.json` when producing sentiment tables. These rows are labeled as live-cache citations in the output.
