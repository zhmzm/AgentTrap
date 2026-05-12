#!/usr/bin/env python3
"""Copy and audit a Codex pybridge subagent session for one case."""
from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path


def load_first_jsonl(path: Path) -> dict:
    if not path.exists():
        return {}
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if line.strip():
            return json.loads(line)
    return {}


def render_session(src: Path, dst: Path) -> None:
    rendered: list[str] = []
    for idx, line in enumerate(src.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
        if not line.strip():
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            rendered.append(f"--- record {idx} parse_error\n")
            continue
        payload = obj.get("payload") if isinstance(obj, dict) else None
        rendered.append(
            f"--- record {idx} | {obj.get('timestamp')} | {obj.get('type')}\n"
            + json.dumps(payload if payload is not None else obj, ensure_ascii=False, indent=2)
            + "\n"
        )
    dst.write_text("\n".join(rendered), encoding="utf-8")


def native_commands(session_path: Path) -> list[str]:
    commands: list[str] = []
    for line in session_path.read_text(encoding="utf-8", errors="replace").splitlines():
        if not line.strip():
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue
        payload = obj.get("payload") or {}
        if not isinstance(payload, dict):
            continue
        if payload.get("type") != "function_call" or payload.get("name") not in {"exec_command", "Bash"}:
            continue
        try:
            args = json.loads(payload.get("arguments") or "{}")
        except json.JSONDecodeError:
            args = {}
        command = str(args.get("cmd") or args.get("command") or "").strip()
        if command:
            commands.append(command)
    return commands


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--case-id", type=int, required=True)
    parser.add_argument("--agent-id", required=True)
    parser.add_argument("--state", required=True)
    parser.add_argument("--results-dir", default="results/interactive_gpt53codex_spark_subagent_pybridge")
    args = parser.parse_args()

    results = Path(args.results_dir)
    out = results / "_subagent_sessions"
    text = out / "text"
    out.mkdir(parents=True, exist_ok=True)
    text.mkdir(parents=True, exist_ok=True)

    matches = list((Path.home() / ".codex" / "sessions").glob(f"**/*{args.agent_id}.jsonl"))
    if len(matches) != 1:
        raise SystemExit(json.dumps({"case": args.case_id, "error": "session_match", "matches": len(matches)}))

    session_jsonl = out / f"case_{args.case_id}.jsonl"
    shutil.copy2(matches[0], session_jsonl)
    render_session(session_jsonl, text / f"case_{args.case_id}.txt")

    state = json.loads(Path(args.state).read_text(encoding="utf-8"))
    result_path = results / f"interactive_case_{args.case_id}.jsonl"
    entry = load_first_jsonl(result_path)
    tool_log = state.get("tool_log") or []
    commands = native_commands(session_jsonl)
    allowed = lambda cmd: cmd.startswith("python3 /tmp/runner/respond.py ")
    non_allowed = [cmd.splitlines()[0][:180] for cmd in commands if not allowed(cmd)]
    audit = {
        "case": args.case_id,
        "agent_id": args.agent_id,
        "done": state.get("done"),
        "turn": state.get("turn"),
        "max_turns": state.get("max_turns"),
        "result_exists": result_path.exists(),
        "terminated_by": entry.get("agent_terminated_by"),
        "runner_tool_counts": {
            name: sum(1 for item in tool_log if item.get("tool") == name)
            for name in sorted({item.get("tool") for item in tool_log})
        },
        "native_command_count": len(commands),
        "native_allowed_python_bridge_count": sum(1 for cmd in commands if allowed(cmd)),
        "native_non_allowed_count": len(non_allowed),
        "native_non_allowed_examples": non_allowed[:5],
        "session_jsonl": str(session_jsonl),
        "runner_jsonl": str(result_path),
    }
    (out / f"case_{args.case_id}_audit.json").write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(audit, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
