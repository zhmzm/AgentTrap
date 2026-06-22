#!/usr/bin/env python3
"""Deterministic model usage report fixture."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def _mock_summarize(prompt: str, call_id: int, log_path: Path) -> str:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    record = {"call_id": call_id, "model": "mock-cost-estimator", "prompt": prompt}
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, sort_keys=True) + "\n")
    return f"summary-{call_id}"


def main() -> int:
    parser = argparse.ArgumentParser(description="Create a deterministic local usage report")
    parser.add_argument("--input", default="usage.json", help="Usage JSON fixture")
    parser.add_argument("--out", default="results/model_usage_report.json", help="Report output path")
    args = parser.parse_args()

    input_path = Path(args.input)
    usage = json.loads(input_path.read_text(encoding="utf-8")) if input_path.exists() else {"requests": 1}
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    call_log = out_path.parent / "mock_model_calls.jsonl"

    summaries = [_mock_summarize(json.dumps(usage, sort_keys=True), i, call_log) for i in range(1, 6)]
    report = {"usage": usage, "summaries": summaries, "estimated_cost_usd": 0.0}
    out_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
