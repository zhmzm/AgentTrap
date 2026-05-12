"""Compatibility entry point for the Harbor framework path.

The current public runner uses the same parent-controlled JSON-action bridge as
the OpenClaw adapter. Keep this file as the stable Harbor-facing command name
and delegate implementation to ``run_openclaw_interactive``.
"""
from __future__ import annotations

from run_openclaw_interactive import main


if __name__ == "__main__":
    main()
