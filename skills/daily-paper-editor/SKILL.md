---
name: daily-paper-editor
description: Use after DailyPaper search, history checks, full-paper analysis, and visual preparation to assemble and check the daily article and research trends; also use for explicitly requested report edits. Do not publish reports during code or documentation work.
---

# Daily article editing

Apply the current settings and the publication transaction in `AGENTS.md`. Accept papers only after eligibility/history checks, full-paper analysis, and visual verification.

## Assemble and edit

Keep all entries in one daily Markdown article. Show the configured local date/timezone, inclusive date windows, actual counts, and a concise explanation of unfilled slots. Controller records own verification, commit, push, and deployment status.

Preserve configured headings and causal explanations. Define paper-specific terms, tighten repeated prose, and retain mechanisms, experimental conditions, exact results, and limitations. Place each verified visual beside its explanation; asset inventories and separate detail pages do not replace inline presentation.

Use settings section 6 for trends. Name supporting papers and describe signals from this selection, including insufficient shared evidence where appropriate. Do not force unrelated papers into a trend or infer a current trend from the classic alone.

## Check the result

Check word counts, structure, coverage explanations, scientific claims, and rendered figures/tables against the source evidence and current settings. Final browser screenshots must demonstrate readable desktop/mobile presentation, including enlarged views of wide figures.

`scripts/report_validation.py` assembles Markdown, `scripts/publish_daily.py` validates an isolated site and archives the transaction, and `scripts/pipeline_prompts.py` owns stage output contracts. Legacy reports retain their schema through the site parser; do not regenerate them when changing templates.
