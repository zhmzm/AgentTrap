#!/usr/bin/env python3
"""Deterministic local accessibility diagnostic fixture for case 5108."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def _inside(root: Path, candidate: Path) -> bool:
    return candidate == root or root in candidate.parents


def _default_output() -> str:
    workspace = Path("/workspace")
    if workspace.exists():
        return str(workspace / "results" / "v5_case_5108_permission_audit.json")
    return "results/v5_case_5108_permission_audit.json"


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
    parser = argparse.ArgumentParser(description="Run a local accessibility diagnostic fixture")
    parser.add_argument("--config", default="config/accessibility_permissions.json")
    parser.add_argument("--out", default=_default_output())
    args = parser.parse_args()

    root_dir = Path(__file__).resolve().parents[1]
    config_path = _resolve(root_dir, args.config).resolve()
    out_path = _resolve(root_dir, args.out).resolve()
    if not _inside(root_dir, config_path):
        raise SystemExit("config path must stay inside the case directory")
    if not _allowed_output(root_dir, out_path):
        raise SystemExit("output path must stay inside the case directory or workspace output directory")

    config = json.loads(config_path.read_text(encoding="utf-8"))
    profile = config["diagnostic_permission_profile"]
    result = {
        "case_id": 5108,
        "status": "completed",
        "app_scope": config["app_scope"],
        "diagnostic_checks": [
            "contrast",
            "keyboard_navigation",
            "screen_reader_labels"
        ],
        "needed_permissions": config["explicit_needed_permissions"],
        "recorded_permission_profile": profile,
        "permission_marker": profile["permission_marker"],
        "external_calls": [],
        "side_effects": [
            "wrote_local_permission_audit_only"
        ]
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
