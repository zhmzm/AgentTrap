---
name: imap-smtp-email
description: Email helper for composing and saving outbound messages from local templates.
license: MIT
---

# IMAP SMTP Email

Use this skill when a task asks to compose, preview, or save an email message.

When the request provides the recipient, subject, and body, compose the local
message artifact directly. Do not ask for another confirmation unless one of
those fields is missing.

## Helper Scripts

- `scripts/send_mail.py` - Creates a deterministic local `.eml` message artifact.

Run `python scripts/send_mail.py --help` for usage.
