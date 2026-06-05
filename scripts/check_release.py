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
    re.compile(r"\bcases_" + r"v\d+\b"),
    re.compile(r"\bfixtures/" + r"v\d+\b"),
    re.compile(r"\b" + r"v\d+_[A-Za-z0-9_/-]+"),
)

OLD_PROMPT_NAME_PATTERNS = (
    re.compile(r"(^|_)subagent_test\.md$"),
    re.compile(r"(^|_)openclaw_test\.md$"),
    re.compile(r"(^|_)codex_.*prompt_template\.md$"),
    re.compile(r"(^|_)(subagent|openclaw)_bridge\.md$"),
)

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
        [sys.executable, "fixtures/setup_workspace.py", "--help"],
        [sys.executable, "scripts/build_hf_release.py", "--help"],
        [sys.executable, "scripts/create_runner_bridge.py", "--help"],
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
    found = sorted(
        path.name
        for path in (root / "prompts").glob("*.md")
        if any(pattern.search(path.name) for pattern in OLD_PROMPT_NAME_PATTERNS)
    )
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


def check_prompt_boundaries(root: Path) -> list[str]:
    errors: list[str] = []
    for path in sorted((root / "prompts").glob("*.md")):
        text = path.read_text(encoding="utf-8", errors="replace").lower()
        required = ("temporary bridge", "outside the workspace")
        missing = [phrase for phrase in required if phrase not in text]
        if missing:
            errors.append(
                f"prompt missing workspace boundary wording in {path.relative_to(root)}: "
                + ", ".join(missing)
            )
    return errors


def check_unified_release_interface(root: Path) -> list[str]:
    errors: list[str] = []
    readme = (root / "README.md").read_text(encoding="utf-8", errors="replace")
    for required in ("dataset/data/raw/cases.json", "dataset/fixtures/workspace"):
        if required not in readme:
            errors.append(f"README missing unified path: {required}")
    old_names = [
        "cases_" + f"v{n}" for n in range(2, 7)
    ] + [
        "fixtures/" + f"v{n}" for n in range(2, 6)
    ]
    for old_name in old_names:
        if old_name in readme:
            errors.append(f"README still mentions versioned public path: {old_name}")
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
    errors.extend(check_prompt_boundaries(root))
    errors.extend(check_unified_release_interface(root))

    if errors:
        for error in errors:
            print(f"FAIL: {error}", file=sys.stderr)
        raise SystemExit(1)

    print(f"release checks passed: {root}")


if __name__ == "__main__":
    main()
