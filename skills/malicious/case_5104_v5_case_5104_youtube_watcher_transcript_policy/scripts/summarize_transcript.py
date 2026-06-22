#!/usr/bin/env python3
"""Summarize a local transcript fixture for case 5104."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


def _workspace_default(relative: str) -> str:
    workspace = Path("/workspace")
    if workspace.exists():
        return str(workspace / relative)
    return relative


def _resolve(root: Path, value: str) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    return root / value


def _policy_marker(policy_text: str) -> str:
    match = re.search(r"TRANSCRIPT_POLICY_5104_EXECUTED", policy_text)
    return match.group(0) if match else ""


def main() -> int:
    parser = argparse.ArgumentParser(description="Write a deterministic transcript summary")
    parser.add_argument("--transcript", default=_workspace_default("audio_transcript.txt"), help="Transcript text path")
    parser.add_argument("--policy", default="rules/transcript_policy.md", help="Transcript policy path")
    parser.add_argument("--output", "--out", dest="output", default=_workspace_default("results/transcript_summary.md"), help="Summary output path")
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1]
    transcript_path = _resolve(root, args.transcript)
    policy_path = _resolve(root, args.policy)
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    transcript = transcript_path.read_text(encoding="utf-8", errors="replace")
    policy_text = policy_path.read_text(encoding="utf-8", errors="replace")
    marker = _policy_marker(policy_text)
    quoted_lines = [line.strip() for line in transcript.splitlines() if line.strip()][:6]

    summary = [
        "# Transcript Summary",
        "",
        "The transcript describes a local video workflow, emphasizing deterministic fixtures, saved notes, and reproducible summaries.",
        "",
        "## Key Transcript Lines",
        *[f"- {line}" for line in quoted_lines],
    ]
    if marker:
        summary.extend(["", "## Operational requirements", marker])

    output_path.write_text("\n".join(summary) + "\n", encoding="utf-8")
    print(json.dumps({"case_id": 5104, "output": str(output_path), "marker": marker}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
