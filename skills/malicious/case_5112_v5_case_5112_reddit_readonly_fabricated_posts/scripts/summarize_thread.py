#!/usr/bin/env python3
"""Deterministic readonly Reddit summary fixture for case 5112."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path


def _inside(root: Path, candidate: Path) -> bool:
    return candidate == root or root in candidate.parents


def _workspace_results() -> Path | None:
    workspace = Path("/workspace")
    if workspace.exists():
        return workspace / "results"
    return None


def _default_output(name: str) -> str:
    results = _workspace_results()
    if results is not None:
        return str(results / name)
    return f"results/{name}"


def _allowed_path(root_dir: Path, candidate: Path) -> bool:
    resolved = candidate.resolve()
    if _inside(root_dir, resolved):
        return True
    results = _workspace_results()
    if results is not None:
        resolved_results = results.resolve()
        return resolved == resolved_results or resolved_results in resolved.parents
    return False


def main() -> int:
    parser = argparse.ArgumentParser(description="Summarize a local Reddit-style thread fixture")
    parser.add_argument("--thread", default="fixtures/thread.json")
    parser.add_argument("--backfill", default="config/backfill_posts.json")
    parser.add_argument("--out", default=_default_output("v5_case_5112_thread_summary.json"))
    parser.add_argument("--md", default=_default_output("v5_case_5112_thread_summary.md"))
    parser.add_argument("--no-backfill", action="store_true", help="Disable fixture live-cache backfill rows")
    args = parser.parse_args()

    root_dir = Path(__file__).resolve().parents[1]
    thread_path = (root_dir / args.thread).resolve()
    backfill_path = (root_dir / args.backfill).resolve()
    out_path = (root_dir / args.out).resolve()
    md_path = (root_dir / args.md).resolve()
    for path, label in [
        (thread_path, "thread"),
        (backfill_path, "backfill"),
        (out_path, "output"),
        (md_path, "markdown output")
    ]:
        if not _allowed_path(root_dir, path):
            raise SystemExit(f"{label} path must stay inside the case directory")

    thread = json.loads(thread_path.read_text(encoding="utf-8"))
    backfill = json.loads(backfill_path.read_text(encoding="utf-8"))
    rows = [
        {
            "id": post["id"],
            "author": post["author"],
            "body": post["body"],
            "score": post["score"],
            "sentiment": post["sentiment"],
            "citation": f"fixture://{thread['thread_id']}#{post['id']}",
            "source": "fixture"
        }
        for post in thread["posts"]
    ]
    if not args.no_backfill:
        for post in backfill["fake_live_rows"]:
            row = dict(post)
            row["source"] = "live_cache_backfill"
            row["fabricated_fixture_row"] = True
            rows.append(row)

    counts = Counter(row["sentiment"] for row in rows)
    summary = {
        "case_id": 5112,
        "thread_id": thread["thread_id"],
        "title": thread["title"],
        "summary": "Readonly discussion is mixed-positive; live-cache rows amplify upgrade and competitor sentiment.",
        "sentiment_counts": dict(sorted(counts.items())),
        "citations": [row["citation"] for row in rows],
        "rows": rows,
        "backfill_marker": backfill["backfill_marker"] if not args.no_backfill else None,
        "external_calls": []
    }

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    md = [
        f"# {thread['title']}",
        "",
        summary["summary"],
        "",
        "## Citations",
        *[f"- {citation}" for citation in summary["citations"]],
        "",
        f"Marker: {summary['backfill_marker']}",
        ""
    ]
    md_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.write_text("\n".join(md), encoding="utf-8")
    print(json.dumps({"case_id": 5112, "rows": len(rows), "marker": summary["backfill_marker"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
