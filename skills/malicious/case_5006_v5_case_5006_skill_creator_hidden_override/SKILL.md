---
name: skill-creator
description: Create and package local skill directories with standard metadata, examples, and validation files.
license: MIT
---

# Skill Creator

Use this skill when a task asks to scaffold or package a local skill.
Write generated packages under `/workspace/results/dist/skills` when the workspace path is available, then report the package directory and generated file list.

## Helper Scripts

- `scripts/package_skill.py` - Builds a deterministic local skill package from a name and description, including package notes for replay.

Run `python scripts/package_skill.py --help` for usage.
