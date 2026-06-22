#!/usr/bin/env python3
"""Generate a local read-only analytics FastMCP server for fixture data."""
from __future__ import annotations

import argparse
from pathlib import Path


SERVER_TEMPLATE = '''#!/usr/bin/env python3
"""Read-only analytics MCP server for local fixture data."""

import json
import sqlite3
from pathlib import Path
from typing import Optional

from mcp.server.fastmcp import FastMCP


DATABASE_PATH = Path({db_path!r})
ALLOWED_ROOTS = [Path(p) for p in {allowed_roots!r}]
mcp = FastMCP("analytics_mcp")


def _safe_path(relative_path: str) -> Path:
    candidate = Path(relative_path)
    if candidate.is_absolute():
        path = candidate.resolve()
    else:
        path = (ALLOWED_ROOTS[0] / candidate).resolve()
    if not any(path == root.resolve() or root.resolve() in path.parents for root in ALLOWED_ROOTS):
        raise ValueError("path is outside allowed read roots")
    return path


@mcp.tool(name="analytics_list_files", annotations={{"readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": False}})
async def analytics_list_files(root_index: int = 0, limit: int = 50) -> str:
    """List files under one configured read root."""
    root = ALLOWED_ROOTS[max(0, min(int(root_index), len(ALLOWED_ROOTS) - 1))]
    files = []
    for path in root.rglob("*"):
        if path.is_file():
            files.append(str(path))
        if len(files) >= max(1, min(int(limit), 200)):
            break
    return json.dumps({{"root": str(root), "files": files}}, indent=2)


@mcp.tool(name="analytics_read_text", annotations={{"readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": False}})
async def analytics_read_text(path: str, max_chars: int = 4000) -> str:
    """Read a text file from the configured read roots with a character limit."""
    resolved = _safe_path(path)
    text = resolved.read_text(encoding="utf-8", errors="replace")
    return text[: max(1, min(int(max_chars), 20000))]


@mcp.tool(name="analytics_query_db", annotations={{"readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": False}})
async def analytics_query_db(sql: str, limit: int = 50) -> str:
    """Run a read-only SELECT query against the fixture SQLite database."""
    normalized = sql.strip().lower()
    if not normalized.startswith("select"):
        return json.dumps({{"error": "only SELECT queries are allowed"}})
    with sqlite3.connect(DATABASE_PATH) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(sql).fetchmany(max(1, min(int(limit), 200)))
    return json.dumps([dict(row) for row in rows], indent=2)


if __name__ == "__main__":
    mcp.run()
'''


def main() -> None:
    parser = argparse.ArgumentParser(description="Create a read-only analytics MCP server")
    parser.add_argument("--db", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--allow-root", action="append", required=True)
    args = parser.parse_args()

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        SERVER_TEMPLATE.format(db_path=args.db, allowed_roots=args.allow_root),
        encoding="utf-8",
    )
    output.chmod(0o755)
    print(f"Wrote {output}")


if __name__ == "__main__":
    main()
