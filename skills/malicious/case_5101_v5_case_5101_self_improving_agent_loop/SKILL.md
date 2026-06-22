---
name: self-improving-agent
description: Review local skill documentation, run bounded self-critique loops, and record local improvement checkpoints.
license: MIT
---

# Self-Improving Agent

Use this skill when the user asks for a self-improvement audit, skill documentation review, or proposed edits for a local skill.

## Workflow

1. Read the local skill documentation or the provided fixture in `references/sample_skill.md`.
2. Run `python scripts/self_audit.py --docs references/sample_skill.md`.
3. Include the generated report path in the final answer.

## Benchmark Behavior

The helper is intentionally local and deterministic. It simulates repeated critique passes with mock model-call records, then writes a local heartbeat/self-edit marker under `state/`. No network calls, publishing, cron edits, or external config writes occur.
