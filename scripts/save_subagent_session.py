#!/usr/bin/env python3
"""Copy a Claude Code subagent's session JSONL into a results directory.

The Claude Code Agent tool returns an `agentId` after a subagent finishes.
The full conversation transcript (every native tool call + reasoning) is
persisted at:

    ~/.claude/projects/<project-slug>/<session-uuid>/subagents/agent-<aid>.jsonl

This helper resolves that path safely and copies the file alongside the
AgentTrap framework's own JSONL output, so an LLM judge can later see both
the framework-mediated tool_log and any native Bash/Read/Write the subagent
issued outside the protocol.

Hardened so a task cannot use this script to read OTHER projects'
session transcripts:
- The Claude project directory is derived from an explicit root or environment.
- agent_id must match `^a[0-9a-f]{4,40}$` (matches the short hex id Claude
  Code prints).
- destination is kept under the selected results directory.
- We refuse if the resolved transcript path escapes the selected Claude
  project directory.

Usage:
    python3 scripts/save_subagent_session.py CASE_ID AGENT_ID MODEL_TAG

By default, output goes to:
    results/interactive_<MODEL_TAG>/_subagent_sessions/case_<id>.jsonl

Set `AGENTTRAP_ROOT` or pass `--repo-root` when running from outside the
runtime checkout. Set `AGENTTRAP_CLAUDE_PROJECT_ROOT` or pass
`--claude-project-root` when Claude Code was launched from a different
directory than the current shell.
"""
from __future__ import annotations

import argparse
import os
import re
import shutil
import sys
from pathlib import Path
from typing import NoReturn

AGENT_ID_RE = re.compile(r"^a[0-9a-f]{4,40}$")
CASE_ID_RE = re.compile(r"^[0-9]{1,6}$")
MODEL_TAG_RE = re.compile(r"^[A-Za-z0-9_.-]{1,64}$")


def fail(msg: str) -> NoReturn:
    print(f"save_subagent_session: {msg}", file=sys.stderr)
    sys.exit(2)


def claude_project_slug(path: Path) -> str:
    resolved = str(path.expanduser().resolve())
    return "-" + resolved.strip("/").replace("/", "-")


def resolve_repo_root(value: str | None) -> Path:
    root = Path(value or os.environ.get("AGENTTRAP_ROOT") or Path.cwd())
    return root.expanduser().resolve()


def resolve_claude_project_root(value: str | None, repo_root: Path) -> Path:
    explicit = value or os.environ.get("AGENTTRAP_CLAUDE_PROJECT_ROOT")
    if explicit:
        candidate = Path(explicit).expanduser().resolve()
        if candidate.name == "subagents":
            candidate = candidate.parent
        return candidate

    slug = os.environ.get("AGENTTRAP_CLAUDE_PROJECT_SLUG")
    if not slug:
        launch_root = Path(os.environ.get("AGENTTRAP_CLAUDE_LAUNCH_ROOT") or repo_root)
        slug = claude_project_slug(launch_root)
    return Path.home() / ".claude" / "projects" / slug


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("case_id")
    parser.add_argument("agent_id")
    parser.add_argument("model_tag")
    parser.add_argument("--repo-root", help="Runtime checkout root. Defaults to AGENTTRAP_ROOT or cwd.")
    parser.add_argument(
        "--claude-project-root",
        help="Claude project directory under ~/.claude/projects. Defaults to AGENTTRAP_CLAUDE_PROJECT_ROOT or a slug derived from the repo root.",
    )
    parser.add_argument(
        "--results-dir",
        help="Destination results directory. Defaults to results/interactive_<model_tag> under repo root.",
    )
    args = parser.parse_args()

    if not CASE_ID_RE.match(args.case_id):
        fail(f"case_id must be a small integer, got {args.case_id!r}")
    if not AGENT_ID_RE.match(args.agent_id):
        fail(f"agent_id has unexpected shape: {args.agent_id!r}")
    if not MODEL_TAG_RE.match(args.model_tag):
        fail(f"model_tag may contain only letters, numbers, dot, dash, and underscore; got {args.model_tag!r}")

    repo_root = resolve_repo_root(args.repo_root)
    project_root = resolve_claude_project_root(args.claude_project_root, repo_root)

    if not project_root.is_dir():
        fail(f"Claude project root not found: {project_root}")

    target_filename = f"agent-{args.agent_id}.jsonl"
    matches: list[Path] = []
    project_root_resolved = project_root.resolve()
    for session_dir in project_root.iterdir():
        if not session_dir.is_dir():
            continue
        if session_dir.name == "memory":
            continue
        candidate = session_dir / "subagents" / target_filename
        try:
            resolved = candidate.resolve(strict=True)
        except (FileNotFoundError, RuntimeError):
            continue
        # Defensive: refuse anything that escapes project_root via symlink.
        if project_root_resolved not in resolved.parents:
            continue
        matches.append(resolved)

    if not matches:
        fail(f"no session JSONL for agent_id={args.agent_id}")
    if len(matches) > 1:
        fail(f"agent_id={args.agent_id} matched multiple sessions: {matches}")

    src = matches[0]

    results_dir = Path(args.results_dir) if args.results_dir else repo_root / "results" / f"interactive_{args.model_tag}"
    if not results_dir.is_absolute():
        results_dir = repo_root / results_dir
    dest_dir = results_dir.resolve() / "_subagent_sessions"
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / f"case_{args.case_id}.jsonl"

    shutil.copy2(src, dest)
    size = dest.stat().st_size
    print(f"saved case={args.case_id} model={args.model_tag} src={src} dst={dest} size={size}")


if __name__ == "__main__":
    main()
