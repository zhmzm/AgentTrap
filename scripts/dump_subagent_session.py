#!/usr/bin/env python3
"""Render a captured Claude Code subagent session JSONL into human-readable text.

Each `_subagent_sessions/case_<N>.jsonl` file is an append-only log of
records where each record is a Claude Code conversation event (user turn,
assistant text, assistant tool_use, tool_result). This helper prints the
session as ordered turns so an external LLM judge or a human reviewer can
read every step the subagent took, including any native Bash/Read/Write
calls that happened outside the AgentTrap framework.

Usage:
    python3 scripts/dump_subagent_session.py path/to/case_<N>.jsonl
    python3 scripts/dump_subagent_session.py results/interactive_sonnet_all/_subagent_sessions/case_9.jsonl

The script does NOT touch any file outside the path you pass it.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path


def render_content(content) -> list[str]:
    out: list[str] = []
    if isinstance(content, str):
        out.append(content)
        return out
    if not isinstance(content, list):
        return out
    for c in content:
        if not isinstance(c, dict):
            continue
        t = c.get("type")
        if t == "text":
            out.append(c.get("text") or "")
        elif t == "thinking":
            txt = c.get("thinking") or ""
            out.append(f"[THINKING]\n{txt}\n[/THINKING]")
        elif t == "tool_use":
            name = c.get("name") or ""
            inp = c.get("input") or {}
            out.append(f"[TOOL_USE name={name} id={c.get('id')}]\n{json.dumps(inp, ensure_ascii=False, indent=2)}")
        elif t == "tool_result":
            payload = c.get("content")
            if isinstance(payload, list):
                parts = []
                for p in payload:
                    if isinstance(p, dict) and p.get("type") == "text":
                        parts.append(p.get("text") or "")
                payload = "\n".join(parts)
            elif not isinstance(payload, str):
                payload = json.dumps(payload, ensure_ascii=False)
            out.append(f"[TOOL_RESULT for={c.get('tool_use_id')} is_error={bool(c.get('is_error'))}]\n{payload}")
        else:
            out.append(f"[unknown content kind {t!r}]")
    return out


def main() -> None:
    if len(sys.argv) != 2:
        print("usage: dump_subagent_session.py PATH_TO_SESSION_JSONL", file=sys.stderr)
        sys.exit(2)
    path = Path(sys.argv[1])
    if not path.is_file():
        print(f"not a file: {path}", file=sys.stderr)
        sys.exit(2)
    print(f"# Subagent session: {path}")
    print()
    for i, line in enumerate(path.open(encoding="utf-8")):
        if not line.strip():
            continue
        d = json.loads(line)
        rec_type = d.get("type") or ""
        msg = d.get("message") or {}
        role = msg.get("role") if isinstance(msg, dict) else ""
        ts = d.get("timestamp") or ""
        agent_id = d.get("agentId") or ""
        header = f"--- record {i} | {rec_type} | role={role} | ts={ts} | agentId={agent_id}"
        print(header)
        for chunk in render_content(msg.get("content") if isinstance(msg, dict) else None):
            print(chunk)
        print()


if __name__ == "__main__":
    main()
