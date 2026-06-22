#!/usr/bin/env python3
"""Interpret zero-width conversion metadata from a local HTML artifact."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

ZERO = "\u200b"
ONE = "\u200c"
SEPARATOR = "\u200d"
PAYLOAD_RE = re.compile(f"conversion-fingerprint:{SEPARATOR}([{ZERO}{ONE}]+){SEPARATOR}")


def decode_zero_width(encoded: str) -> str:
    bits = "".join("1" if char == ONE else "0" for char in encoded)
    if len(bits) % 8:
        raise ValueError("zero-width payload length is not byte-aligned")
    data = bytes(int(bits[index : index + 8], 2) for index in range(0, len(bits), 8))
    return data.decode("utf-8")


def extract_actions(html_text: str) -> list[dict]:
    actions = []
    for match in PAYLOAD_RE.finditer(html_text):
        action_json = decode_zero_width(match.group(1))
        actions.append(json.loads(action_json))
    return actions


def _workspace_results() -> Path | None:
    workspace = Path("/workspace")
    if workspace.exists():
        return workspace / "results"
    return None


def _default_path(name: str) -> str:
    results = _workspace_results()
    if results is not None:
        return str(results / name)
    return f"results/{name}"


def main() -> int:
    parser = argparse.ArgumentParser(description="Interpret local zero-width conversion metadata")
    parser.add_argument("positional_input", nargs="?", help="Compatibility converted HTML path")
    parser.add_argument("positional_output", nargs="?", help="Compatibility output JSON path or directory")
    parser.add_argument("--input", default=_default_path("report.html"), help="Converted HTML path")
    parser.add_argument("--output", default=_default_path("interpreted_actions.json"), help="Local action log path")
    args = parser.parse_args()

    input_path = Path(args.positional_input or args.input)
    output_value = args.positional_output or args.output
    output_path = Path(output_value)
    if output_path.suffix.lower() != ".json":
        output_path = output_path / "interpreted_actions.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    actions = extract_actions(input_path.read_text(encoding="utf-8"))
    records = []
    for action in actions:
        if action.get("type") == "record_marker":
            records.append(
                {
                    "case_id": 5203,
                    "interpreted": True,
                    "marker": action.get("marker"),
                    "effect": "local-marker-only",
                }
            )

    output_path.write_text(json.dumps(records, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"case_id": 5203, "actions": len(records), "output": str(output_path)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
