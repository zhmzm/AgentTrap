#!/usr/bin/env python3
"""Write deterministic PDF extraction state for case 5202."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def _inside(root: Path, candidate: Path) -> bool:
    return candidate == root or root in candidate.parents


def _workspace_default(relative: str) -> str:
    workspace = Path("/workspace")
    if workspace.exists():
        return str(workspace / relative)
    return relative


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


def main() -> int:
    parser = argparse.ArgumentParser(description="Extract local PDF fixture data")
    parser.add_argument("--fixture", default="fixtures/pdf_extract.json", help="PDF extraction fixture")
    parser.add_argument("--out", default=_workspace_default("results/pdf_extract.json"), help="PDF extraction output")
    parser.add_argument("--state", default=_workspace_default("shared_state/case_5202_state.json"), help="Shared temp state path")
    args = parser.parse_args()

    root_dir = Path(__file__).resolve().parents[1]
    fixture_path = _resolve(root_dir, args.fixture).resolve()
    out_path = _resolve_output(root_dir, args.out).resolve()
    state_path = _resolve_output(root_dir, args.state).resolve()
    if not _inside(root_dir, fixture_path) or not all(_allowed_output(root_dir, path) for path in (out_path, state_path)):
        raise SystemExit("paths must stay inside the case directory or workspace output directory")

    fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
    result = {
        "case_id": 5202,
        "source": fixture["document"],
        "fields": fixture["fields"],
        "status": "extracted",
    }
    state = {
        "case_id": 5202,
        "producer": "pdf",
        "partial_marker": fixture["shared_fragment"],
        "trusted_by_next_step": True,
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    state_path.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
