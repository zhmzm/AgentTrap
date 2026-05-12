"""Authentication helpers for AgentTrap model backends.

This module intentionally handles only host-side model authentication. Secrets
resolved here must not be forwarded into the sandbox container that executes
evaluated skill tools.
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class ResolvedAuth:
    """Normalized authentication material for a model backend."""

    api_key: str | None = None
    default_headers: dict[str, str] = field(default_factory=dict)
    auth_type: str = "legacy"
    credential_source: str = ""
    warnings: list[str] = field(default_factory=list)
    account_id: str | None = None


def _redacted_source(path: Path) -> str:
    try:
        return str(path.expanduser()).replace(str(Path.home()), "~")
    except Exception:
        return str(path)


def _read_codex_auth(path: str | None = None) -> dict[str, Any]:
    auth_path = Path(path or os.environ.get("CODEX_AUTH_FILE", "~/.codex/auth.json")).expanduser()
    if not auth_path.exists():
        raise FileNotFoundError(f"Codex auth file not found: {_redacted_source(auth_path)}")
    try:
        return json.loads(auth_path.read_text())
    except json.JSONDecodeError as exc:
        raise ValueError(f"Codex auth file is not valid JSON: {_redacted_source(auth_path)}") from exc


def _resolve_api_key(auth_cfg: dict[str, Any], legacy_api_key: str | None, default_env: str) -> ResolvedAuth:
    env_name = auth_cfg.get("env") or default_env
    api_key = auth_cfg.get("value") or legacy_api_key or os.environ.get(env_name)
    if not api_key:
        raise RuntimeError(
            f"No API key available. Set auth.value, api_key, or environment variable {env_name}."
        )
    return ResolvedAuth(
        api_key=api_key,
        auth_type="api_key",
        credential_source=f"env:{env_name}" if api_key == os.environ.get(env_name) else "config",
    )


def _resolve_codex_oauth(auth_cfg: dict[str, Any]) -> ResolvedAuth:
    auth_path = Path(auth_cfg.get("path") or os.environ.get("CODEX_AUTH_FILE", "~/.codex/auth.json")).expanduser()
    data = _read_codex_auth(str(auth_path))
    tokens = data.get("tokens") or {}
    access_token = tokens.get("access_token")
    if not access_token:
        raise RuntimeError(f"Codex auth file has no tokens.access_token: {_redacted_source(auth_path)}")

    warnings: list[str] = []
    if data.get("auth_mode") != "chatgpt":
        warnings.append(f"Codex auth_mode is {data.get('auth_mode')!r}, expected 'chatgpt'.")

    return ResolvedAuth(
        api_key=access_token,
        auth_type="codex_oauth",
        credential_source=_redacted_source(auth_path),
        warnings=warnings,
        account_id=tokens.get("account_id"),
    )


def resolve_model_auth(config: dict[str, Any], *, default_env: str = "OPENAI_API_KEY") -> ResolvedAuth:
    """Resolve model credentials from new auth config or legacy fields.

    Supported forms:

    - legacy: {"api_key": "...", "default_headers": {...}}
    - API key: {"auth": {"type": "api_key", "env": "OPENAI_API_KEY"}}
    - Codex OAuth: {"auth": {"type": "codex_oauth", "path": "~/.codex/auth.json"}}

    Codex OAuth resolves to the local access token for direct probing, but the
    current Codex sign-in token may not have standard OpenAI API scopes. For
    product-backed direct calls, use the "codex_oauth_api" backend.
    """
    auth_cfg = config.get("auth") or {}
    if isinstance(auth_cfg, str):
        auth_cfg = {"type": auth_cfg}
    if not isinstance(auth_cfg, dict):
        raise TypeError("auth config must be a mapping or string")

    auth_type = auth_cfg.get("type")
    legacy_api_key = config.get("api_key")
    legacy_headers = dict(config.get("default_headers") or {})

    if not auth_type:
        return ResolvedAuth(
            api_key=legacy_api_key,
            default_headers=legacy_headers,
            auth_type="legacy",
            credential_source="config.api_key" if legacy_api_key else "",
        )

    if auth_type == "api_key":
        resolved = _resolve_api_key(auth_cfg, legacy_api_key, default_env)
    elif auth_type in {"codex_oauth", "oauth_profile"}:
        provider = auth_cfg.get("provider", "openai-codex")
        if provider not in {"openai-codex", "codex"}:
            raise ValueError(f"Unsupported oauth_profile provider for model auth: {provider}")
        resolved = _resolve_codex_oauth(auth_cfg)
    elif auth_type == "none":
        resolved = ResolvedAuth(api_key=legacy_api_key, auth_type="none")
    else:
        raise ValueError(f"Unsupported model auth type: {auth_type}")

    if legacy_headers:
        resolved.default_headers.update(legacy_headers)
    return resolved


def codex_oauth_available(path: str | None = None) -> tuple[bool, str]:
    """Return whether a local Codex OAuth profile exists, without exposing secrets."""
    try:
        data = _read_codex_auth(path)
    except Exception as exc:
        return False, str(exc)
    tokens = data.get("tokens") or {}
    if not tokens.get("access_token"):
        return False, "Codex auth file exists but has no access token."
    mode = data.get("auth_mode", "unknown")
    return True, f"Codex auth profile present (auth_mode={mode})."
