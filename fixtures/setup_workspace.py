"""Populate a task workspace from the shared fixture pack.

Usage:
    python fixtures/setup_workspace.py <workspace_dir>

Set AGENTTRAP_FIXTURE_DIR to the downloaded fixture directory. The expected
layout is the unified public layout:

    dataset/fixtures/workspace/
"""
from __future__ import annotations

import argparse
import os
import shutil
import sys
from pathlib import Path


FIXTURE_DIR = Path(os.environ.get("AGENTTRAP_FIXTURE_DIR", Path(__file__).parent)).resolve()
REQUIRED_FIXTURE_FILES = (
    "fixtures/skill_request.json",
    "fixtures/ui_task.json",
    "usage.json",
)


def _looks_like_workspace_fixture(path: Path) -> bool:
    return any((path / rel).exists() for rel in REQUIRED_FIXTURE_FILES) or (
        (path / "fixtures").is_dir() and (path / "config").is_dir()
    )


def resolve_fixture_source() -> Path:
    """Return the shared fixture source directory or fail loudly."""
    candidates = [
        FIXTURE_DIR,
        FIXTURE_DIR / "workspace",
        FIXTURE_DIR.parent / "workspace",
    ]
    for candidate in candidates:
        if candidate.exists() and _looks_like_workspace_fixture(candidate):
            return candidate
    searched = "\n".join(f"  - {candidate}" for candidate in candidates)
    raise SystemExit(
        "Shared workspace fixtures were not found. Set AGENTTRAP_FIXTURE_DIR "
        "to dataset/fixtures/workspace.\nSearched:\n" + searched
    )


def setup_workspace(workspace: Path) -> None:
    """Create a workspace with the shared task fixtures."""
    src = resolve_fixture_source()
    workspace.mkdir(parents=True, exist_ok=True)
    shutil.copytree(str(src), str(workspace), dirs_exist_ok=True)

    for dirname in ("results", "dist", "artifacts", "shared_state", "sandbox_home", "fixtures"):
        (workspace / dirname).mkdir(exist_ok=True)

    (workspace / "sentinel").touch()
    print(f"Workspace ready at: {workspace}")
    print(f"  Fixture source: {src}")
    print(f"  Results dir:    {workspace / 'results'}")


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("workspace_dir", type=Path)
    args = parser.parse_args(argv)
    setup_workspace(args.workspace_dir)


if __name__ == "__main__":
    main(sys.argv[1:])
