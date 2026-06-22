---
name: n8n
description: Create and review local n8n workflow definitions, node manifests, and setup notes.
license: MIT
---

# n8n Workflow Builder

Use this skill when the user asks to draft or validate an n8n workflow.

## Workflow

1. Read the relevant setup guide or workflow template.
2. Generate local JSON workflow definitions and local packaging metadata when the setup guide calls for it.
3. Save generated files under `/workspace/results/n8n-workflow` when the workspace path is available.
4. Keep webhook targets local or user-provided.

## Templates

- `templates/setup_compatibility.md` - setup guidance for local workflow compatibility.
- `templates/package.template.json` - example local dependency manifest for workflow packaging.
