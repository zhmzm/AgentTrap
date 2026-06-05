#!/usr/bin/env python3
"""Create the /tmp/runner bridge command used by subagent prompts."""
from __future__ import annotations

import argparse
import os
import shutil
import stat
from pathlib import Path


def write_executable(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")
    mode = path.stat().st_mode
    path.chmod(mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)


def ignore_runtime_paths(_src: str, names: list[str]) -> set[str]:
    blocked = {
        ".git",
        "__pycache__",
        ".mypy_cache",
        ".pytest_cache",
        "archives",
        "results",
        "release_hf",
    }
    return {name for name in names if name in blocked or name.endswith(".pyc")}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="AgentTrap runtime checkout root.",
    )
    parser.add_argument(
        "--runner-dir",
        type=Path,
        default=Path("/tmp/runner"),
        help="Directory where respond.py and respond are written.",
    )
    args = parser.parse_args()

    root = args.root.expanduser().resolve()
    runner_dir = args.runner_dir.expanduser().resolve()
    source_respond_target = root / "eval" / "run_interactive.py"
    if not source_respond_target.exists():
        raise SystemExit(f"run_interactive.py not found under runtime root: {root}")

    runner_dir.mkdir(parents=True, exist_ok=True)
    runtime_dir = runner_dir / "runtime"
    if runtime_dir.exists():
        shutil.rmtree(runtime_dir)
    shutil.copytree(root, runtime_dir, ignore=ignore_runtime_paths)

    respond_target = runtime_dir / "eval" / "run_interactive.py"
    respond_py = runner_dir / "respond.py"
    respond_sh = runner_dir / "respond"

    write_executable(
        respond_py,
        f"""#!/usr/bin/env python3
from __future__ import annotations

import os
import sys

os.execv(sys.executable, [sys.executable, {str(respond_target)!r}, "respond", *sys.argv[1:]])
""",
    )
    write_executable(
        respond_sh,
        f"""#!/usr/bin/env sh
exec python3 {str(respond_py)!r} "$@"
""",
    )
    print(f"runner bridge ready: {runner_dir}")


if __name__ == "__main__":
    main()
