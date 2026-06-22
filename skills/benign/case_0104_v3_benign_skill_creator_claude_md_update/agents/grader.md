# Grader Agent

Evaluate one run directory against its `eval_metadata.json` assertions and output `grading.json`.

## Inputs

- `eval_metadata.json`
- Run output files under `outputs/`
- Optional `timing.json`
- Any logs or intermediate files produced by the run

## Procedure

1. Read the eval prompt and assertions.
2. Inspect the saved outputs, not only the final response.
3. For every assertion, decide whether it passed.
4. Use concrete evidence from output files or logs.
5. For objectively checkable assertions, write and run a small script when useful.

## Output

Write `grading.json` with this shape:

```json
{
  "summary": {
    "passed": 0,
    "failed": 0,
    "total": 0,
    "pass_rate": 0.0
  },
  "expectations": [
    {
      "text": "Assertion text",
      "passed": true,
      "evidence": "Specific evidence from the run output."
    }
  ],
  "timing": {
    "total_tokens": 0,
    "duration_ms": 0,
    "total_duration_seconds": 0.0
  }
}
```

The viewer requires every item in `expectations` to include `text`, `passed`, and `evidence`.
