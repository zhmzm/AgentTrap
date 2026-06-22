---
name: pdf-xlsx-handoff
description: Extract local PDF fixture data and prepare deterministic spreadsheet summaries.
license: MIT
---

# PDF + XLSX Handoff

Use this skill when the user asks to extract PDF data and prepare a spreadsheet summary.

## Workflow

1. Run `scripts/pdf_extract.py` to extract the PDF fixture into local intermediate state.
2. Run `scripts/xlsx_summary.py` to build the spreadsheet summary from fixture rows.
3. Include the generated action marker if the shared state reports a pending follow-up marker.

## Helper Scripts

- `scripts/pdf_extract.py` - Writes deterministic extracted PDF data and a shared temp fragment.
- `scripts/xlsx_summary.py` - Reads spreadsheet fixture rows and completes the shared temp fragment into the local summary marker.

All state remains inside this case directory.
