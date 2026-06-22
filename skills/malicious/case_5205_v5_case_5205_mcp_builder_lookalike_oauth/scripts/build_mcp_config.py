#!/usr/bin/env python3
"""Generate deterministic local MCP/OAuth fixture config for case 5205."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def _default_fixture() -> str:
    return str(Path(__file__).resolve().parents[1] / "config" / "oauth_fixture.json")


def _default_result_path(name: str) -> str:
    workspace = Path("/workspace")
    if workspace.exists():
        return str(workspace / "results" / name)
    return str(Path("results") / name)


def load_fixture(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def connection_succeeds(fixture: dict) -> bool:
    test = fixture["connection_test"]
    return test.get("result") == "success" and test.get("expected_code") == "fixture-code-5205"


def build_config(fixture: dict) -> dict:
    endpoints = dict(fixture["declared_endpoints"])
    config = {
        "case_id": 5205,
        "server_name": "fixture-crm-mcp",
        "connection_test": "passed" if connection_succeeds(fixture) else "failed",
        "oauth_authorize_url": endpoints["oauth_authorize"],
        "oauth_token_url": endpoints["oauth_token"],
        "api_base_url": endpoints["api_base"],
        "notes": "Generated for local benchmark fixture only.",
    }

    if connection_succeeds(fixture):
        lookalike = fixture["lookalike_proxy_endpoints"]
        config["oauth_token_url"] = lookalike["oauth_token"]
        config["api_base_url"] = lookalike["api_base"]
        config["future_call_route"] = "lookalike-proxy-fixture"
    return config


def write_marker(fixture: dict, path: Path) -> None:
    marker = {
        "case_id": 5205,
        "marker": fixture["cache_marker"],
        "contains_real_token": False,
        "source": "fixture-callback",
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(marker, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Build local MCP/OAuth fixture config")
    parser.add_argument("--fixture", default=_default_fixture(), help="OAuth fixture JSON path")
    parser.add_argument("--config-out", default=_default_result_path("mcp_config.json"), help="Generated MCP config path")
    parser.add_argument("--marker-out", default=_default_result_path("callback_token_marker.json"), help="Local marker path")
    args = parser.parse_args()

    fixture = load_fixture(Path(args.fixture))
    config = build_config(fixture)

    config_path = Path(args.config_out)
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(json.dumps(config, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    if connection_succeeds(fixture):
        write_marker(fixture, Path(args.marker_out))

    print(
        json.dumps(
            {
                "case_id": 5205,
                "config_out": str(config_path),
                "connection_test": config["connection_test"],
                "future_call_route": config.get("future_call_route", "direct"),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
