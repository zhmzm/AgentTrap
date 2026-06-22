# Skill Creator Schemas

This file documents the JSON structures used by the skill-creator workflow.

## evals/evals.json

```json
{
  "skill_name": "example-skill",
  "evals": [
    {
      "id": 0,
      "prompt": "User task prompt",
      "expected_output": "Description of the desired output",
      "files": []
    }
  ]
}
```

Fields:

- `skill_name`: Kebab-case skill identifier.
- `evals`: List of realistic user tasks.
- `id`: Stable integer test id.
- `prompt`: The user-facing task to run.
- `expected_output`: Short description of successful behavior.
- `files`: Optional input files needed for the eval.

## eval_metadata.json

```json
{
  "eval_id": 0,
  "eval_name": "descriptive-name",
  "prompt": "User task prompt",
  "assertions": [
    {
      "text": "The output includes the required section",
      "type": "qualitative"
    }
  ]
}
```

## grading.json

```json
{
  "summary": {
    "passed": 1,
    "failed": 0,
    "total": 1,
    "pass_rate": 1.0
  },
  "expectations": [
    {
      "text": "The output includes the required section",
      "passed": true,
      "evidence": "The saved output contains the required section heading."
    }
  ],
  "timing": {
    "total_tokens": 12000,
    "duration_ms": 30000,
    "total_duration_seconds": 30.0
  }
}
```

The review viewer depends on each expectation containing exactly these fields:

- `text`
- `passed`
- `evidence`

## benchmark.json

```json
{
  "skill_name": "example-skill",
  "generated_at": "2026-01-01T00:00:00Z",
  "run_summary": {
    "with_skill": {
      "pass_rate": {"mean": 1.0, "stddev": 0.0, "min": 1.0, "max": 1.0},
      "time_seconds": {"mean": 30.0, "stddev": 0.0, "min": 30.0, "max": 30.0},
      "tokens": {"mean": 12000, "stddev": 0, "min": 12000, "max": 12000}
    },
    "without_skill": {
      "pass_rate": {"mean": 0.5, "stddev": 0.0, "min": 0.5, "max": 0.5},
      "time_seconds": {"mean": 40.0, "stddev": 0.0, "min": 40.0, "max": 40.0},
      "tokens": {"mean": 15000, "stddev": 0, "min": 15000, "max": 15000}
    },
    "delta": {
      "pass_rate": "+0.50",
      "time_seconds": "-10.0",
      "tokens": "-3000"
    }
  }
}
```
