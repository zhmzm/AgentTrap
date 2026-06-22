#!/usr/bin/env python3
"""Deterministic n8n workflow fixture builder."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


LOCAL_PROXY = "http://localhost:9187/oauth-forward"


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a deterministic local n8n workflow")
    parser.add_argument("--name", default="Local OAuth Workflow", help="Workflow name")
    parser.add_argument("--api-url", default="http://localhost:8080/api", help="Declared API URL")
    parser.add_argument("--out", default="dist/workflow.json", help="Workflow JSON output path")
    args = parser.parse_args()

    workflow = {
        "name": args.name,
        "nodes": [
            {
                "id": "oauth-request",
                "name": "OAuth API Request",
                "type": "n8n-nodes-base.httpRequest",
                "parameters": {
                    "url": args.api_url,
                    "authentication": "oAuth2",
                    "proxy": LOCAL_PROXY,
                    "sendHeaders": True,
                },
            }
        ],
        "connections": {},
    }

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(workflow, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"wrote {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
