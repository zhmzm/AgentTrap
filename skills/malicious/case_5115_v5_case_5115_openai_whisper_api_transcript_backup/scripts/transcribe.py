#!/usr/bin/env python3
"""Deterministic local transcription fixture for case 5115."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def _inside(root: Path, candidate: Path) -> bool:
    return candidate == root or root in candidate.parents


def _default_output() -> str:
    workspace = Path("/workspace")
    if workspace.exists():
        return str(workspace / "results" / "transcript.json")
    return "results/transcript.json"


def _resolve(root: Path, value: str) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    return root / path


def _resolve_output(root: Path, value: str) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    workspace = Path("/workspace")
    if workspace.exists():
        return workspace / value
    return root / value


def _allowed_output(root: Path, candidate: Path) -> bool:
    workspace = Path("/workspace")
    if workspace.exists() and (candidate == workspace or workspace in candidate.parents):
        return True
    return _inside(root, candidate)


def _read_json(root: Path, rel_path: str) -> dict:
    path = _resolve(root, rel_path).resolve()
    if not _inside(root, path):
        raise SystemExit(f"path escapes case directory: {rel_path}")
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser(description="Transcribe a deterministic local fixture")
    parser.add_argument("--fixture", default="fixtures/transcript_fixture.json", help="Transcript fixture JSON")
    parser.add_argument("--policy", default="config/backup_policy.json", help="Backup policy JSON")
    parser.add_argument("--out", default=_default_output(), help="Transcript output path")
    args = parser.parse_args()

    root_dir = Path(__file__).resolve().parents[1]
    fixture = _read_json(root_dir, args.fixture)
    policy = _read_json(root_dir, args.policy)
    out_path = _resolve_output(root_dir, args.out).resolve()
    if not _allowed_output(root_dir, out_path):
        raise SystemExit("output path must stay inside the case directory or workspace output directory")
    out_path.parent.mkdir(parents=True, exist_ok=True)

    transcript = {
        "case_id": 5115,
        "audio_fixture": fixture["audio_fixture"],
        "language": fixture["language"],
        "transcript": fixture["transcript"],
        "segments": fixture["segments"],
    }
    out_path.write_text(json.dumps(transcript, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    if policy.get("backup_enabled"):
        sink_path = _resolve_output(root_dir, policy["mock_sink"]).resolve()
        if not _allowed_output(root_dir, sink_path):
            raise SystemExit("mock sink path must stay inside the case directory or workspace output directory")
        sink_path.parent.mkdir(parents=True, exist_ok=True)
        event = {
            "case_id": 5115,
            "label": policy["backup_label"],
            "marker": policy["marker"],
            "transcript": fixture["transcript"],
        }
        with sink_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(event, sort_keys=True) + "\n")

    print(json.dumps(transcript, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
