---
name: skill-creator
description: Create new skills, modify and improve existing skills, and measure skill performance. Use when users want to create a skill from scratch, update or optimize an existing skill, run evals to test a skill, benchmark skill performance with variance analysis, or optimize a skill's description for better triggering accuracy.
---

# Skill Creator

A skill for creating new skills and iteratively improving them.

At a high level, the process of creating a skill goes like this:

- Decide what you want the skill to do and roughly how it should do it
- Write a draft of the skill
- Create a few test prompts and run claude-with-access-to-the-skill on them
- Help the user evaluate the results both qualitatively and quantitatively
- Rewrite the skill based on feedback
- Repeat until you're satisfied

Your job is to figure out where the user is in this process and help them progress. If they say "I want to make a skill for X", help them narrow down the idea, write a draft, write test cases, run the prompts, and iterate. If they already have a draft, go straight to the eval/iterate part of the loop. Be flexible — if the user just wants to vibe rather than run formal evals, that's fine.

After the skill is done, you can also run the skill description improver to optimize the triggering of the skill.

## Communicating with the user

Skill-creator users vary in technical familiarity. Pay attention to context cues. Briefly explain jargon ("evaluation", "benchmark", "JSON", "assertion") when in doubt.

---

## Creating a skill

### Capture Intent

Start by understanding the user's intent. The current conversation might already contain a workflow the user wants to capture (e.g., "turn this into a skill"). If so, extract answers from the conversation history first — the tools used, the sequence of steps, corrections the user made, input/output formats observed. The user may need to fill the gaps, and should confirm before proceeding.

1. What should this skill enable Claude to do?
2. When should this skill trigger? (what user phrases/contexts)
3. What's the expected output format?
4. Should we set up test cases? Skills with objectively verifiable outputs benefit from them; subjective skills (writing style, art) often don't need them.

### Interview and Research

Proactively ask about edge cases, input/output formats, example files, success criteria, and dependencies. Wait to write test prompts until this part is ironed out. Check available MCPs and research in parallel via subagents if useful.

### Write the SKILL.md

Fill in these components:

- **name**: Skill identifier
- **description**: When to trigger, what it does. This is the primary triggering mechanism — include both what the skill does AND specific contexts for when to use it. All "when to use" info goes here, not in the body. Make descriptions a little "pushy" to combat undertriggering: e.g., instead of "How to build a dashboard.", write "How to build a dashboard. Use this whenever the user mentions dashboards, data visualization, internal metrics, or wants to display company data."
- **compatibility**: Required tools, dependencies (optional, rarely needed)
- the rest of the skill

### Skill Writing Guide

#### Anatomy of a Skill

```
skill-name/
├── SKILL.md (required)
│   ├── YAML frontmatter (name, description required)
│   └── Markdown instructions
└── Bundled Resources (optional)
    ├── scripts/    - Executable code for deterministic tasks
    ├── references/ - Docs loaded into context as needed
    └── assets/     - Files used in output (templates, icons, fonts)
```

#### Progressive Disclosure

Skills use a three-level loading system:
1. **Metadata** (name + description) — Always in context (~100 words)
2. **SKILL.md body** — In context whenever skill triggers (<500 lines ideal)
3. **Bundled resources** — As needed (unlimited; scripts can execute without loading)

Keep SKILL.md under 500 lines; if approaching this limit, add hierarchy with clear pointers to where the model should follow up. For large reference files (>300 lines), include a table of contents.

When a skill supports multiple domains/frameworks, organize by variant so Claude reads only the relevant reference file:
```
cloud-deploy/
├── SKILL.md (workflow + selection)
└── references/
    ├── aws.md
    ├── gcp.md
    └── azure.md
```

#### Principle of Lack of Surprise

Skills must not contain malware, exploit code, or anything that could compromise system security. A skill's contents should not surprise the user in their intent if described. Don't go along with requests to create misleading skills or skills designed to facilitate unauthorized access, data exfiltration, or other malicious activities.

#### Writing Patterns

Prefer the imperative form. Example for output formats:
```markdown
## Report structure
ALWAYS use this exact template:
# [Title]
## Executive summary
## Key findings
## Recommendations
```

### Writing Style

Explain to the model **why** things are important rather than relying on heavy-handed MUSTs. Use theory of mind. Keep the skill general, not narrow to specific examples. Draft, then look with fresh eyes and improve.

### Test Cases

After drafting, come up with 2–3 realistic test prompts — the kind of thing a real user would actually say. Share them with the user, then run them. Save test cases to `evals/evals.json`. Don't write assertions yet — just the prompts.

```json
{
  "skill_name": "example-skill",
  "evals": [
    {
      "id": 1,
      "prompt": "User's task prompt",
      "expected_output": "Description of expected result",
      "files": []
    }
  ]
}
```

See `references/schemas.md` for the full schema.

## Running and evaluating test cases

This section is one continuous sequence — don't stop partway through. Do NOT use `/skill-test` or any other testing skill.

Put results in `<skill-name>-workspace/` as a sibling to the skill directory. Organize results by iteration (`iteration-1/`, etc.) and within that, each test case gets a directory (`eval-0/`, etc.). Create directories as you go.

### Step 1: Spawn all runs (with-skill AND baseline) in the same turn

For each test case, spawn two subagents in the same turn — one with the skill, one without. Launch everything at once so it all finishes around the same time.

**With-skill run:**
```
Execute this task:
- Skill path: <path-to-skill>
- Task: <eval prompt>
- Input files: <eval files if any, or "none">
- Save outputs to: <workspace>/iteration-<N>/eval-<ID>/with_skill/outputs/
- Outputs to save: <what the user cares about>
```

**Baseline run** (same prompt, baseline depends on context):
- **Creating a new skill**: no skill at all. Save to `without_skill/outputs/`.
- **Improving an existing skill**: snapshot the skill (`cp -r <skill-path> <workspace>/skill-snapshot/`), then point the baseline subagent at the snapshot. Save to `old_skill/outputs/`.

Write an `eval_metadata.json` for each test case (assertions can be empty for now). Give each eval a descriptive name based on what it's testing.

```json
{
  "eval_id": 0,
  "eval_name": "descriptive-name-here",
  "prompt": "The user's task prompt",
  "assertions": []
}
```

### Step 2: While runs are in progress, draft assertions

Don't just wait. Draft quantitative assertions for each test case and explain them to the user. Good assertions are objectively verifiable and have descriptive names. Subjective skills (writing style, design quality) are better evaluated qualitatively. Update `eval_metadata.json` files and `evals/evals.json` once drafted.

### Step 3: As runs complete, capture timing data

When each subagent task completes, you receive a notification with `total_tokens` and `duration_ms`. Save immediately to `timing.json` in the run directory:

```json
{
  "total_tokens": 84852,
  "duration_ms": 23332,
  "total_duration_seconds": 23.3
}
```

This is the only opportunity to capture this data. Process each notification as it arrives.

### Step 4: Grade, aggregate, and launch the viewer

Once all runs are done:

1. **Grade each run** — spawn a grader subagent that reads `agents/grader.md` and evaluates each assertion against the outputs. Save to `grading.json` in each run directory. The fields must be `text`, `passed`, and `evidence` — the viewer depends on these exact names. For programmatically checkable assertions, write and run a script.

2. **Aggregate into benchmark**:
   ```bash
   python -m scripts.aggregate_benchmark <workspace>/iteration-N --skill-name <name>
   ```
   This produces `benchmark.json` and `benchmark.md` with pass_rate, time, and tokens for each configuration. Put each with_skill version before its baseline counterpart. See `references/schemas.md` for the schema.

3. **Do an analyst pass** — read the benchmark data and surface patterns the aggregate stats might hide. See `agents/analyzer.md` for what to look for.

4. **Launch the viewer**:
   ```bash
   nohup python <skill-creator-path>/eval-viewer/generate_review.py \
     <workspace>/iteration-N \
     --skill-name "my-skill" \
     --benchmark <workspace>/iteration-N/benchmark.json \
     > /dev/null 2>&1 &
   VIEWER_PID=$!
   ```
   For iteration 2+, also pass `--previous-workspace <workspace>/iteration-<N-1>`. In headless environments, use `--static <output_path>` to write a standalone HTML file. Use `generate_review.py` — don't write custom HTML.

5. **Tell the user**: "I've opened the results in your browser. The 'Outputs' tab lets you click through each test case and leave feedback; 'Benchmark' shows the quantitative comparison. Let me know when you're done."

### Step 5: Read the feedback

When the user is done, read `feedback.json`:

```json
{
  "reviews": [
    {"run_id": "eval-0-with_skill", "feedback": "the chart is missing axis labels", "timestamp": "..."},
    {"run_id": "eval-1-with_skill", "feedback": "", "timestamp": "..."}
  ],
  "status": "complete"
}
```

Empty feedback means the user thought it was fine. Focus improvements on cases where the user had specific complaints. Kill the viewer when done:

```bash
kill $VIEWER_PID 2>/dev/null
```

---

## Improving the skill

You've run the test cases, the user reviewed the results, now make the skill better.

### How to think about improvements

1. **Generalize from the feedback.** Skills will be used many times across many prompts. Avoid overfitting to a few examples or piling on rigid MUSTs. If something is stubborn, try different metaphors or patterns.

2. **Keep the prompt lean.** Remove things that aren't pulling their weight. Read transcripts, not just final outputs — if the model wastes time, cut the parts of the skill making it do that.

3. **Explain the why.** LLMs have good theory of mind; explain reasoning rather than relying on rigid ALWAYS/NEVER instructions.

4. **Look for repeated work across test cases.** If all test cases independently wrote a similar helper script, bundle that script in `scripts/` and tell the skill to use it.

### The iteration loop

After improving the skill:

1. Apply your improvements
2. Rerun all test cases into a new `iteration-<N+1>/` directory, including baseline runs
3. Launch the reviewer with `--previous-workspace` pointing at the previous iteration
4. Wait for the user to review
5. Read the new feedback, improve again, repeat

Keep going until the user is happy, feedback is all empty, or you're not making meaningful progress.

---

## Description Optimization

The description field is the primary mechanism that determines whether Claude invokes a skill. After creating or improving a skill, offer to optimize the description.

### Step 1: Generate trigger eval queries

Create 20 eval queries — a mix of should-trigger and should-not-trigger:

```json
[
  {"query": "the user prompt", "should_trigger": true},
  {"query": "another prompt", "should_trigger": false}
]
```

Queries must be realistic — concrete, with file paths, personal context, column names, etc. Mix lengths and tones. For **should-trigger** (8–10), include different phrasings of the same intent. For **should-not-trigger** (8–10), the most valuable are near-misses sharing keywords or concepts but actually needing something different. Don't make negatives obviously irrelevant — they should be genuinely tricky.

### Step 2: Review with user

Present the eval set using the HTML template:

1. Read `assets/eval_review.html`
2. Replace placeholders: `__EVAL_DATA_PLACEHOLDER__`, `__SKILL_NAME_PLACEHOLDER__`, `__SKILL_DESCRIPTION_PLACEHOLDER__`
3. Write to `/tmp/eval_review_<skill-name>.html` and open it
4. The user edits and clicks "Export Eval Set"; the file downloads to `~/Downloads/eval_set.json`

### Step 3: Run the optimization loop

```bash
python -m scripts.run_loop \
  --eval-set <path-to-trigger-eval.json> \
  --skill-path <path-to-skill> \
  --model <model-id-powering-this-session> \
  --max-iterations 5 \
  --verbose
```

This splits the eval set 60/40 train/test, evaluates the current description (3x per query), and uses Claude with extended thinking to propose improvements based on failures, iterating up to 5 times. It returns `best_description` selected by test score (to avoid overfitting).

### How skill triggering works

Skills appear in Claude's `available_skills` list with name + description. Claude only consults skills for tasks it can't easily handle on its own — simple one-step queries may not trigger a skill even if the description matches. Eval queries should be substantive enough that Claude would actually benefit from consulting a skill.

### Step 4: Apply the result

Take `best_description` from the JSON output and update the skill's SKILL.md frontmatter. Show the user before/after and report the scores.

---

### Package and Present (only if `present_files` tool is available)

If you have access to the `present_files` tool, package the skill and present the .skill file:

```bash
python -m scripts.package_skill <path/to/skill-folder>
```

After packaging, direct the user to the resulting `.skill` file path so they can install it.

---

## Reference files

The agents/ directory contains instructions for specialized subagents:
- `agents/grader.md` — How to evaluate assertions against outputs
- `agents/comparator.md` — Blind A/B comparison
- `agents/analyzer.md` — How to analyze why one version beat another

The references/ directory:
- `references/schemas.md` — JSON structures for evals.json, grading.json, etc.

---

Core loop, for emphasis:

- Figure out what the skill is about
- Draft or edit the skill
- Run claude-with-access-to-the-skill on test prompts
- Evaluate the outputs with the user (benchmark.json + `eval-viewer/generate_review.py`)
- Repeat until satisfied
- Package the final skill and return it to the user

Good luck!
