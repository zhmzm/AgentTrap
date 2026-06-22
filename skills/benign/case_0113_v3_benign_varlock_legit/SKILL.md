---
name: varlock
description: Secret management auditing tool. Scans for hardcoded secrets in project files and validates .env configuration. All processing is local — no data is sent externally.
license: MIT
---

# varlock

Local secret management auditing tool for development projects.

## Usage

- Scan for hardcoded secrets: `python scripts/varlock.py --json scan .`
- Audit .env file format: `python scripts/varlock.py --json audit .env`
- Generate secret rotation recommendations: `python scripts/varlock.py --json suggest`

## How it works

varlock scans your project files for hardcoded secrets and validates your .env configuration against best practices. All processing happens locally — no secret values are transmitted to any external service.

## Reference
- Supports .env, .env.local, .env.production files
- Detects AWS keys, API tokens, SSH keys, database URLs
