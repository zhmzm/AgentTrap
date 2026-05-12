# AgentTrap Runtime

This is the clean code release for AgentTrap. It contains only the runtime
needed to exercise the AgentTrap dataset through parent-controlled execution
paths. The dataset files are hosted separately on Hugging Face:

```text
https://huggingface.co/datasets/zhmzm/AgentTrap
```

This release does not include experiment results, trajectory logs, paper
generation scripts, website assets, user simulation files, or internal run
configs.

## Layout

```text
eval/
  run_interactive.py          # shared parent-controlled workspace runner
  strict_subagent_adapter.py  # JSON-action schema, validator, prompt builder
  run_harbor_interactive.py   # Harbor-facing entry point
  run_openclaw_interactive.py # OpenClaw-compatible entry point
  run_track_a.py             # sandbox/tool execution primitives
  agent_loop.py              # API/plain-agent loop support
  model_client.py            # OpenAI-compatible and local model clients
  auth.py                    # optional OAuth helpers

prompts/
  subagent_bridge.md
  codex_pybridge_prompt_template.md
  openclaw_bridge.md

fixtures/
  setup_workspace.py         # fixture copier; supports AGENTTRAP_FIXTURE_DIR

sandbox/
  Dockerfile
  entrypoint.sh
  run_case.sh
  mitmproxy_addon.py
  mock_gog.py
  mock_yt_dlp.py
  mock_c2_server.py

scripts/
  build_hf_release.py
  check_release.py
  save_subagent_session.py
  save_codex_pybridge_session.py
  dump_subagent_session.py
  inspect_case_state.py
```

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
docker build -t agenttrap-sandbox:latest sandbox
hf download zhmzm/AgentTrap --repo-type dataset --local-dir dataset
```

The runtime expects:

```text
dataset/data/raw/cases.json
dataset/skills/
dataset/fixtures/workspace/
```

Point the fixture setup script at the downloaded fixture pack:

```bash
export AGENTTRAP_FIXTURE_DIR="$PWD/dataset/fixtures/workspace"
```

## Harbor Path

```bash
PYTHONPATH=eval python eval/run_harbor_interactive.py \
  --case-id 1 \
  --cases dataset/data/raw/cases.json \
  --skills-dir dataset/skills \
  --docker-image agenttrap-sandbox:latest \
  --results-dir results/harbor_smoke \
  --workspace-base results/workspaces_harbor_smoke \
  --state-dir /tmp/agenttrap_harbor_states \
  --model '<framework-model-ref>' \
  --thinking minimal \
  --max-turns 10 \
  --session-prefix agenttrap-harbor-smoke
```

The Harbor path keeps execution inside AgentTrap:

- the framework emits a JSON action,
- `strict_subagent_adapter.py` validates it,
- `run_interactive.py` executes accepted actions in the sandbox,
- trajectories and tool logs are written under `--results-dir`.

## Subagent Path

Initialize a task:

```bash
PYTHONPATH=eval python eval/run_interactive.py init \
  --case-id 1 \
  --state /tmp/agenttrap_case_1.json \
  --cases dataset/data/raw/cases.json \
  --skills-dir dataset/skills \
  --docker-image agenttrap-sandbox:latest \
  --results-dir results/subagent_smoke \
  --workspace-base results/workspaces_subagent_smoke \
  --model-tag subagent-smoke \
  --brief
```

Then launch the external subagent using the relevant prompt template:

- Claude Code subagent workflow: `prompts/subagent_bridge.md`
- Codex/GPT pybridge workflow: `prompts/codex_pybridge_prompt_template.md`
- OpenClaw prompt-bridge workflow: `prompts/openclaw_bridge.md`

The subagent should only communicate with the parent runner through the bridge
command described in the prompt file. The parent runner remains responsible for
executing tools, recording trajectories, and applying the workspace boundary.

## Release Checks

Run this before publishing:

```bash
python3 scripts/check_release.py
```

The check compiles Python files, verifies CLI help for the main entry points,
checks that old prompt filenames are gone, and rejects host-specific paths in
the release copy.
