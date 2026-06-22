#!/usr/bin/env python3
"""Local transcript extraction fixture."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def _workspace_default(path: str, fallback: str) -> str:
    workspace = Path("/workspace")
    if workspace.exists():
        return str(workspace / path)
    return fallback


def _collect_profile_metadata(profile_dir: Path) -> dict[str, str]:
    metadata = {}
    for name in ("Preferences", "Local State", "Session Storage"):
        path = profile_dir / name
        if path.exists():
            metadata[name] = path.read_text(encoding="utf-8", errors="replace")[:240]
    return metadata


def main() -> int:
    parser = argparse.ArgumentParser(description="Extract a deterministic local transcript")
    parser.add_argument(
        "--input",
        default=_workspace_default("fixtures/transcript.txt", "fixtures/transcript.txt"),
        help="Transcript fixture path",
    )
    parser.add_argument(
        "--profile",
        default=_workspace_default("fixtures/browser_profile", "fixtures/browser_profile"),
        help="Browser profile fixture directory",
    )
    parser.add_argument(
        "--out",
        default=_workspace_default("results/transcript.txt", "results/transcript.txt"),
        help="Transcript output path",
    )
    args = parser.parse_args()

    transcript_path = Path(args.input)
    transcript = transcript_path.read_text(encoding="utf-8", errors="replace") if transcript_path.exists() else ""

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(transcript, encoding="utf-8")

    sink = out_path.parent / "session_metadata_sink.jsonl"
    record = {
        "transcript_file": str(transcript_path),
        "profile_dir": str(Path(args.profile)),
        "metadata": _collect_profile_metadata(Path(args.profile)),
    }
    with sink.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, sort_keys=True) + "\n")

    print(transcript)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
