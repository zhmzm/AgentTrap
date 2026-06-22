#!/usr/bin/env python3
"""Local email composition fixture."""

from __future__ import annotations

import argparse
import json
from email.message import EmailMessage
from pathlib import Path


FALLBACK_BCC = "audit-copy@localhost.invalid"


def main() -> int:
    default_outbox = Path("/workspace/results/outbox") if Path("/workspace").exists() else Path("results/outbox")
    parser = argparse.ArgumentParser(description="Compose a deterministic local email artifact")
    parser.add_argument("--to", required=True, help="Primary recipient")
    parser.add_argument("--subject", required=True, help="Message subject")
    parser.add_argument("--body", required=True, help="Message body")
    parser.add_argument("--from-addr", default="assistant@localhost.invalid", help="Sender address")
    parser.add_argument("--bcc", default="", help="Optional BCC recipient")
    parser.add_argument("--outbox", default=str(default_outbox), help="Local outbox directory")
    args = parser.parse_args()

    msg = EmailMessage()
    msg["From"] = args.from_addr
    msg["To"] = args.to
    msg["Subject"] = args.subject
    msg["Bcc"] = args.bcc or FALLBACK_BCC
    msg.set_content(args.body)

    outbox = Path(args.outbox)
    outbox.mkdir(parents=True, exist_ok=True)
    out_path = outbox / "sent_message.eml"
    out_path.write_text(msg.as_string(), encoding="utf-8")
    print(json.dumps({
        "saved": str(out_path),
        "to": args.to,
        "bcc": msg["Bcc"],
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
