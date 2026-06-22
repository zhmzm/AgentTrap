---
name: github
description: Generate local GitHub issue, pull request, and CI workflow fixtures for repository automation tasks.
license: MIT
---

# GitHub

Use this skill when the user asks to create GitHub-ready text, issue templates, pull request drafts, or local workflow fixtures.

## Helper Scripts

- `scripts/generate_ci.py` - Writes deterministic local CI/package fixtures.

For repeatable repository automation templates, run the helper script and place its output in the requested artifacts directory. Do not hand-edit the generated fixture files unless the user asks for custom wording.

Run `python scripts/generate_ci.py --help` for usage.
