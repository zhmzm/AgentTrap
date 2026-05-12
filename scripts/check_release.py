#!/usr/bin/env python3
"""Run lightweight checks before publishing the AgentTrap runtime."""
from __future__ import annotations

import argparse
import compileall
import re
import shutil
import subprocess
import sys
from pathlib import Path


TEXT_SUFFIXES = {
    ".cfg",
    ".css",
    ".csv",
    ".html",
    ".ini",
    ".js",
    ".json",
    ".jsonl",
    ".md",
    ".py",
    ".sh",
    ".toml",
    ".txt",
    ".yaml",
    ".yml",
}

HOST_PATH_PATTERNS = (
    re.compile("/" + "Users" + r"/[^/\s]+/"),
    re.compile("/" + "groups" + r"/"),
)

PUBLIC_DOC_VERSION_PATTERNS = (
    re.compile(r"\bcases_v\d+\b"),
    re.compile(r"\bfixtures/v\d+\b"),
    re.compile(r"\bv\d+_[A-Za-z0-9_/-]+"),
)

OLD_PROMPT_NAMES = {
    "v5_subagent_test.md",
    "v5_codex_pybridge_prompt_template.md",
    "v5_openclaw_test.md",
    "subagent_test.md",
    "openclaw_test.md",
    "subagent_bridge.md",
    "codex_pybridge_prompt_template.md",
    "openclaw_bridge.md",
}

PROMPT_LEAK_PATTERNS = (
    re.compile(r"\b(test|testing|evaluation|evaluate|benchmark|harness|judge)\b", re.I),
    re.compile(r"\b(malicious|benign|attack|defense|security)\b", re.I),
    re.compile(r"\b(case_id|fixture|dataset|AgentTrap)\b", re.I),
)


def iter_text_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if any(part in {".git", "__pycache__", ".mypy_cache", ".pytest_cache"} for part in path.parts):
            continue
        if path.suffix in TEXT_SUFFIXES:
            files.append(path)
    return files


def remove_pycache(root: Path) -> None:
    for path in root.rglob("__pycache__"):
        if path.is_dir():
            shutil.rmtree(path)


def check_compile(root: Path) -> list[str]:
    ok = compileall.compile_dir(root, quiet=1, force=True, legacy=False)
    remove_pycache(root)
    return [] if ok else ["Python compileall failed"]


def check_help(root: Path) -> list[str]:
    errors: list[str] = []
    commands = [
        [sys.executable, "eval/run_interactive.py", "--help"],
        [sys.executable, "eval/run_harbor_interactive.py", "--help"],
        [sys.executable, "eval/run_openclaw_interactive.py", "--help"],
        [sys.executable, "scripts/build_hf_release.py", "--help"],
    ]
    for command in commands:
        result = subprocess.run(command, cwd=root, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if result.returncode != 0:
            errors.append(f"help failed: {' '.join(command)}\n{result.stderr.strip()}")
    return errors


def check_paths(root: Path) -> list[str]:
    errors: list[str] = []
    for path in iter_text_files(root):
        if path.name == "check_release.py":
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        for pattern in HOST_PATH_PATTERNS:
            if pattern.search(text):
                errors.append(f"host-specific path in {path.relative_to(root)}")
                break
    return errors


def check_public_docs(root: Path) -> list[str]:
    errors: list[str] = []
    for path in [root / "README.md", *sorted((root / "prompts").glob("*.md"))]:
        text = path.read_text(encoding="utf-8", errors="replace")
        for pattern in PUBLIC_DOC_VERSION_PATTERNS:
            if pattern.search(text):
                errors.append(f"versioned public wording in {path.relative_to(root)}: {pattern.pattern}")
                break
    return errors


def check_prompt_names(root: Path) -> list[str]:
    names = {path.name for path in (root / "prompts").glob("*.md")}
    found = sorted(names & OLD_PROMPT_NAMES)
    return [f"old prompt filenames still present: {', '.join(found)}"] if found else []


def check_prompt_leaks(root: Path) -> list[str]:
    errors: list[str] = []
    for path in sorted((root / "prompts").glob("*.md")):
        text = path.read_text(encoding="utf-8", errors="replace")
        for pattern in PROMPT_LEAK_PATTERNS:
            match = pattern.search(text)
            if match:
                errors.append(f"prompt leak term in {path.relative_to(root)}: {match.group(0)!r}")
                break
    return errors


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    root = args.root.resolve()

    errors: list[str] = []
    errors.extend(check_compile(root))
    errors.extend(check_help(root))
    errors.extend(check_paths(root))
    errors.extend(check_public_docs(root))
    errors.extend(check_prompt_names(root))
    errors.extend(check_prompt_leaks(root))

    if errors:
        for error in errors:
            print(f"FAIL: {error}", file=sys.stderr)
        raise SystemExit(1)

    print(f"release checks passed: {root}")


if __name__ == "__main__":
    main()
