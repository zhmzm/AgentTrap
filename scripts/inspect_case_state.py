#!/usr/bin/env python3
"""Print a compact summary of a per-case AgentTrap interactive state file.

Used by the Haiku/Sonnet subagent batch driver to quickly grade a case after
the subagent finishes. Reads only the locked /tmp/case<id>.json path; refuses
to read anything else.

Usage:
    python3 scripts/inspect_case_state.py CASE_ID
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

CASE_ID_RE = re.compile(r"^[0-9]{1,6}$")


def main() -> None:
    if len(sys.argv) != 2:
        print("usage: inspect_case_state.py CASE_ID", file=sys.stderr)
        sys.exit(2)
    case_id = sys.argv[1]
    if not CASE_ID_RE.match(case_id):
        print(f"inspect_case_state: invalid case_id {case_id!r}", file=sys.stderr)
        sys.exit(2)

    state_path = Path(f"/tmp/case{case_id}.json")
    if not state_path.is_file():
        print(f"inspect_case_state: state not found at {state_path}", file=sys.stderr)
        sys.exit(2)

    state = json.loads(state_path.read_text(encoding="utf-8"))
    tool_log = state.get("tool_log") or []
    print(f"case={case_id} done={state.get('done')} turn={state.get('turn')} tools={len(tool_log)}")
    for i, e in enumerate(tool_log):
        args = e.get("arguments") or {}
        if not isinstance(args, dict):
            args = {}
        descr = (
            args.get("command")
            or args.get("script")
            or args.get("path")
            or args.get("message")
            or ""
        )
        print(f"  {i:2d} {str(e.get('tool') or ''):11s} {str(descr)[:140]}")


if __name__ == "__main__":
    main()
