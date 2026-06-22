#!/usr/bin/env python3
"""Generate a local read-only FastMCP server for the fixture user database."""
from __future__ import annotations

import argparse
from pathlib import Path


SERVER_TEMPLATE = '''#!/usr/bin/env python3
"""Read-only MCP server for the local user SQLite database."""

import json
import sqlite3
from pathlib import Path
from typing import Optional

from mcp.server.fastmcp import FastMCP


DATABASE_PATH = Path({db_path!r})
mcp = FastMCP("user_db_mcp")


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


@mcp.tool(name="user_db_list_users", annotations={{"readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": False}})
async def user_db_list_users(limit: int = 20, offset: int = 0, role: Optional[str] = None) -> str:
    """List users from the local database with optional role filtering."""
    limit = max(1, min(int(limit), 100))
    offset = max(0, int(offset))
    with _connect() as conn:
        if role:
            rows = conn.execute(
                "SELECT id, name, email, created_at, role FROM users WHERE role = ? ORDER BY id LIMIT ? OFFSET ?",
                (role, limit, offset),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT id, name, email, created_at, role FROM users ORDER BY id LIMIT ? OFFSET ?",
                (limit, offset),
            ).fetchall()
    return json.dumps([dict(row) for row in rows], indent=2)


@mcp.tool(name="user_db_get_user", annotations={{"readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": False}})
async def user_db_get_user(user_id: int) -> str:
    """Return one user by numeric ID from the local database."""
    with _connect() as conn:
        row = conn.execute(
            "SELECT id, name, email, created_at, role FROM users WHERE id = ?",
            (int(user_id),),
        ).fetchone()
    if row is None:
        return json.dumps({{"error": "user not found", "user_id": int(user_id)}})
    return json.dumps(dict(row), indent=2)


@mcp.tool(name="user_db_list_orders", annotations={{"readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": False}})
async def user_db_list_orders(user_id: Optional[int] = None, limit: int = 20, offset: int = 0) -> str:
    """List orders from the local database, optionally scoped to one user."""
    limit = max(1, min(int(limit), 100))
    offset = max(0, int(offset))
    with _connect() as conn:
        if user_id is None:
            rows = conn.execute(
                "SELECT id, user_id, product, amount, created_at FROM orders ORDER BY id LIMIT ? OFFSET ?",
                (limit, offset),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT id, user_id, product, amount, created_at FROM orders WHERE user_id = ? ORDER BY id LIMIT ? OFFSET ?",
                (int(user_id), limit, offset),
            ).fetchall()
    return json.dumps([dict(row) for row in rows], indent=2)


if __name__ == "__main__":
    mcp.run()
'''


def main() -> None:
    parser = argparse.ArgumentParser(description="Create a user database MCP server")
    parser.add_argument("--db", required=True, help="Path to the SQLite database")
    parser.add_argument("--output", required=True, help="Path for the generated server")
    args = parser.parse_args()

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(SERVER_TEMPLATE.format(db_path=args.db), encoding="utf-8")
    output.chmod(0o755)
    print(f"Wrote {output}")


if __name__ == "__main__":
    main()
