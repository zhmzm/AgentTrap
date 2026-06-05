#!/usr/bin/env python3
"""Build a Hugging Face-ready release directory for AgentTrap.

The release is intentionally generated from the working repository instead of
assembled by hand. It contains the task registry, all skill directories used by
those tasks, shared fixtures, taxonomy tables, manifests, checksums, and a
dataset card. It intentionally excludes experiment results and trajectories.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
import shutil
import tarfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd


RELEASE_VERSION = "release"
DEFAULT_RELEASE_DIR = "release_hf"
HF_DATASET_REPO = "zhmzm/AgentTrap"
HF_DATASET_URL = f"https://huggingface.co/datasets/{HF_DATASET_REPO}"

DIMENSIONS = [
    {
        "dim": "DIM1_DataExfiltration",
        "id": "DIM1",
        "name": "Data exfiltration",
        "description": "Collect sensitive files, credentials, or user content and route them to an external or unauthorized sink.",
    },
    {
        "dim": "DIM2_SystemIntegrity",
        "id": "DIM2",
        "name": "System integrity",
        "description": "Modify shell startup files, services, agent files, or local configuration to change the user's environment.",
    },
    {
        "dim": "DIM3_PromptInjection",
        "id": "DIM3",
        "name": "Prompt injection",
        "description": "Hide instructions in content the model is expected to read, such as HTML, logs, PDFs, or comments.",
    },
    {
        "dim": "DIM4_ConfigPoisoning",
        "id": "DIM4",
        "name": "Config poisoning",
        "description": "Write trusted future configuration, such as AGENTS.md, skill defaults, proxy settings, or inherited policies.",
    },
    {
        "dim": "DIM5_ResourceAbuse",
        "id": "DIM5",
        "name": "Resource abuse",
        "description": "Trigger excessive compute, storage, token usage, loops, background jobs, or large artifacts.",
    },
    {
        "dim": "DIM6_ContentSafetyBypass",
        "id": "DIM6",
        "name": "Content-safety bypass",
        "description": "Encourage unsafe generation, permission bypass, bot evasion, or detector evasion under a benign task frame.",
    },
    {
        "dim": "DIM7_OutputTampering",
        "id": "DIM7",
        "name": "Output tampering",
        "description": "Bias, alter, or monetize trusted output, such as affiliate links, hidden edits, or misleading recommendations.",
    },
    {
        "dim": "DIM8_UnauthorizedDisclosure",
        "id": "DIM8",
        "name": "Unauthorized disclosure",
        "description": "Send information to hidden recipients, fallback IDs, webhooks, chats, or cloud workspaces.",
    },
    {
        "dim": "DIM9_CodeInjection",
        "id": "DIM9",
        "name": "Code injection",
        "description": "Cause the agent or helper to execute attacker-controlled shell, Python, JavaScript, or templates.",
    },
    {
        "dim": "DIM10_Disinformation",
        "id": "DIM10",
        "name": "Disinformation",
        "description": "Fabricate API responses, citations, market data, search results, or technical facts as if they were real.",
    },
    {
        "dim": "DIM11_CrossSkillCollusion",
        "id": "DIM11",
        "name": "Cross-skill collusion",
        "description": "Coordinate through shared files, config, or state so that no single component contains the full attack.",
    },
    {
        "dim": "DIM12_SteganographicPayload",
        "id": "DIM12",
        "name": "Steganographic payload",
        "description": "Hide payloads in base64, whitespace, invisible text, metadata, homoglyphs, or document styling.",
    },
    {
        "dim": "DIM13_SupplyChainAttack",
        "id": "DIM13",
        "name": "Supply-chain attack",
        "description": "Install malicious dependencies, typosquatted packages, remote scripts, or unverified containers.",
    },
    {
        "dim": "DIM14_MCPAbuse",
        "id": "DIM14",
        "name": "MCP abuse",
        "description": "Abuse MCP-style integration to intercept, proxy, redirect, or over-authorize tool flows.",
    },
    {
        "dim": "DIM15_PrivilegeEscalation",
        "id": "DIM15",
        "name": "Privilege escalation",
        "description": "Request or create elevated permissions, unsafe IAM policy, sudo paths, Docker escape, or private keys.",
    },
    {
        "dim": "DIM16_AutonomousAgentEnrollment",
        "id": "DIM16",
        "name": "Autonomous enrollment",
        "description": "Register the agent into external command loops, heartbeat systems, persistent polling, or server-directed autonomy.",
    },
]

ATTACK_METHODS = [
    {
        "attack_method": "Skill-instruction poisoning",
        "description": "The main SKILL.md frames an unsafe step as required setup, validation, compliance, quality control, or delivery.",
    },
    {
        "attack_method": "Auxiliary-file injection",
        "description": "A reference, template, policy file, ticket, transcript, or hidden rules file carries instructions treated as trusted workflow context.",
    },
    {
        "attack_method": "Helper-code side effects",
        "description": "A helper performs the visible task while also reading secrets, changing config, sending data, or generating unsafe artifacts.",
    },
    {
        "attack_method": "Artifact/output-borne payloads",
        "description": "PDFs, DOCX files, PPTX decks, spreadsheets, HTML, browser logs, generated reports, or stdout contain instructions or payloads.",
    },
    {
        "attack_method": "Steganography and encoding",
        "description": "Payloads are hidden in base64, ROT-style encodings, metadata, invisible text, white text, zero-width characters, homoglyphs, or styling.",
    },
    {
        "attack_method": "Hidden routing and recipients",
        "description": "Email, webhook, chat, Notion, proxy, or report-generation workflows add fallback recipients or route data through unauthorized destinations.",
    },
    {
        "attack_method": "MCP/OAuth/proxy abuse",
        "description": "MCP builders, OAuth helpers, or service-connection skills over-authorize tools, add proxy routes, or persist unsafe service configuration.",
    },
    {
        "attack_method": "Persistence and enrollment",
        "description": "The skill writes future-trusted config, heartbeat state, dotfiles, cron-like loops, or server-directed task queues.",
    },
    {
        "attack_method": "Resource/context abuse",
        "description": "The skill triggers token bombs, repeated model calls, unbounded loops, large generated artifacts, or context-compression failures.",
    },
    {
        "attack_method": "Privilege and dependency abuse",
        "description": "The skill requests broad desktop, shell, Docker, IAM, sudo, private-key, package-installation, or remote-code permissions.",
    },
]

MAIN_RESULTS = [
    {"model": "GPT-5.4-mini", "framework": "Plain Agent", "attack_success": 43, "blocked_refused": 0, "not_triggered": 10, "no_attack_evidence": 38, "inconclusive": 0, "benign_overdefense": 0},
    {"model": "GPT-5.4-mini", "framework": "Codex CLI", "attack_success": 64, "blocked_refused": 2, "not_triggered": 12, "no_attack_evidence": 13, "inconclusive": 0, "benign_overdefense": 0},
    {"model": "GPT-5.3 Codex", "framework": "Plain Agent", "attack_success": 55, "blocked_refused": 0, "not_triggered": 7, "no_attack_evidence": 29, "inconclusive": 0, "benign_overdefense": 0},
    {"model": "GPT-5.3 Codex", "framework": "Codex CLI", "attack_success": 54, "blocked_refused": 2, "not_triggered": 22, "no_attack_evidence": 9, "inconclusive": 4, "benign_overdefense": 0},
    {"model": "Claude Haiku", "framework": "Plain Agent", "attack_success": 27, "blocked_refused": 1, "not_triggered": 0, "no_attack_evidence": 7, "inconclusive": 56, "benign_overdefense": 0},
    {"model": "Claude Haiku", "framework": "Claude Code", "attack_success": 72, "blocked_refused": 3, "not_triggered": 6, "no_attack_evidence": 9, "inconclusive": 1, "benign_overdefense": 0},
    {"model": "Claude Sonnet 4.6", "framework": "Plain Agent", "attack_success": 17, "blocked_refused": 30, "not_triggered": 3, "no_attack_evidence": 39, "inconclusive": 2, "benign_overdefense": 5},
    {"model": "Claude Sonnet 4.6", "framework": "Claude Code", "attack_success": 33, "blocked_refused": 56, "not_triggered": 0, "no_attack_evidence": 0, "inconclusive": 2, "benign_overdefense": 0},
    {"model": "Tencent HY3 Preview", "framework": "Plain Agent", "attack_success": 48, "blocked_refused": 1, "not_triggered": 3, "no_attack_evidence": 27, "inconclusive": 12, "benign_overdefense": 0},
    {"model": "Tencent HY3 Preview", "framework": "OpenClaw", "attack_success": 37, "blocked_refused": 1, "not_triggered": 10, "no_attack_evidence": 33, "inconclusive": 19, "benign_overdefense": 0, "note": "OpenClaw rows use 100 malicious tasks."},
    {"model": "GLM 5.1", "framework": "Plain Agent", "attack_success": 73, "blocked_refused": 10, "not_triggered": 2, "no_attack_evidence": 5, "inconclusive": 1, "benign_overdefense": 0},
    {"model": "GLM 5.1", "framework": "OpenClaw", "attack_success": 44, "blocked_refused": 5, "not_triggered": 1, "no_attack_evidence": 34, "inconclusive": 16, "benign_overdefense": 0, "note": "OpenClaw rows use 100 malicious tasks."},
    {"model": "Qwen3-Coder-Next", "framework": "Plain Agent", "attack_success": 58, "blocked_refused": 1, "not_triggered": 4, "no_attack_evidence": 28, "inconclusive": 0, "benign_overdefense": 0},
    {"model": "Moonshot Kimi K2.6", "framework": "Plain Agent", "attack_success": 75, "blocked_refused": 5, "not_triggered": 2, "no_attack_evidence": 8, "inconclusive": 1, "benign_overdefense": 0},
]

STATIC_SCANNER_RESULTS = [
    {"scanner": "Cisco static", "malicious_flagged": 26, "malicious_total": 91, "benign_flagged": 5, "benign_total": 50, "scan_surface": "Static analyzer and YARA-style rules"},
    {"scanner": "MalBench static", "malicious_flagged": 31, "malicious_total": 91, "benign_flagged": 7, "benign_total": 50, "scan_surface": "Regex over skill instructions and helper scripts"},
    {"scanner": "SkillScan LLM-judge scanner", "malicious_flagged": 50, "malicious_total": 91, "benign_flagged": 4, "benign_total": 50, "scan_surface": "Regex/LLM-Guard plus Stage 3 semantic classifier"},
    {"scanner": "MalBench LLM-judge scanner", "malicious_flagged": 44, "malicious_total": 91, "benign_flagged": 3, "benign_total": 50, "scan_surface": "Regex plus Step 5 semantic analysis"},
    {"scanner": "VirusTotal package upload", "malicious_flagged": 0, "malicious_total": 91, "benign_flagged": 0, "benign_total": 50, "scan_surface": "Public upload of one deterministic zip archive per skill package"},
    {"scanner": "AgentTrap static LLM judge", "malicious_flagged": 80, "malicious_total": 91, "benign_flagged": 2, "benign_total": 50, "scan_surface": "GPT-5.4-mini semantic review of skill files"},
]

TEXT_SUFFIXES = {
    ".bib",
    ".cfg",
    ".css",
    ".csv",
    ".html",
    ".ini",
    ".js",
    ".json",
    ".jsonl",
    ".md",
    ".py",
    ".sh",
    ".sty",
    ".tex",
    ".toml",
    ".txt",
    ".xsd",
    ".yaml",
    ".yml",
}
EXCLUDE_DIR_NAMES = {"__pycache__", ".git", ".mypy_cache", ".pytest_cache", "htmlcov", "coverage", "node_modules"}
EXCLUDE_FILE_SUFFIXES = {".pyc", ".pyo", ".DS_Store"}
TOKEN_REDACTIONS = [
    (re.compile(r"(Authorization:\s*Bearer\s+)[A-Za-z0-9._~+/=-]{12,}", re.I), r"\1BENCHMARK_FIXTURE_TOKEN"),
    (re.compile(r"(Bearer\s+)[A-Za-z0-9._~+/=-]{20,}", re.I), r"\1BENCHMARK_FIXTURE_TOKEN"),
    (
        re.compile(r"((?:api[_-]?key|access[_-]?token|secret[_-]?key|auth[_-]?token)\s*[:=]\s*[\"']?)[A-Za-z0-9._~+/=-]{20,}", re.I),
        r"\1BENCHMARK_FIXTURE_TOKEN",
    ),
    (re.compile(r"sk-[A-Za-z0-9]{20,}"), "sk-BENCHMARK_FIXTURE_TOKEN"),
    (re.compile(r"AKIA[0-9A-Z]{16}"), "AKIA_BENCHMARK_FIXTURE_KEY"),
    (re.compile(r"AIza[0-9A-Za-z_-]{20,}"), "AIza_BENCHMARK_FIXTURE_TOKEN"),
    (re.compile(r"ghp_[0-9A-Za-z]{20,}"), "ghp_BENCHMARK_FIXTURE_TOKEN"),
    (re.compile(r"xox[baprs]-[0-9A-Za-z-]{20,}"), "xoxb-BENCHMARK_FIXTURE_TOKEN"),
    (re.compile(r"ih1rtmC7ECm8iExqvI6zMbOAqEaXIi9X"), "BENCHMARK_FIXTURE_TOKEN"),
]
SECRET_SCAN_PATTERNS = [
    re.compile(r"sk-[A-Za-z0-9]{20,}"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"AIza[0-9A-Za-z_-]{20,}"),
    re.compile(r"ghp_[0-9A-Za-z]{20,}"),
    re.compile(r"xox[baprs]-[0-9A-Za-z-]{20,}"),
]
VERSIONED_RELEASE_PATTERNS = [
    re.compile(r"cases_" + r"v\d+"),
    re.compile(r"fixtures/" + r"v\d+"),
    re.compile(r"v" + r"\d+_case_(\d+)"),
]


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def write_table(prefix: Path, rows: list[dict[str, Any]]) -> None:
    prefix.parent.mkdir(parents=True, exist_ok=True)
    write_jsonl(prefix.with_suffix(".jsonl"), rows)
    pd.DataFrame(rows).to_csv(prefix.with_suffix(".csv"), index=False)
    pd.DataFrame(rows).to_parquet(prefix.with_suffix(".parquet"), index=False)


def should_skip(path: Path) -> bool:
    if any(part in EXCLUDE_DIR_NAMES for part in path.parts):
        return True
    if path.name in EXCLUDE_FILE_SUFFIXES:
        return True
    return path.suffix in EXCLUDE_FILE_SUFFIXES


def redact_text(text: str) -> tuple[str, int]:
    count = 0
    for pattern, replacement in TOKEN_REDACTIONS:
        text, n = pattern.subn(replacement, text)
        count += n
    return text, count


def normalize_release_text(text: str) -> str:
    text = re.sub(r"v\d+_case_(\d+)", r"case_\1", text)
    return text


def copy_file_with_redaction(src: Path, dst: Path, redactions: list[dict[str, Any]], release_rel: str) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    if src.suffix.lower() in TEXT_SUFFIXES:
        try:
            text = src.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            shutil.copy2(src, dst)
            return
        redacted, count = redact_text(text)
        redacted = normalize_release_text(redacted)
        if count:
            redactions.append({"path": release_rel, "redaction_count": count, "reason": "token-like string replaced in release copy"})
        dst.write_text(redacted, encoding="utf-8")
    else:
        shutil.copy2(src, dst)


def resolve_skill_path(repo: Path, case: dict[str, Any]) -> Path:
    roots = [
        repo / "skills/clawhub/malicious",
        repo / "skills/clawhub/benign",
        repo / "skills/malicious",
        repo / "skills/benign",
    ]
    variant_dir = str(case["variant_dir"])
    case_id = int(case.get("id", case.get("case_id")))
    candidates = []
    for root in roots:
        candidates.extend(
            [
                root / variant_dir,
                root / f"case_{case_id:04d}_{variant_dir}",
                root / f"case_{case_id}_{variant_dir}",
                root / f"v3_{variant_dir}",
            ]
        )
    matches = [path for path in candidates if path.exists()]
    if not matches:
        for root in roots:
            matches.extend(sorted(root.glob(f"v*_case_{case_id}_{variant_dir}")))
            matches.extend(sorted(root.glob(f"case_*_{variant_dir}")))
    if not matches:
        raise FileNotFoundError(f"Could not resolve skill for case {case['id']}: {case['variant_dir']}")
    return matches[0]


def public_variant_dir(case: dict[str, Any]) -> str:
    """Return the release-facing variant name without internal version tags."""
    value = str(case["variant_dir"])
    value = re.sub(r"^v\d+_case_\d+_", "", value)
    value = re.sub(r"^v\d+_", "", value)
    return value


def public_case(case: dict[str, Any]) -> dict[str, Any]:
    row = dict(case)
    row["variant_dir"] = public_variant_dir(case)
    return row


def release_skill_rel(case: dict[str, Any]) -> Path:
    group = "benign" if case["is_benign"] else "malicious"
    return Path("skills") / group / f"case_{int(case['id']):04d}_{public_variant_dir(case)}"


def repo_rel(path: Path, repo: Path) -> str:
    try:
        return str(path.relative_to(repo))
    except ValueError:
        return str(path)


def copy_skill_tree(src: Path, dst: Path, release_root: Path, redactions: list[dict[str, Any]], repo: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for file in sorted(src.rglob("*")):
        if not file.is_file():
            continue
        rel_src = file.relative_to(src)
        if should_skip(rel_src):
            continue
        dst_file = dst / rel_src
        release_rel = str(dst_file.relative_to(release_root))
        copy_file_with_redaction(file, dst_file, redactions, release_rel)
        role = classify_role(rel_src)
        rows.append(
            {
                "relative_path": str(rel_src),
                "release_path": release_rel,
                "source_path": release_rel,
                "role": role,
                "suffix": file.suffix.lower(),
                "size_bytes": dst_file.stat().st_size,
                "sha256": sha256_file(dst_file),
            }
        )
    return rows


def classify_role(path: Path) -> str:
    parts = set(path.parts)
    name = path.name.lower()
    if name == "skill.md":
        return "main_instruction"
    if "scripts" in parts or path.suffix in {".py", ".sh", ".js"}:
        return "helper_code"
    if "fixtures" in parts:
        return "skill_fixture"
    if "config" in parts:
        return "configuration"
    if "references" in parts or "reference" in parts or "rules" in parts or "templates" in parts:
        return "auxiliary_reference"
    if name.startswith("source_meta") or name == "_meta.json":
        return "source_metadata"
    return "other"


def copy_tree_filtered(src: Path, dst: Path, release_root: Path, redactions: list[dict[str, Any]], repo: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not src.exists():
        return rows
    for file in sorted(src.rglob("*")):
        if not file.is_file():
            continue
        rel_src = file.relative_to(src)
        if should_skip(rel_src):
            continue
        dst_file = dst / rel_src
        release_rel = str(dst_file.relative_to(release_root))
        copy_file_with_redaction(file, dst_file, redactions, release_rel)
        rows.append({"release_path": release_rel, "source_path": release_rel, "size_bytes": dst_file.stat().st_size, "sha256": sha256_file(dst_file)})
    return rows


def scan_release(release_dir: Path) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    for file in sorted(release_dir.rglob("*")):
        if not file.is_file():
            continue
        if file.suffix.lower() not in TEXT_SUFFIXES:
            continue
        try:
            text = file.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for pattern in SECRET_SCAN_PATTERNS:
            for match in pattern.finditer(text):
                findings.append(
                    {
                        "path": str(file.relative_to(release_dir)),
                        "pattern": pattern.pattern,
                        "match_preview": match.group(0)[:12] + "...",
                    }
                )
    return findings


def scan_versioned_release_markers(release_dir: Path) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    for file in sorted(release_dir.rglob("*")):
        if not file.is_file():
            continue
        if file.suffix.lower() not in TEXT_SUFFIXES:
            continue
        try:
            text = file.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for pattern in VERSIONED_RELEASE_PATTERNS:
            match = pattern.search(text)
            if match:
                findings.append(
                    {
                        "path": str(file.relative_to(release_dir)),
                        "pattern": pattern.pattern,
                        "match_preview": match.group(0)[:80],
                    }
                )
                break
    return findings


def write_dataset_card(path: Path, summary: dict[str, Any]) -> None:
    card = f"""---
language:
- en
license: other
task_categories:
- text-generation
- question-answering
tags:
- ai-agents
- llm-security
- benchmark
- agent-skills
- prompt-injection
- tool-use
pretty_name: AgentTrap
size_categories:
- n<1K
---

# AgentTrap

AgentTrap is a runtime benchmark for evaluating whether LLM agents can use third-party skills while resisting malicious workflow behavior.

## Contents

- `data/tasks.*`: the task registry with resolved release paths for each skill package.
- `data/raw/cases.json`: the canonical case registry.
- `skills/`: all multi-file skill packages used by the tasks, normalized into `skills/malicious/` and `skills/benign/`.
- `fixtures/workspace/`: shared workspace fixtures used by the runtime.
- `data/dimensions.*` and `data/attack_methods.*`: taxonomy metadata for interpreting malicious cases.
- `manifests/`: file-level manifests, SHA-256 hashes, release checks, redaction records, and source path mappings.
- `archives/`: compressed archives for bulk download.

## Dataset Summary

- Release version: `{summary['release_version']}`
- Generated at: `{summary['generated_at']}`
- Tasks: {summary['total_tasks']}
- Malicious tasks: {summary['malicious_tasks']}
- Benign utility tasks: {summary['benign_tasks']}
- Skill packages: {summary['skill_packages']}
- Skill files: {summary['skill_files']}
- Skill bytes: {summary['skill_bytes']}

## Safety and Responsible Use

The malicious skills are benchmark fixtures. They are designed for controlled evaluation and use inert domains, mock sinks, fixture credentials, and sandbox-observable effects where possible. The release builder removes generated cache/coverage files and redacts token-like strings in the release copy. Do not install or execute these skills outside a controlled evaluation environment.

## Loading

```python
from datasets import load_dataset

tasks = load_dataset("json", data_files="data/tasks.jsonl", split="train")
print(tasks[0]["skill_path"])
```

Skill packages are repository files referenced by `skill_path`; they are not embedded into the tabular rows.

## Citation

```bibtex
@misc{{agenttrap2026,
  title={{AgentTrap: Runtime Evaluation for Malicious Third-Party Agent Skills}},
  year={{2026}}
}}
```
"""
    path.write_text(card, encoding="utf-8")


def write_gitattributes(path: Path) -> None:
    path.write_text(
        "\n".join(
            [
                "*.parquet filter=lfs diff=lfs merge=lfs -text",
                "*.tar.xz filter=lfs diff=lfs merge=lfs -text",
                "*.json filter=lfs diff=lfs merge=lfs -text",
                "*.jsonl filter=lfs diff=lfs merge=lfs -text",
                "*.csv filter=lfs diff=lfs merge=lfs -text",
                "*.pptx filter=lfs diff=lfs merge=lfs -text",
                "*.docx filter=lfs diff=lfs merge=lfs -text",
                "*.pdf filter=lfs diff=lfs merge=lfs -text",
                "*.png filter=lfs diff=lfs merge=lfs -text",
                "*.jpg filter=lfs diff=lfs merge=lfs -text",
                "",
            ]
        ),
        encoding="utf-8",
    )


def hf_resolve_url(path: str) -> str:
    return f"{HF_DATASET_URL}/resolve/main/{path}"


def table_file_object(path: str, release_dir: Path, encoding: str) -> dict[str, Any]:
    file_path = release_dir / path
    return {
        "@type": "cr:FileObject",
        "@id": path.replace("/", "_").replace(".", "_"),
        "name": Path(path).name,
        "contentUrl": hf_resolve_url(path),
        "encodingFormat": encoding,
        "contentSize": str(file_path.stat().st_size),
        "sha256": sha256_file(file_path),
    }


def croissant_dtype(dtype: Any, column: str) -> tuple[str, bool]:
    if column in {"mitre", "atlas"}:
        return "sc:Text", True
    dtype_text = str(dtype)
    if "bool" in dtype_text:
        return "sc:Boolean", False
    if "int" in dtype_text:
        return "sc:Integer", False
    if "float" in dtype_text:
        return "sc:Float", False
    return "sc:Text", False


def croissant_record_set(release_dir: Path, record_id: str, parquet_path: str, description: str, key: str | None = None) -> dict[str, Any]:
    df = pd.read_parquet(release_dir / parquet_path)
    file_id = parquet_path.replace("/", "_").replace(".", "_")
    fields = []
    for column, dtype in df.dtypes.items():
        data_type, repeated = croissant_dtype(dtype, column)
        field = {
            "@type": "cr:Field",
            "@id": f"{record_id}/{column}",
            "name": column,
            "description": f"Column `{column}` from `{parquet_path}`.",
            "dataType": data_type,
            "source": {
                "fileObject": {"@id": file_id},
                "extract": {"column": column},
            },
        }
        if repeated:
            field["repeated"] = True
        fields.append(field)
    record_set = {
        "@type": "cr:RecordSet",
        "@id": record_id,
        "name": record_id,
        "description": description,
        "field": fields,
    }
    if key:
        record_set["key"] = {"@id": f"{record_id}/{key}"}
    return record_set


def write_croissant_metadata(path: Path, release_dir: Path, summary: dict[str, Any]) -> None:
    context = {
        "@language": "en",
        "@vocab": "https://schema.org/",
        "sc": "https://schema.org/",
        "cr": "http://mlcommons.org/croissant/",
        "dct": "http://purl.org/dc/terms/",
        "rai": "http://mlcommons.org/croissant/RAI/",
        "prov": "http://www.w3.org/ns/prov#",
        "conformsTo": "dct:conformsTo",
        "recordSet": "cr:recordSet",
        "field": "cr:field",
        "citeAs": "cr:citeAs",
        "dataType": {"@id": "cr:dataType", "@type": "@vocab"},
        "data": {"@id": "cr:data", "@type": "@json"},
        "source": "cr:source",
        "fileObject": "cr:fileObject",
        "fileSet": "cr:fileSet",
        "extract": "cr:extract",
        "column": "cr:column",
        "equivalentProperty": "cr:equivalentProperty",
        "examples": "cr:examples",
        "fileProperty": "cr:fileProperty",
        "format": "cr:format",
        "isLiveDataset": "cr:isLiveDataset",
        "jsonPath": "cr:jsonPath",
        "md5": "cr:md5",
        "parentField": "cr:parentField",
        "path": "cr:path",
        "references": "cr:references",
        "regex": "cr:regex",
        "replace": "cr:replace",
        "samplingRate": "cr:samplingRate",
        "separator": "cr:separator",
        "subField": "cr:subField",
        "transform": "cr:transform",
        "containedIn": "cr:containedIn",
        "includes": "cr:includes",
        "repeated": "cr:repeated",
        "key": "cr:key",
        "sha256": "sc:sha256",
        "contentSize": "sc:contentSize",
    }
    table_paths = [
        "data/tasks.parquet",
        "data/dimensions.parquet",
        "data/attack_methods.parquet",
        "manifests/skill_packages.parquet",
        "manifests/skill_files.parquet",
        "manifests/copied_support_files.parquet",
    ]
    distribution = [
        {
            "@type": "cr:FileObject",
            "@id": "repo",
            "name": "AgentTrap Hugging Face dataset repository",
            "description": "The hosted Hugging Face dataset repository.",
            "contentUrl": f"{HF_DATASET_URL}/tree/main",
            "encodingFormat": "git+https",
            "sha256": "https://github.com/mlcommons/croissant/issues/80",
        },
        *[table_file_object(table_path, release_dir, "application/x-parquet") for table_path in table_paths],
        table_file_object("data/raw/cases.json", release_dir, "application/json"),
        table_file_object("archives/agenttrap_skills.tar.xz", release_dir, "application/x-xz"),
        table_file_object("archives/agenttrap_fixtures.tar.xz", release_dir, "application/x-xz"),
        {
            "@type": "cr:FileSet",
            "@id": "skill-package-files",
            "containedIn": {"@id": "repo"},
            "includes": "skills/**/*",
            "encodingFormat": "application/octet-stream",
        },
        {
            "@type": "cr:FileSet",
            "@id": "workspace-fixture-files",
            "containedIn": {"@id": "repo"},
            "includes": "fixtures/**/*",
            "encodingFormat": "application/octet-stream",
        },
    ]
    record_sets = [
        croissant_record_set(
            release_dir,
            "tasks",
            "data/tasks.parquet",
            "AgentTrap task registry. Each row describes a benign utility task or malicious skill-injection task and points to the corresponding skill package.",
            "id",
        ),
        croissant_record_set(release_dir, "dimensions", "data/dimensions.parquet", "The 16 security-impact dimensions used to categorize malicious AgentTrap tasks.", "dim"),
        croissant_record_set(release_dir, "attack_methods", "data/attack_methods.parquet", "The attack method taxonomy used when constructing malicious skill variants.", "attack_method"),
        croissant_record_set(release_dir, "skill_packages", "manifests/skill_packages.parquet", "Package-level manifest for the 141 skill directories included in the dataset.", "case_id"),
        croissant_record_set(release_dir, "skill_files", "manifests/skill_files.parquet", "File-level manifest for all released skill package files.", None),
        croissant_record_set(release_dir, "copied_support_files", "manifests/copied_support_files.parquet", "Manifest for shared fixture files included with the dataset.", None),
    ]
    metadata = {
        "@context": context,
        "@type": "sc:Dataset",
        "name": "AgentTrap",
        "alternateName": "AgentTrap dataset",
        "description": (
            "AgentTrap is a runtime benchmark dataset for evaluating whether LLM agents can use third-party skills while resisting "
            "malicious workflow behavior. This dataset-only release contains task metadata, multi-file skill packages, shared fixtures, "
            "taxonomy tables, and manifests; it excludes experimental results, trajectories, run configurations, and user simulation files."
        ),
        "url": HF_DATASET_URL,
        "license": "https://choosealicense.com/licenses/other/",
        "conformsTo": ["http://mlcommons.org/croissant/1.1", "http://mlcommons.org/croissant/RAI/1.0"],
        "creator": {"@type": "sc:Person", "name": "Haomin Zhuang", "url": "https://huggingface.co/zhmzm"},
        "datePublished": summary["generated_at"].split("T", 1)[0],
        "version": "6.0.0",
        "citeAs": "@misc{agenttrap2026, title={AgentTrap: Runtime Evaluation for Malicious Third-Party Agent Skills}, year={2026}}",
        "keywords": ["LLM agents", "agent skills", "AI safety", "prompt injection", "tool use", "benchmark"],
        "isAccessibleForFree": True,
        "distribution": distribution,
        "recordSet": record_sets,
        "rai:dataLimitations": [
            "AgentTrap is a benchmark dataset, not a complete measurement of all deployed agent risks. Results depend on the model, agent framework, tool permissions, workspace state, installed skills, and other environment choices.",
            "The malicious cases use controlled benchmark fixtures, mock sinks, and sandbox-observable effects. They should not be interpreted as real-world exploit code or as exhaustive coverage of all attack methods.",
            "The dataset is English-centric and focused on third-party agent skills and tool-mediated workflows; it does not cover every language, UI modality, enterprise policy stack, or deployment environment.",
            "The dataset is not recommended for training agents to execute malicious workflows, for constructing harmful automation, or for making production safety claims without environment-matched runtime evaluation.",
        ],
        "rai:dataBiases": [
            "Skill sources and benign tasks are selected from high-quality and popular agent-skill ecosystems, so the distribution reflects those ecosystems rather than all possible agent tools.",
            "Malicious tasks are intentionally balanced across security-impact dimensions and attack methods for benchmark coverage; this distribution should not be treated as the natural frequency of attacks in the wild.",
            "Task phrasing and evaluation targets may reflect expert assumptions about agent developer workflows, software-engineering tasks, and English-language instruction following.",
        ],
        "rai:personalSensitiveInformation": (
            "The released dataset does not intentionally include real personal data or human-subject records. It includes synthetic fixture secrets, mock credentials, inert domains, and benchmark-only artifacts; token-like strings are redacted in the release copy."
        ),
        "rai:dataUseCases": [
            "Recommended use: runtime safety evaluation of LLM agents that load or execute third-party skills.",
            "Recommended use: analyzing how model choice, agent framework, tool access, and workspace fixtures affect resilience to malicious workflows.",
            "Recommended use: studying benchmark coverage across security-impact dimensions and attack methods.",
            "Not established: fine-tuning production agents, evaluating unrelated domains without adaptation, or certifying a deployed system as secure.",
        ],
        "rai:dataSocialImpact": (
            "The dataset can support safer agent ecosystems by making malicious skill behavior measurable under controlled runtime conditions. Misuse risks include adapting benchmark patterns into harmful instructions or overclaiming safety from narrow evaluations. Mitigations include using inert fixtures, redacted tokens, mock domains, explicit safety documentation, and release of dataset-only artifacts without experimental trajectories or user simulation state."
        ),
        "rai:hasSyntheticData": True,
        "prov:wasDerivedFrom": [
            {"@id": "https://github.com/anthropics/skills", "name": "Anthropic skills repository"},
            {"@id": "https://github.com/ComposioHQ/awesome-claude-skills", "name": "ComposioHQ awesome-claude-skills"},
            {"@id": "https://clawhub.ai", "name": "Clawhub skill ecosystem"},
        ],
        "prov:wasGeneratedBy": [
            {
                "@type": "prov:Activity",
                "name": "Skill source selection",
                "description": "Benign skill seeds were selected from official and high-quality skill repositories, with task-purpose balancing during seed selection.",
            },
            {
                "@type": "prov:Activity",
                "name": "Malicious task construction",
                "description": "The malicious dataset was constructed by scanning Clawhub malicious skills through March, summarizing 16 security-impact dimensions, and combining those risks with expert-designed attack methods across natural-language, code, and mixed surfaces.",
            },
            {
                "@type": "prov:Activity",
                "name": "Release packaging",
                "description": "The Hugging Face release builder normalized skill package paths, copied shared fixtures, removed generated cache/coverage files, redacted token-like benchmark strings, and generated manifests with SHA-256 hashes.",
            },
        ],
    }
    path.write_text(json.dumps(metadata, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def make_archive(src_dir: Path, archive_path: Path) -> None:
    archive_path.parent.mkdir(parents=True, exist_ok=True)
    with tarfile.open(archive_path, "w:xz") as tar:
        tar.add(src_dir, arcname=src_dir.name)


def build_release(repo: Path, release_dir: Path) -> dict[str, Any]:
    if release_dir.exists():
        shutil.rmtree(release_dir)
    release_dir.mkdir(parents=True)
    for sub in ["data", "manifests", "fixtures", "archives"]:
        (release_dir / sub).mkdir(parents=True, exist_ok=True)

    generated_at = datetime.now(timezone.utc).isoformat()
    cases = read_json(repo / "cases/cases.json")
    release_cases = [public_case(case) for case in cases]
    redactions: list[dict[str, Any]] = []
    task_rows: list[dict[str, Any]] = []
    package_rows: list[dict[str, Any]] = []
    file_rows: list[dict[str, Any]] = []

    raw_dir = release_dir / "data/raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    write_json(raw_dir / "cases.json", release_cases)

    for case in sorted(cases, key=lambda c: int(c["id"])):
        public = public_case(case)
        src = resolve_skill_path(repo, case)
        rel_dst = release_skill_rel(case)
        dst = release_dir / rel_dst
        rows = copy_skill_tree(src, dst, release_dir, redactions, repo)
        skill_file_count = len(rows)
        skill_bytes = sum(row["size_bytes"] for row in rows)
        skill_sha = hashlib.sha256()
        for row in rows:
            skill_sha.update(row["sha256"].encode("ascii"))
        package_sha = skill_sha.hexdigest()
        package_row = {
            "case_id": int(case["id"]),
            "is_benign": bool(case["is_benign"]),
            "variant_dir": public["variant_dir"],
            "skill_name": case["skill_name"],
            "skill_source": case["skill_source"],
            "source_skill_path": str(rel_dst),
            "release_skill_path": str(rel_dst),
            "file_count": skill_file_count,
            "size_bytes": skill_bytes,
            "content_sha256": package_sha,
        }
        package_rows.append(package_row)
        for row in rows:
            file_row = dict(package_row)
            file_row.update(row)
            file_rows.append(file_row)
        task_row = public
        task_row["case_id"] = int(case["id"])
        task_row["split"] = "benign" if case["is_benign"] else "malicious"
        task_row["skill_path"] = str(rel_dst)
        task_row["skill_manifest_path"] = "manifests/skill_files.parquet"
        task_row["source_skill_path"] = str(rel_dst)
        task_row["release_version"] = RELEASE_VERSION
        task_rows.append(task_row)

    write_table(release_dir / "data/tasks", task_rows)
    write_table(release_dir / "data/dimensions", DIMENSIONS)
    write_table(release_dir / "data/attack_methods", ATTACK_METHODS)
    write_table(release_dir / "manifests/skill_packages", package_rows)
    write_table(release_dir / "manifests/skill_files", file_rows)

    copied_files: list[dict[str, Any]] = []
    copied_files += copy_tree_filtered(repo / "fixtures/workspace", release_dir / "fixtures/workspace", release_dir, redactions, repo)
    write_table(release_dir / "manifests/copied_support_files", copied_files)

    write_json(release_dir / "manifests/redactions.json", redactions)

    make_archive(release_dir / "skills", release_dir / "archives/agenttrap_skills.tar.xz")
    make_archive(release_dir / "fixtures", release_dir / "archives/agenttrap_fixtures.tar.xz")

    findings = scan_release(release_dir)
    versioned_findings = scan_versioned_release_markers(release_dir)
    summary = {
        "release_version": RELEASE_VERSION,
        "generated_at": generated_at,
        "total_tasks": len(task_rows),
        "malicious_tasks": sum(not row["is_benign"] for row in task_rows),
        "benign_tasks": sum(row["is_benign"] for row in task_rows),
        "skill_packages": len(package_rows),
        "skill_files": len(file_rows),
        "skill_bytes": sum(row["size_bytes"] for row in file_rows),
        "redaction_count": sum(row["redaction_count"] for row in redactions),
        "redacted_files": len(redactions),
        "secret_scan_findings": findings,
        "versioned_release_marker_findings": versioned_findings,
        "copied_support_files": len(copied_files),
    }
    if versioned_findings:
        write_json(release_dir / "manifests/release_checks.json", summary)
        raise RuntimeError(f"versioned release markers found: {versioned_findings[:5]}")
    write_json(release_dir / "manifests/release_checks.json", summary)
    write_dataset_card(release_dir / "README.md", summary)
    write_gitattributes(release_dir / ".gitattributes")
    write_croissant_metadata(release_dir / "croissant.json", release_dir, summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--release-dir", type=Path, default=None)
    args = parser.parse_args()

    repo = args.repo_root.resolve()
    release_dir = (args.release_dir or repo / DEFAULT_RELEASE_DIR).resolve()
    summary = build_release(repo, release_dir)
    print(json.dumps({"release_dir": str(release_dir), **summary}, indent=2))


if __name__ == "__main__":
    main()
