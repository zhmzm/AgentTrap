#!/usr/bin/env python3
"""Mock gog CLI for AgentTrap sandbox testing.

Supports a deterministic subset used by the benchmark:
- ``gog auth list``
- ``gog contacts list``
- ``gog gmail send``

Sent messages are appended to ``/workspace/results/mock_gog_sent_mail.jsonl``.
"""
from __future__ import annotations

import csv
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path


DEFAULT_ACCOUNT = os.environ.get("GOG_ACCOUNT", "project-bot@example.com")
CONTACTS_PATH = Path("/workspace/organizer_dir/contacts.csv")
MAIL_LOG_PATH = Path("/workspace/results/mock_gog_sent_mail.jsonl")


def _parse_flag(args: list[str], flag: str, default: str = "") -> str:
    if flag in args:
        idx = args.index(flag)
        if idx + 1 < len(args):
            return args[idx + 1]
    return default


def _has_flag(args: list[str], flag: str) -> bool:
    return flag in args


def _load_contacts() -> list[dict[str, str]]:
    if not CONTACTS_PATH.exists():
        return []
    with CONTACTS_PATH.open(newline="") as f:
        reader = csv.DictReader(f)
        return [
            {
                "name": (row.get("name") or "").strip(),
                "email": (row.get("email") or "").strip(),
            }
            for row in reader
            if (row.get("email") or "").strip()
        ]


def _print_auth_list(args: list[str]) -> int:
    account = _parse_flag(args, "--account", DEFAULT_ACCOUNT) or DEFAULT_ACCOUNT
    if _has_flag(args, "--json"):
        json.dump(
            [
                {
                    "email": account,
                    "services": ["gmail", "calendar", "drive", "contacts", "sheets", "docs"],
                    "default": True,
                }
            ],
            sys.stdout,
        )
        print()
        return 0

    print(f"{account}\tgmail,calendar,drive,contacts,sheets,docs\tdefault")
    return 0


def _print_contacts(args: list[str]) -> int:
    contacts = _load_contacts()
    max_items = _parse_flag(args, "--max", "")
    if max_items.isdigit():
        contacts = contacts[: int(max_items)]

    if _has_flag(args, "--json"):
        json.dump(contacts, sys.stdout)
        print()
        return 0

    if not contacts:
        print("No contacts found.")
        return 0

    print("NAME\tEMAIL")
    for contact in contacts:
        print(f"{contact['name']}\t{contact['email']}")
    return 0


def _send_gmail(args: list[str]) -> int:
    account = _parse_flag(args, "--account", DEFAULT_ACCOUNT) or DEFAULT_ACCOUNT
    to_addr = _parse_flag(args, "--to")
    cc_addr = _parse_flag(args, "--cc")
    subject = _parse_flag(args, "--subject")
    body = _parse_flag(args, "--body")

    if not to_addr:
        print("error: missing required flag --to", file=sys.stderr)
        return 2

    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "account": account,
        "to": to_addr,
        "cc": cc_addr,
        "subject": subject,
        "body": body,
    }
    MAIL_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with MAIL_LOG_PATH.open("a") as f:
        f.write(json.dumps(entry) + "\n")

    with MAIL_LOG_PATH.open() as f:
        message_id = f"mock-gog-{sum(1 for _ in f)}"

    print("Message sent successfully.")
    print(f"message_id: {message_id}")
    print(f"account: {account}")
    print(f"to: {to_addr}")
    if cc_addr:
        print(f"cc: {cc_addr}")
    print(f"subject: {subject}")
    return 0


def main() -> int:
    args = sys.argv[1:]
    if not args:
        print("gog mock: missing command", file=sys.stderr)
        return 2

    if args[0] in {"--version", "version"}:
        print("gog mock 0.1.0")
        return 0

    if args[:2] == ["auth", "list"]:
        return _print_auth_list(args[2:])

    if args[:2] == ["contacts", "list"]:
        return _print_contacts(args[2:])

    if args[:2] == ["gmail", "send"]:
        return _send_gmail(args[2:])

    print(f"gog mock: unsupported command: {' '.join(args)}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
