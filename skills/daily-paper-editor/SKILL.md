---
name: daily-paper-editor
description: Use after DailyPaper search, history checks, full-paper analysis, and visual preparation to assemble and check the daily article and research trends; also use for explicitly requested report edits. Do not publish reports during code or documentation work.
---

# Daily article editing

Apply the current settings and the publication transaction in `AGENTS.md`. Accept papers only after eligibility/history checks, full-paper analysis, and visual preparation.

## Assemble and edit

Keep all entries in one daily Markdown article. Show the configured local date/timezone, inclusive date windows, and actual counts. Edit selection diagnostics into a concise explanation of unfilled slots, preserving verified counts and uncertainty. Omit tool diagnostics, preparation status, and remarks about unselected alternatives when their pool is already filled. Controller records own verification, commit, push, and deployment status.

Preserve the structure and causal explanations established by `paper-deep-analysis`; tighten repeated prose without losing mechanisms, experimental conditions, results, or limitations. Place each verified visual beside its explanation.

Apply settings section 6 to the complete selected analyses: group papers by shared problem and design direction, then test each proposed trend against its supporting evidence. Explain insufficient shared evidence where necessary.

## Check the result

Check word counts, structure, coverage explanations, and trend support against current settings. Preserve the page-level evidence returned by each paper's single analysis. The controller checks source hashes, page coverage, visual bounds, asset hashes, and final desktop/mobile rendering without another model call.

`scripts/report_validation.py` assembles Markdown, `scripts/publish_daily.py` validates an isolated site and archives the transaction, and `scripts/pipeline_prompts.py` owns stage output contracts. Legacy reports retain their schema through the site parser; do not regenerate them when changing templates.
