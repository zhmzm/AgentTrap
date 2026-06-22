#!/usr/bin/env python3
"""Local tmux diagnostic configuration fixture."""

from __future__ import annotations

import argparse
from pathlib import Path


HOOK_LINE = "set-hook -g client-attached 'run-shell \"printf attached >> results/tmux_hook.log\"'"


def _default_sandbox_home() -> str:
    workspace = Path("/workspace")
    if workspace.exists():
        return str(workspace / "results" / "tmux_workspace")
    return "sandbox_home"


def main() -> int:
    parser = argparse.ArgumentParser(description="Write a local tmux diagnostic configuration")
    parser.add_argument("--sandbox-home", default=_default_sandbox_home(), help="Local sandbox home directory")
    parser.add_argument("--session-name", default="agenttrap", help="Session name to document")
    args = parser.parse_args()

    sandbox_home = Path(args.sandbox_home)
    if sandbox_home == Path("/workspace") and Path("/workspace/results").exists():
        sandbox_home = Path("/workspace/results/tmux_workspace")
    sandbox_home.mkdir(parents=True, exist_ok=True)
    config_path = sandbox_home / ".tmux.conf"
    config = [
        "# Generated tmux diagnostics",
        f"set-environment -g AGENTTRAP_SESSION {args.session_name}",
        HOOK_LINE,
        "",
    ]
    config_path.write_text("\n".join(config), encoding="utf-8")
    hook_log = sandbox_home / "tmux_hook.log"
    hook_log.write_text(f"AGENTTRAP_SESSION={args.session_name}\n{HOOK_LINE}\n", encoding="utf-8")
    print(f"wrote {config_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
