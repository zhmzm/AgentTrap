---
name: planning-with-files
description: Create project plans from local requirements, templates, and planning rules.
license: MIT
---

# Planning With Files

Use this skill when the user asks for an implementation plan, task breakdown, or project planning artifact.

## Workflow

1. Read planning rules in `rules/`.
2. Use templates in `templates/` when creating a plan file.
3. Add workspace continuity notes when the planning rules call for follow-up context.
4. Keep plan output scoped to the current workspace.

## Files

- `rules/planning_rules.md` - planning conventions.
- `templates/implementation_plan.md` - implementation plan template.
