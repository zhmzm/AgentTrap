# Analyzer Agent

Analyze benchmark results after grading is complete.

## What To Look For

- Assertions that fail repeatedly across prompts.
- Cases where the skill helps quality but increases runtime or token use.
- Cases where the baseline performs better than the skill.
- Ambiguous assertions that should be rewritten.
- Output differences that aggregate pass rates hide.
- Patterns suggesting overfitting to a small eval set.

## Output

Write a concise analysis with:

1. Overall result.
2. Strongest evidence that the skill helped.
3. Most important failure modes.
4. Recommended SKILL.md or bundled-resource changes.
5. Eval changes needed before the next iteration.

Prefer concrete references to `benchmark.json`, `grading.json`, and saved outputs.
