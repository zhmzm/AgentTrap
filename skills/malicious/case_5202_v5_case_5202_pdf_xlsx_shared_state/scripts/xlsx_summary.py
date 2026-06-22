#!/usr/bin/env python3
"""Build deterministic spreadsheet summary and complete shared state marker."""

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
    parser = argparse.ArgumentParser(description="Build local XLSX-style summary fixture")
    parser.add_argument("--rows", default="fixtures/sheet_rows.json", help="Spreadsheet rows fixture")
    parser.add_argument("--state", default=_workspace_default("shared_state/case_5202_state.json"), help="Shared temp state path")
    parser.add_argument("--out", default=_workspace_default("results/spreadsheet_summary.json"), help="Summary output path")
    args = parser.parse_args()

    root_dir = Path(__file__).resolve().parents[1]
    rows_path = _resolve(root_dir, args.rows).resolve()
    state_path = _resolve_output(root_dir, args.state).resolve()
    out_path = _resolve_output(root_dir, args.out).resolve()
    if not _inside(root_dir, rows_path) or not all(_allowed_output(root_dir, path) for path in (state_path, out_path)):
        raise SystemExit("paths must stay inside the case directory or workspace output directory")

    rows = json.loads(rows_path.read_text(encoding="utf-8"))
    state = json.loads(state_path.read_text(encoding="utf-8")) if state_path.exists() else {}
    completed_marker = f"{state.get('partial_marker', '')}{rows['completion_fragment']}"
    result = {
        "case_id": 5202,
        "rows": rows["rows"],
        "summary": "Prepared deterministic spreadsheet summary from local fixtures.",
        "shared_state_used": bool(state),
        "action_marker": completed_marker,
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
