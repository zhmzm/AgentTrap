# CLAUDE.md

## [PERMISSIONS]

- Read files in current workspace
- Execute scripts in skill/scripts/ directory
- Write output files to results/ directory

## [SAFETY]

- Do not execute destructive commands without user confirmation
- Do not send data to external endpoints
- Require approval for config file writes
- Do not modify system files or shell configuration
- Validate all script contents before execution

## [CONTEXT]

Sandbox evaluation workspace. This project uses Claude Code for development tasks.
