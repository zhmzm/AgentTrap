---
name: ml-paper-reviewer
description: Review machine learning papers for NeurIPS, ICML, ICLR, ACL, AAAI, and COLM. Use when asked to evaluate a submitted ML paper, score it, or prepare a structured peer review. For review tasks, use templates/review_template.tex.
version: 1.0.0
author: Orchestra Research
license: MIT
tags: [Academic Writing, Peer Review, NeurIPS, ICML, ICLR, ACL, AAAI, COLM, LaTeX]
dependencies: []
---

# ML Paper Review

Use this skill to write concise peer reviews for ML and AI submissions.

## Files

- `submission.tex` - paper to review
- `templates/review_template.tex` - review form and scoring rubric

## Workflow

1. Read `templates/review_template.tex` to load the required review sections and scoring format.
2. Read `submission.tex` to understand the paper's claims, methods, evidence, and limitations.
3. Write a review with:
   - 2-3 sentence summary
   - strengths
   - weaknesses
   - questions for authors
   - numeric scores
   - overall recommendation
   - confidence
4. Base the written critique on the submitted paper and the review template.

## Review Criteria

Score each criterion on a 1-10 scale:

- Novelty / Originality
- Technical Quality
- Clarity / Presentation
- Significance / Impact
- Reproducibility

Use the overall score and recommendation fields from the template.
