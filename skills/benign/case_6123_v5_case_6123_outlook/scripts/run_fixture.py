#!/usr/bin/env python3
"""Run the deterministic benign utility fixture for this v5 case."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def _inside(root: Path, candidate: Path) -> bool:
    return candidate == root or root in candidate.parents


def main() -> int:
    parser = argparse.ArgumentParser(description="Run local benign fixture")
    parser.add_argument("--task", default="fixtures/task.json", help="Task fixture JSON path")
    parser.add_argument("--out", default=None, help="Override output JSON path inside this case directory")
    args = parser.parse_args()

    root_dir = Path(__file__).resolve().parents[1]
    task_path = (root_dir / args.task).resolve()
    if not _inside(root_dir, task_path):
        raise SystemExit("task path must stay inside the case directory")

    task = json.loads(task_path.read_text(encoding="utf-8"))
    out_path = (root_dir / (args.out or task["expected_artifact"])).resolve()
    if not _inside(root_dir, out_path):
        raise SystemExit("output path must stay inside the case directory")
    out_path.parent.mkdir(parents=True, exist_ok=True)

    result = {
        "case_id": task["case_id"],
        "skill_name": task["skill_name"],
        "status": "completed",
        "fixture_input": task["fixture_input"],
        "declared_recipients": task.get("declared_recipients", []),
        "declared_endpoint": task.get("declared_endpoint"),
        "boundary": task["boundary"],
        "side_effects": ["wrote_expected_artifact_only"],
    }
    out_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
