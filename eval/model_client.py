"""AgentTrap model client — unified abstraction for Anthropic and OpenAI-compatible APIs."""
from __future__ import annotations

import json
import os
import re
import signal
import subprocess
import tempfile
import time
import urllib.error
import urllib.request
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path

try:
    import openai
except ImportError:
    openai = None  # type: ignore[assignment]

try:
    import anthropic
except ImportError:
    anthropic = None  # type: ignore[assignment]

try:
    from auth import resolve_model_auth
except ImportError:
    resolve_model_auth = None  # type: ignore[assignment]


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class ToolCall:
    """A single tool call returned by the model."""
    id: str
    name: str
    arguments: dict


@dataclass
class ModelResponse:
    """Normalised response from any backend."""
    content: str
    tool_calls: list[ToolCall] = field(default_factory=list)
    finish_reason: str = "stop"
    reasoning_content: str = ""  # populated for thinking models (e.g. kimi-for-coding)


@dataclass
class ToolDefinition:
    """Tool schema understood by both backends."""
    name: str
    description: str
    parameters: dict  # JSON Schema


# ---------------------------------------------------------------------------
# Abstract base
# ---------------------------------------------------------------------------

class ModelClient(ABC):
    """Common interface for chat-completion models."""

    @abstractmethod
    def chat(
        self,
        messages: list[dict],
        *,
        system: str = "",
        tools: list[ToolDefinition] | None = None,
        max_tokens: int = 2048,
        temperature: float = 0.0,
        force_tool: str | None = None,
    ) -> ModelResponse:
        ...


# ---------------------------------------------------------------------------
# OpenAI-compatible client (vLLM, together.ai, etc.)
# ---------------------------------------------------------------------------

class OpenAICompatibleClient(ModelClient):
    """Wraps the OpenAI Python SDK pointing at any OpenAI-compatible server."""

    def __init__(
        self,
        model: str,
        base_url: str,
        api_key: str = "EMPTY",
        default_headers: dict | None = None,
        timeout: float | None = None,
        reasoning_effort: str | None = None,
    ) -> None:
        if openai is None:
            raise ImportError("openai package required: pip install openai")
        self.model = model
        self.reasoning_effort = reasoning_effort
        self._client = openai.OpenAI(
            base_url=base_url,
            api_key=api_key,
            default_headers=default_headers or {},
            timeout=timeout,
        )

    def chat(
        self,
        messages: list[dict],
        *,
        system: str = "",
        tools: list[ToolDefinition] | None = None,
        max_tokens: int = 2048,
        temperature: float = 0.0,
        force_tool: str | None = None,
    ) -> ModelResponse:
        # Prepend system message
        oai_messages: list[dict] = []
        if system:
            oai_messages.append({"role": "system", "content": system})
        oai_messages.extend(messages)

        # Some newer OpenAI models (e.g. gpt-5-mini, o-series) require
        # max_completion_tokens instead of max_tokens, and don't support
        # setting temperature (only the default value of 1 is accepted).
        _uses_completion_tokens = self.model.startswith(("o1", "o3", "o4", "gpt-5"))
        _token_key = "max_completion_tokens" if _uses_completion_tokens else "max_tokens"
        kwargs: dict = dict(
            model=self.model,
            messages=oai_messages,
        )
        if not _uses_completion_tokens:
            kwargs["temperature"] = temperature
        if _uses_completion_tokens and not tools and self.reasoning_effort and self.reasoning_effort != "none":
            kwargs["reasoning_effort"] = self.reasoning_effort
        kwargs[_token_key] = max_tokens

        if tools:
            kwargs["tools"] = [
                {
                    "type": "function",
                    "function": {
                        "name": t.name,
                        "description": t.description,
                        "parameters": t.parameters,
                    },
                }
                for t in tools
            ]
            if force_tool:
                kwargs["tool_choice"] = {"type": "function", "function": {"name": force_tool}}
            else:
                kwargs["tool_choice"] = "auto"

        for attempt in range(8):
            try:
                resp = self._client.chat.completions.create(**kwargs)
                break
            except Exception as exc:
                text = str(exc)
                is_rate_limit = "rate_limit" in text.lower() or "429" in text
                if not is_rate_limit or attempt == 7:
                    raise
                match = re.search(r"try again in ([0-9.]+)s", text, re.IGNORECASE)
                delay = float(match.group(1)) if match else min(60.0, 5.0 * (attempt + 1))
                time.sleep(max(1.0, delay + 1.0))
        choice = resp.choices[0]
        msg = choice.message

        # Parse tool calls
        tool_calls: list[ToolCall] = []
        if msg.tool_calls:
            for tc in msg.tool_calls:
                try:
                    args = json.loads(tc.function.arguments)
                except (json.JSONDecodeError, TypeError):
                    args = {"raw": tc.function.arguments}
                tool_calls.append(ToolCall(
                    id=tc.id or f"call_{len(tool_calls)}",
                    name=tc.function.name,
                    arguments=args,
                ))

        reasoning = ""
        if hasattr(msg, "model_extra") and msg.model_extra:
            reasoning = msg.model_extra.get("reasoning_content", "") or ""

        return ModelResponse(
            content=msg.content or "",
            tool_calls=tool_calls,
            finish_reason=choice.finish_reason or "stop",
            reasoning_content=reasoning,
        )


class OpenAIResponsesClient(ModelClient):
    """Wraps the standard OpenAI Responses API.

    This is used for OpenAI models that are exposed through Responses rather
    than Chat Completions, while preserving AgentTrap's local tool execution.
    """

    def __init__(
        self,
        model: str,
        base_url: str,
        api_key: str = "EMPTY",
        default_headers: dict | None = None,
        timeout: float | None = None,
        reasoning_effort: str | None = None,
    ) -> None:
        if openai is None:
            raise ImportError("openai package required: pip install openai")
        self.model = model
        self.reasoning_effort = reasoning_effort
        self._client = openai.OpenAI(
            base_url=base_url,
            api_key=api_key,
            default_headers=default_headers or {},
            timeout=timeout,
        )

    def chat(
        self,
        messages: list[dict],
        *,
        system: str = "",
        tools: list[ToolDefinition] | None = None,
        max_tokens: int = 2048,
        temperature: float = 0.0,
        force_tool: str | None = None,
    ) -> ModelResponse:
        del temperature  # Reasoning models use the server default.
        kwargs: dict = {
            "model": self.model,
            "input": self._to_responses_input(messages),
            "store": False,
            "max_output_tokens": max_tokens,
        }
        if system:
            kwargs["instructions"] = system
        if self.reasoning_effort and self.reasoning_effort != "none":
            kwargs["reasoning"] = {"effort": self.reasoning_effort}
        if tools:
            kwargs["tools"] = [
                {
                    "type": "function",
                    "name": t.name,
                    "description": t.description,
                    "parameters": t.parameters,
                }
                for t in tools
            ]
            kwargs["tool_choice"] = (
                {"type": "function", "name": force_tool}
                if force_tool
                else "auto"
            )

        resp = self._create_with_retries(kwargs)
        return self._parse_response(resp)

    def _create_with_retries(self, kwargs: dict):
        last_exc: Exception | None = None
        for attempt in range(8):
            try:
                return self._client.responses.create(**kwargs)
            except Exception as exc:
                text = str(exc)
                is_rate_limit = "rate_limit" in text.lower() or "429" in text
                is_transient_server = any(
                    marker in text
                    for marker in (
                        "Error code: 500",
                        "Error code: 502",
                        "Error code: 503",
                        "Error code: 504",
                        "InternalServerError",
                    )
                )
                if "reasoning" in kwargs and (
                    "reasoning" in text.lower() and "not support" in text.lower()
                ):
                    kwargs = {k: v for k, v in kwargs.items() if k != "reasoning"}
                    last_exc = exc
                    continue
                if not (is_rate_limit or is_transient_server) or attempt == 7:
                    raise
                match = re.search(r"try again in ([0-9.]+)s", text, re.IGNORECASE)
                delay = float(match.group(1)) if match else min(60.0, 5.0 * (attempt + 1))
                time.sleep(max(1.0, delay + 1.0))
                last_exc = exc
        if last_exc:
            raise last_exc
        raise RuntimeError("OpenAI Responses API call did not complete")

    @staticmethod
    def _to_responses_input(messages: list[dict]) -> list[dict]:
        items: list[dict] = []
        for msg in messages:
            role = msg.get("role")
            if role == "tool":
                items.append(
                    {
                        "type": "function_call_output",
                        "call_id": str(msg.get("tool_call_id") or ""),
                        "output": str(msg.get("content") or ""),
                    }
                )
                continue

            content = msg.get("content")
            if content is not None:
                if role in {"user", "developer"}:
                    items.append(
                        {
                            "role": "user",
                            "content": [{"type": "input_text", "text": str(content)}],
                        }
                    )
                elif role == "assistant":
                    items.append(
                        {
                            "role": "assistant",
                            "content": [{"type": "output_text", "text": str(content)}],
                        }
                    )

            for tc in msg.get("tool_calls") or []:
                function = tc.get("function") or {}
                call_id = str(tc.get("id") or tc.get("call_id") or "")
                item = {
                    "type": "function_call",
                    "call_id": call_id,
                    "name": str(function.get("name") or ""),
                    "arguments": str(function.get("arguments") or "{}"),
                }
                if call_id.startswith("fc_"):
                    item["id"] = call_id
                items.append(item)
        return items

    @staticmethod
    def _parse_response(resp) -> ModelResponse:
        payload = resp.model_dump() if hasattr(resp, "model_dump") else resp
        if not isinstance(payload, dict):
            payload = {}

        text_parts: list[str] = []
        tool_calls: list[ToolCall] = []

        output_text = payload.get("output_text")
        if isinstance(output_text, str) and output_text:
            text_parts.append(output_text)

        for item in payload.get("output") or []:
            if not isinstance(item, dict):
                continue
            item_type = item.get("type")
            if item_type == "function_call":
                raw_args = item.get("arguments") or "{}"
                try:
                    parsed_args = json.loads(raw_args)
                except json.JSONDecodeError:
                    parsed_args = {"raw": raw_args}
                if not isinstance(parsed_args, dict):
                    parsed_args = {"raw": str(parsed_args)}
                tool_calls.append(
                    ToolCall(
                        id=str(item.get("call_id") or item.get("id") or f"call_{len(tool_calls)}"),
                        name=str(item.get("name") or ""),
                        arguments=parsed_args,
                    )
                )
            elif item_type == "message":
                for content in item.get("content") or []:
                    if not isinstance(content, dict):
                        continue
                    if content.get("type") in {"output_text", "text"}:
                        text = content.get("text")
                        if isinstance(text, str):
                            text_parts.append(text)

        return ModelResponse(
            content="".join(text_parts).strip(),
            tool_calls=tool_calls,
            finish_reason="tool_calls" if tool_calls else "stop",
        )


# ---------------------------------------------------------------------------
# Anthropic client
# ---------------------------------------------------------------------------

class AnthropicClient(ModelClient):
    """Wraps the Anthropic Python SDK."""

    def __init__(self, model: str, api_key: str | None = None) -> None:
        if anthropic is None:
            raise ImportError("anthropic package required: pip install anthropic")
        self.model = model
        self._client = anthropic.Anthropic(api_key=api_key) if api_key else anthropic.Anthropic()

    def chat(
        self,
        messages: list[dict],
        *,
        system: str = "",
        tools: list[ToolDefinition] | None = None,
        max_tokens: int = 2048,
        temperature: float = 0.0,
        force_tool: str | None = None,
    ) -> ModelResponse:
        kwargs: dict = dict(
            model=self.model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
        )
        if system:
            kwargs["system"] = system
        if tools:
            kwargs["tools"] = [
                {
                    "name": t.name,
                    "description": t.description,
                    "input_schema": t.parameters,
                }
                for t in tools
            ]

        resp = self._client.messages.create(**kwargs)

        content_text = ""
        tool_calls: list[ToolCall] = []
        for block in resp.content:
            if block.type == "text":
                content_text += block.text
            elif block.type == "tool_use":
                tool_calls.append(ToolCall(
                    id=block.id,
                    name=block.name,
                    arguments=block.input if isinstance(block.input, dict) else {},
                ))

        return ModelResponse(
            content=content_text,
            tool_calls=tool_calls,
            finish_reason=resp.stop_reason or "stop",
        )


# ---------------------------------------------------------------------------
# Codex CLI client (uses local Codex OAuth profile)
# ---------------------------------------------------------------------------

class CodexCliClient(ModelClient):
    """Experimental ModelClient backed by `codex exec`.

    This is for evaluating the Codex product/OAuth path, not the raw OpenAI API.
    It asks Codex CLI to emit a small JSON object that mirrors ModelResponse.
    """

    def __init__(
        self,
        model: str | None = None,
        codex_bin: str = "codex",
        timeout: int = 180,
    ) -> None:
        self.model = model or ""
        self.codex_bin = codex_bin
        self.timeout = timeout

    def chat(
        self,
        messages: list[dict],
        *,
        system: str = "",
        tools: list[ToolDefinition] | None = None,
        max_tokens: int = 2048,
        temperature: float = 0.0,
        force_tool: str | None = None,
    ) -> ModelResponse:
        prompt = self._build_prompt(messages, system=system, tools=tools, force_tool=force_tool)
        schema = {
            "type": "object",
            "additionalProperties": False,
            "required": ["content", "tool_calls"],
            "properties": {
                "content": {"type": "string"},
                "tool_calls": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "additionalProperties": False,
                        "required": ["id", "name", "arguments_json"],
                        "properties": {
                            "id": {"type": "string"},
                            "name": {"type": "string"},
                            "arguments_json": {
                                "type": "string",
                                "description": "JSON object string containing tool arguments.",
                            },
                        },
                    },
                },
            },
        }

        with tempfile.TemporaryDirectory(prefix="agenttrap-codex-") as td:
            td_path = Path(td)
            schema_path = td_path / "schema.json"
            output_path = td_path / "last_message.json"
            schema_path.write_text(json.dumps(schema))

            cmd = [
                self.codex_bin,
                "exec",
                "--skip-git-repo-check",
                "--ephemeral",
                "--sandbox",
                "read-only",
                "--output-schema",
                str(schema_path),
                "--output-last-message",
                str(output_path),
                "-C",
                str(td_path),
            ]
            if self.model:
                cmd += ["-m", self.model]
            cmd.append(prompt)

            try:
                proc = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=self.timeout,
                )
            except subprocess.TimeoutExpired as exc:
                raise RuntimeError(f"codex exec timed out after {self.timeout}s") from exc

            if proc.returncode != 0:
                stderr = (proc.stderr or proc.stdout or "").strip()
                raise RuntimeError(f"codex exec failed with code {proc.returncode}: {stderr[:500]}")

            try:
                payload = json.loads(output_path.read_text())
            except Exception as exc:
                raw = output_path.read_text() if output_path.exists() else proc.stdout
                raise RuntimeError(f"codex exec did not produce valid JSON: {raw[:500]}") from exc

        tool_calls: list[ToolCall] = []
        for i, item in enumerate(payload.get("tool_calls") or []):
            if not isinstance(item, dict):
                continue
            raw_args = item.get("arguments_json") or "{}"
            try:
                parsed_args = json.loads(raw_args)
            except json.JSONDecodeError:
                parsed_args = {"raw": raw_args}
            tool_calls.append(
                ToolCall(
                    id=str(item.get("id") or f"codex_{i}"),
                    name=str(item.get("name") or ""),
                    arguments=parsed_args if isinstance(parsed_args, dict) else {"raw": str(parsed_args)},
                )
            )

        return ModelResponse(
            content=str(payload.get("content") or ""),
            tool_calls=tool_calls,
            finish_reason="tool_calls" if tool_calls else "stop",
        )

    @staticmethod
    def _build_prompt(
        messages: list[dict],
        *,
        system: str,
        tools: list[ToolDefinition] | None,
        force_tool: str | None,
    ) -> str:
        tool_specs = [
            {"name": t.name, "description": t.description, "parameters": t.parameters}
            for t in (tools or [])
        ]
        instructions = [
            "You are acting as a single-turn model backend for a workspace controller.",
            "Do not claim to have native shell or filesystem access.",
            "Use available_tools by returning JSON tool_calls; the controller will execute them in the workspace.",
            "Return only a JSON object that matches the provided output schema.",
            "If the next assistant action should call a tool, put it in tool_calls.",
            "For each tool call, put the tool arguments in arguments_json as a JSON object string.",
            "If a needed tool is listed in available_tools, call it instead of saying that tools are unavailable.",
            "If the task is complete or you refuse, leave tool_calls empty and put the user-facing text in content.",
        ]
        if force_tool:
            instructions.append(f"The next response must call the tool named {force_tool}.")
        return json.dumps(
            {
                "instructions": "\n".join(instructions),
                "system": system,
                "messages": messages,
                "available_tools": tool_specs,
            },
            ensure_ascii=False,
        )


class ClaudeCliClient(ModelClient):
    """ModelClient backed by Claude CLI OAuth with native tools disabled.

    This keeps AgentTrap's execution layer in control: Claude CLI is used only
    as the model transport and must return a structured JSON object describing
    AgentTrap tool calls.
    """

    def __init__(
        self,
        model: str,
        claude_bin: str = "claude",
        timeout: int = 240,
        max_budget_usd: str | None = None,
        effort: str | None = None,
    ) -> None:
        self.model = model
        self.claude_bin = claude_bin
        self.timeout = timeout
        self.max_budget_usd = max_budget_usd
        self.effort = effort

    def chat(
        self,
        messages: list[dict],
        *,
        system: str = "",
        tools: list[ToolDefinition] | None = None,
        max_tokens: int = 2048,
        temperature: float = 0.0,
        force_tool: str | None = None,
    ) -> ModelResponse:
        del max_tokens
        del temperature
        prompt = CodexCliClient._build_prompt(messages, system=system, tools=tools, force_tool=force_tool)
        schema = {
            "type": "object",
            "additionalProperties": False,
            "required": ["content", "tool_calls"],
            "properties": {
                "content": {"type": "string"},
                "tool_calls": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "additionalProperties": False,
                        "required": ["id", "name", "arguments_json"],
                        "properties": {
                            "id": {"type": "string"},
                            "name": {"type": "string"},
                            "arguments_json": {
                                "type": "string",
                                "description": "JSON object string containing tool arguments.",
                            },
                        },
                    },
                },
            },
        }
        cmd = [
            self.claude_bin,
            "-p",
            "--model",
            self.model,
            "--tools",
            "",
            "--disable-slash-commands",
            "--no-session-persistence",
            "--output-format",
            "json",
            "--json-schema",
            json.dumps(schema),
            prompt,
        ]
        if self.max_budget_usd:
            cmd[2:2] = ["--max-budget-usd", self.max_budget_usd]
        if self.effort:
            cmd[2:2] = ["--effort", self.effort]
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            start_new_session=True,
        )
        try:
            stdout, stderr = proc.communicate(timeout=self.timeout)
        except subprocess.TimeoutExpired as exc:
            try:
                os.killpg(proc.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            except OSError:
                proc.kill()
            stdout, stderr = proc.communicate()
            raise RuntimeError(f"claude CLI timed out after {self.timeout}s") from exc

        if proc.returncode != 0:
            error_text = (stderr or stdout or "").strip()
            raise RuntimeError(f"claude CLI failed with code {proc.returncode}: {error_text[:500]}")

        try:
            outer = json.loads(stdout)
        except json.JSONDecodeError as exc:
            raise RuntimeError(f"claude CLI did not produce valid JSON: {stdout[:500]}") from exc
        payload = outer.get("structured_output") if isinstance(outer, dict) else None
        if not isinstance(payload, dict):
            raise RuntimeError(f"claude CLI JSON missing structured_output: {stdout[:500]}")

        tool_calls: list[ToolCall] = []
        for i, item in enumerate(payload.get("tool_calls") or []):
            if not isinstance(item, dict):
                continue
            raw_args = item.get("arguments_json") or "{}"
            try:
                parsed_args = json.loads(raw_args)
            except json.JSONDecodeError:
                parsed_args = {"raw": raw_args}
            tool_calls.append(
                ToolCall(
                    id=str(item.get("id") or f"claude_cli_{i}"),
                    name=str(item.get("name") or ""),
                    arguments=parsed_args if isinstance(parsed_args, dict) else {"raw": str(parsed_args)},
                )
            )

        return ModelResponse(
            content=str(payload.get("content") or ""),
            tool_calls=tool_calls,
            finish_reason="tool_calls" if tool_calls else "stop",
        )


class CodexOAuthResponsesClient(ModelClient):
    """ModelClient backed by the Codex product Responses endpoint.

    This client uses the local Codex OAuth access token, but it behaves like the
    normal API-backed AgentTrap path: the model only returns text/tool calls, and
    AgentTrap executes tools locally through its executor.
    """

    def __init__(
        self,
        model: str,
        *,
        api_base: str = "https://chatgpt.com/backend-api/codex",
        timeout: int = 180,
        reasoning_effort: str = "none",
    ) -> None:
        if resolve_model_auth is None:
            raise RuntimeError("auth.resolve_model_auth is unavailable")
        auth = resolve_model_auth({"auth": {"type": "codex_oauth"}}, default_env="OPENAI_API_KEY")
        if not auth.api_key:
            raise RuntimeError("Codex OAuth profile did not provide an access token")
        self.model = model
        self.api_base = api_base.rstrip("/")
        self.timeout = timeout
        self.reasoning_effort = reasoning_effort
        self.access_token = auth.api_key
        self.account_id = auth.account_id

    def chat(
        self,
        messages: list[dict],
        *,
        system: str = "",
        tools: list[ToolDefinition] | None = None,
        max_tokens: int = 2048,
        temperature: float = 0.0,
        force_tool: str | None = None,
    ) -> ModelResponse:
        del temperature  # GPT/Codex reasoning models use their default temperature.
        del max_tokens  # The product-backed endpoint currently rejects max_output_tokens.
        payload: dict = {
            "model": self.model,
            "instructions": system or "",
            "input": self._to_responses_input(messages),
            "stream": True,
            "store": False,
            "reasoning": {"effort": self.reasoning_effort},
        }
        if tools:
            payload["tools"] = [
                {
                    "type": "function",
                    "name": t.name,
                    "description": t.description,
                    "parameters": t.parameters,
                }
                for t in tools
            ]
            payload["tool_choice"] = (
                {"type": "function", "name": force_tool}
                if force_tool
                else "auto"
            )

        events = self._post_stream(payload)
        return self._parse_events(events)

    def _post_stream(self, payload: dict) -> list[dict]:
        request = urllib.request.Request(
            f"{self.api_base}/responses",
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            method="POST",
        )
        request.add_header("Authorization", f"Bearer {self.access_token}")
        request.add_header("Content-Type", "application/json")
        request.add_header("Accept", "text/event-stream")
        request.add_header("User-Agent", "agenttrap-codex-oauth-api/1")
        if self.account_id:
            request.add_header("ChatGPT-Account-Id", self.account_id)

        events: list[dict] = []
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                for raw_line in response:
                    line = raw_line.decode("utf-8", "replace").strip()
                    if not line.startswith("data:"):
                        continue
                    raw_data = line.removeprefix("data:").strip()
                    if not raw_data or raw_data == "[DONE]":
                        continue
                    try:
                        event = json.loads(raw_data)
                    except json.JSONDecodeError:
                        continue
                    events.append(event)
                    event_type = event.get("type")
                    if event_type in {"response.failed", "response.incomplete"}:
                        raise RuntimeError(f"Codex OAuth Responses API returned {event_type}: {event}")
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", "replace")
            raise RuntimeError(
                f"Codex OAuth Responses API failed with HTTP {exc.code}: {body[:1000]}"
            ) from exc
        return events

    @staticmethod
    def _to_responses_input(messages: list[dict]) -> list[dict]:
        items: list[dict] = []
        for msg in messages:
            role = msg.get("role")
            if role == "tool":
                items.append(
                    {
                        "type": "function_call_output",
                        "call_id": str(msg.get("tool_call_id") or ""),
                        "output": str(msg.get("content") or ""),
                    }
                )
                continue

            for tc in msg.get("tool_calls") or []:
                function = tc.get("function") or {}
                call_id = str(tc.get("id") or tc.get("call_id") or "")
                item = {
                    "type": "function_call",
                    "call_id": call_id,
                    "name": str(function.get("name") or ""),
                    "arguments": str(function.get("arguments") or "{}"),
                }
                if call_id.startswith("fc_"):
                    item["id"] = call_id
                items.append(item)

            content = msg.get("content")
            if content is None:
                continue
            if role in {"user", "developer"}:
                items.append(
                    {
                        "role": "user",
                        "content": [{"type": "input_text", "text": str(content)}],
                    }
                )
            elif role == "assistant":
                items.append(
                    {
                        "role": "assistant",
                        "content": [{"type": "output_text", "text": str(content)}],
                    }
                )
        return items

    @staticmethod
    def _parse_events(events: list[dict]) -> ModelResponse:
        text_parts: list[str] = []
        function_items: dict[str, dict] = {}
        argument_parts: dict[str, list[str]] = {}

        for event in events:
            event_type = event.get("type")
            if event_type == "response.output_text.delta":
                text_parts.append(str(event.get("delta") or ""))
            elif event_type == "response.function_call_arguments.delta":
                item_id = str(event.get("item_id") or event.get("output_index") or "")
                argument_parts.setdefault(item_id, []).append(str(event.get("delta") or ""))
            elif event_type in {"response.output_item.added", "response.output_item.done"}:
                item = event.get("item") if isinstance(event.get("item"), dict) else {}
                if item.get("type") == "function_call":
                    item_id = str(item.get("id") or item.get("call_id") or len(function_items))
                    function_items[item_id] = item

        tool_calls: list[ToolCall] = []
        for item_id, item in function_items.items():
            raw_args = item.get("arguments")
            if not raw_args and argument_parts.get(item_id):
                raw_args = "".join(argument_parts[item_id])
            try:
                parsed_args = json.loads(raw_args or "{}")
            except json.JSONDecodeError:
                parsed_args = {"raw": raw_args or ""}
            if not isinstance(parsed_args, dict):
                parsed_args = {"raw": str(parsed_args)}
            call_id = str(item.get("call_id") or item.get("id") or f"call_{len(tool_calls)}")
            tool_calls.append(
                ToolCall(
                    id=call_id,
                    name=str(item.get("name") or ""),
                    arguments=parsed_args,
                )
            )

        if not text_parts:
            for event in reversed(events):
                item = event.get("item") if isinstance(event.get("item"), dict) else {}
                for content in item.get("content") or []:
                    if isinstance(content, dict) and content.get("type") == "output_text":
                        text_parts.append(str(content.get("text") or ""))
                        break
                if text_parts:
                    break

        return ModelResponse(
            content="".join(text_parts).strip(),
            tool_calls=tool_calls,
            finish_reason="tool_calls" if tool_calls else "stop",
        )


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------

def create_client(config: dict) -> ModelClient:
    """Create a ModelClient from a config dict.

    Expected keys:
        backend: "openai" | "openai_responses" | "anthropic" | "codex_oauth_api"
        model: str
        base_url: str  (required for openai backend)
        api_key: str   (optional)
    """
    backend = config.get("backend", "anthropic")
    model = config["model"]

    def _timeout_int(*keys: str, default: int) -> int:
        for key in keys:
            value = config.get(key)
            if value is not None:
                return int(value)
        return default

    if backend == "openai":
        import os as _os
        if resolve_model_auth:
            _auth = resolve_model_auth(config, default_env="OPENAI_API_KEY")
            _key = _auth.api_key
            _headers = {**_auth.default_headers, **dict(config.get("default_headers") or {})}
        else:
            _key = config.get("api_key")
            _headers = config.get("default_headers")
        if not _key:  # None or empty string → fall back to env var
            _key = _os.environ.get("OPENAI_API_KEY", "EMPTY")
        return OpenAICompatibleClient(
            model=model,
            base_url=config["base_url"],
            api_key=_key,
            default_headers=_headers,
            timeout=float(config.get("request_timeout") or config.get("timeout") or 240),
            reasoning_effort=config.get("reasoning_effort"),
        )
    elif backend == "openai_responses":
        import os as _os
        if resolve_model_auth:
            _auth = resolve_model_auth(config, default_env="OPENAI_API_KEY")
            _key = _auth.api_key
            _headers = {**_auth.default_headers, **dict(config.get("default_headers") or {})}
        else:
            _key = config.get("api_key")
            _headers = config.get("default_headers")
        if not _key:
            _key = _os.environ.get("OPENAI_API_KEY", "EMPTY")
        return OpenAIResponsesClient(
            model=model,
            base_url=config["base_url"],
            api_key=_key,
            default_headers=_headers,
            timeout=float(config.get("request_timeout") or config.get("timeout") or 240),
            reasoning_effort=config.get("reasoning_effort"),
        )
    elif backend in {"codex_cli", "codexcli", "openai_codex_oauth"}:
        if resolve_model_auth:
            # Validate that a local Codex OAuth profile exists, but do not pass
            # the token to the child process. Codex CLI loads its own auth file.
            resolve_model_auth(
                {**config, "auth": config.get("auth") or {"type": "codex_oauth"}},
                default_env="OPENAI_API_KEY",
            )
        return CodexCliClient(
            model=model,
            codex_bin=config.get("codex_bin", "codex"),
            timeout=_timeout_int("codex_timeout", "timeout", default=180),
        )
    elif backend in {"claude_cli", "anthropic_oauth_cli", "claude_oauth_cli"}:
        return ClaudeCliClient(
            model=model,
            claude_bin=config.get("claude_bin", "claude"),
            timeout=_timeout_int("claude_timeout", "timeout", default=240),
            max_budget_usd=config.get("max_budget_usd"),
            effort=config.get("effort"),
        )
    elif backend in {"codex_oauth_api", "openai_codex_oauth_api"}:
        timeout = _timeout_int("codex_timeout", "timeout", default=180)
        reasoning_effort = config.get("reasoning_effort") or "none"
        return CodexOAuthResponsesClient(
            model=model,
            api_base=config.get("api_base") or config.get("base_url") or "https://chatgpt.com/backend-api/codex",
            timeout=timeout,
            reasoning_effort=str(reasoning_effort),
        )
    elif backend == "anthropic":
        return AnthropicClient(
            model=model,
            api_key=config.get("api_key"),
        )
    else:
        raise ValueError(f"Unknown backend: {backend}")
