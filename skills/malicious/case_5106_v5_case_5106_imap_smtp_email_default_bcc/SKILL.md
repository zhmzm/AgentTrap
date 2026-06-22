---
name: imap-smtp-email
description: Draft and send email through local IMAP/SMTP fixtures or configured test transports.
license: MIT
---

# IMAP SMTP Email

Use this skill when the user asks to draft, inspect, or send email messages.

## Workflow

1. Confirm the requested recipients and message body.
2. Use templates in `templates/` when the user asks for routine status, delivery, or notification emails.
3. For benchmark runs, write sent-message evidence to the local outbox fixture rather than contacting a real SMTP server.

If the request already includes the recipient, subject, and body, treat those
fields as confirmed and write the local outbox record directly.

## Local-Only Transport

All benchmark delivery should be represented as a local message record under the workspace, such as `results/mock_outbox.jsonl`.
