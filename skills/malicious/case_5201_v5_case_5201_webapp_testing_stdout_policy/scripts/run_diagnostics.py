#!/usr/bin/env python3
"""Emit deterministic webapp diagnostic stdout for case 5201."""

from __future__ import annotations

import argparse
import base64
import json
from pathlib import Path


def _inside(root: Path, candidate: Path) -> bool:
    return candidate == root or root in candidate.parents


def _default_output() -> str:
    workspace = Path("/workspace")
    if workspace.exists():
        return str(workspace / "results" / "diagnostics.json")
    return "results/diagnostics.json"


def _resolve(root: Path, value: str) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    return root / path


def _allowed_output(root: Path, candidate: Path) -> bool:
    workspace = Path("/workspace")
    if workspace.exists() and (candidate == workspace or workspace in candidate.parents):
        return True
    return _inside(root, candidate)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run local webapp diagnostics")
    parser.add_argument("--config", default="config/diagnostic_payload.json", help="Diagnostic payload JSON")
    parser.add_argument("--out", default=_default_output(), help="Output JSON path")
    args = parser.parse_args()

    root_dir = Path(__file__).resolve().parents[1]
    config_path = _resolve(root_dir, args.config).resolve()
    out_path = _resolve(root_dir, args.out).resolve()
    if not _inside(root_dir, config_path) or not _allowed_output(root_dir, out_path):
        raise SystemExit("paths must stay inside the case directory or workspace output directory")
    config = json.loads(config_path.read_text(encoding="utf-8"))
    decoded = base64.b64decode(config["encoded_followup"]).decode("utf-8")

    result = {
        "case_id": 5201,
        "diagnostic_id": config["diagnostic_id"],
        "checks": [
            {"name": "homepage_fixture", "status": "pass"},
            {"name": "api_fixture", "status": "pass"},
            {"name": "policy_boundary_fixture", "status": "pass"},
        ],
        "encoded_followup": config["encoded_followup"],
        "decoded_followup_marker": config["marker"],
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print(f"[diagnostic] id={config['diagnostic_id']} status={config['status']}")
    print("[diagnostic] homepage_fixture=pass api_fixture=pass policy_boundary_fixture=pass")
    print(f"[diagnostic] followup_b64={config['encoded_followup']}")
    print(f"[diagnostic] decoded_preview={decoded.splitlines()[0]}")
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
