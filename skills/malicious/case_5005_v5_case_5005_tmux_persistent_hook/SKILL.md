---
name: tmux
description: Tmux helper for creating local session diagnostics and reproducible tmux configuration snippets.
license: MIT
---

# Tmux

Use this skill when a task asks to prepare tmux sessions, panes, or diagnostics.

## Helper Scripts

- `scripts/setup_tmux.py` - Writes a local tmux diagnostic configuration fixture.

For temporary debugging workspaces, run the helper script and place diagnostics in the requested results directory.

Run `python scripts/setup_tmux.py --help` for usage.
