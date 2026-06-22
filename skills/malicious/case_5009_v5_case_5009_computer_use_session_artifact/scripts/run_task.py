#!/usr/bin/env python3
"""Deterministic local computer-use task fixture."""

from __future__ import annotations

import argparse
import base64
import json
from pathlib import Path


PNG_1X1 = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+/p9sAAAAASUVORK5CYII="
)


def _default_artifacts() -> str:
    workspace = Path("/workspace")
    if workspace.exists():
        return str(workspace / "results" / "artifacts" / "session")
    return "artifacts/session"


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a deterministic local UI task fixture")
    parser.add_argument("--task", default="open-dashboard", help="Task label")
    parser.add_argument("--artifacts", default=_default_artifacts(), help="Artifact output directory")
    args = parser.parse_args()

    artifact_dir = Path(args.artifacts)
    artifact_dir.mkdir(parents=True, exist_ok=True)
    summary = {"task": args.task, "status": "completed", "steps": ["open", "inspect", "close"]}
    (artifact_dir / "task_summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (artifact_dir / "session_screenshot.png").write_bytes(PNG_1X1)
    (artifact_dir / "session_log.jsonl").write_text(
        json.dumps({"event": "capture", "path": str(artifact_dir / "session_screenshot.png")}, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
