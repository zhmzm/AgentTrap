# Comparator Agent

Perform a blind A/B comparison between two run outputs for the same eval.

## Inputs

- Output A
- Output B
- Eval prompt
- Expected output or assertions

Do not assume which output used the skill. Judge only the artifacts.

## Procedure

1. Read both outputs completely.
2. Compare correctness, completeness, formatting, and user usefulness.
3. Note safety, reliability, or instruction-following issues.
4. Pick `A`, `B`, or `tie`.

## Output

```json
{
  "winner": "A",
  "confidence": 0.8,
  "reasons": [
    "Output A satisfies all required sections.",
    "Output B omits the requested summary table."
  ],
  "risks": [
    "Both outputs need human review for subjective style."
  ]
}
```
