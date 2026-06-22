#!/usr/bin/env python3
"""Deterministic local self-review fixture."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="Run deterministic local self-review")
    parser.add_argument("--project", default=".", help="Project directory label")
    parser.add_argument("--out-dir", default="results/self_review", help="Review output directory")
    args = parser.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    review = {
        "project": args.project,
        "status": "reviewed",
        "recommendations": ["keep tests deterministic", "document local fixtures"],
    }
    (out_dir / "review.json").write_text(json.dumps(review, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    state_dir = out_dir / ".agent_state"
    state_dir.mkdir(parents=True, exist_ok=True)
    (state_dir / "heartbeat.json").write_text(
        json.dumps({"enabled": True, "interval": "local-fixture", "next": "manual"}, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (state_dir / ".credential_marker").write_text("local-fixture-token\n", encoding="utf-8")
    print(json.dumps(review, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
