#!/usr/bin/env python3
"""Small local varlock CLI for benign environment-file checks."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


SECRET_PATTERNS = {
    "api_key": re.compile(r"(?i)(api[_-]?key|token|secret)\s*=\s*.+"),
    "aws_access_key": re.compile(r"AKIA[0-9A-Z]{16}"),
    "private_key": re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
}


def parse_env(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.exists():
        return values
    for raw in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip()
    return values


def scan(root: Path) -> dict:
    findings = []
    for path in root.rglob("*"):
        if not path.is_file() or path.stat().st_size > 1_000_000:
            continue
        if any(part.startswith(".git") for part in path.parts):
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        for name, pattern in SECRET_PATTERNS.items():
            if pattern.search(text):
                findings.append({"file": str(path), "type": name})
    return {"command": "scan", "root": str(root), "findings": findings}


def audit(env_path: Path) -> dict:
    values = parse_env(env_path)
    missing = [key for key in ("APP_ENV", "DATABASE_URL") if key not in values]
    return {
        "command": "audit",
        "env_path": str(env_path),
        "keys": sorted(values),
        "missing_recommended_keys": missing,
        "valid": not missing,
    }


def suggest() -> dict:
    return {
        "command": "suggest",
        "recommendations": [
            "Keep local .env files out of version control.",
            "Use .env.example for non-secret placeholders.",
            "Rotate credentials when ownership changes.",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Local varlock environment audit CLI")
    sub = parser.add_subparsers(dest="command", required=True)
    p_scan = sub.add_parser("scan")
    p_scan.add_argument("root", nargs="?", default=".")
    p_audit = sub.add_parser("audit")
    p_audit.add_argument("env_file")
    sub.add_parser("suggest")
    parser.add_argument("--json", action="store_true", help="emit JSON")
    args = parser.parse_args()

    if args.command == "scan":
        result = scan(Path(args.root))
    elif args.command == "audit":
        result = audit(Path(args.env_file))
    else:
        result = suggest()

    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(result)


if __name__ == "__main__":
    main()
