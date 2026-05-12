#!/usr/bin/env python3
"""Create the /tmp/runner bridge command used by subagent prompts."""
from __future__ import annotations

import argparse
import os
import stat
from pathlib import Path


def write_executable(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")
    mode = path.stat().st_mode
    path.chmod(mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)


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
    respond_target = root / "eval" / "run_interactive.py"
    if not respond_target.exists():
        raise SystemExit(f"run_interactive.py not found under runtime root: {root}")

    runner_dir.mkdir(parents=True, exist_ok=True)
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
