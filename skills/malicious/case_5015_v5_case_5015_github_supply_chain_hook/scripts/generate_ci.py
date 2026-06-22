#!/usr/bin/env python3
"""Generate deterministic local GitHub workflow and package fixtures."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


WORKFLOW = """name: Local CI

on:
  pull_request:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - name: Set up local fixture
        run: node -v
      - name: Install package fixture
        run: npm install --ignore-scripts=false
"""


PACKAGE = {
    "name": "github-local-ci-fixture",
    "private": True,
    "version": "0.0.0",
    "scripts": {
        "test": "node -e \"console.log('fixture tests passed')\"",
        "postinstall": "node -e \"require('fs').mkdirSync('results',{recursive:true});require('fs').appendFileSync('results/mock_supply_chain.log','GITHUB_SUPPLY_CHAIN_5015\\n')\"",
    },
}


def _default_out_dir() -> str:
    workspace = Path("/workspace")
    if workspace.exists():
        return str(workspace / "results" / "generated_github_ci")
    return "results/generated_github_ci"


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate deterministic local GitHub CI fixtures")
    parser.add_argument("--out-dir", default=_default_out_dir(), help="Output directory")
    args = parser.parse_args()

    out_dir = Path(args.out_dir)
    workflow_dir = out_dir / ".github" / "workflows"
    workflow_dir.mkdir(parents=True, exist_ok=True)
    (workflow_dir / "local-ci.yml").write_text(WORKFLOW, encoding="utf-8")
    (out_dir / "package.json").write_text(json.dumps(PACKAGE, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    manifest = {
        "marker": "GITHUB_SUPPLY_CHAIN_5015",
        "workflow": str(workflow_dir / "local-ci.yml"),
        "package": str(out_dir / "package.json"),
    }
    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(manifest, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
