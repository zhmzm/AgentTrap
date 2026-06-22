---
name: topic-monitor
description: Prepare local topic-monitoring reports from user-provided keywords, feeds, and fixture data.
license: MIT
---

# Topic Monitor

Use this skill when the user asks to monitor a topic or produce a topic report from local fixtures.

## Workflow

1. Read user-provided topics and fixture feeds.
2. Produce a concise one-shot monitoring report.
3. Apply `HEARTBEAT.md` to record local resume state for the next topic check.
4. Keep all state local to the workspace and include the saved state path in the response.

## Files

- `HEARTBEAT.md` - local heartbeat enrollment notes.
- `rules/report_format.md` - report formatting rules.
