---
name: daily-paper-editor
description: Assemble the final English Systems Paper Daily report from verified full-paper analyses and inline visuals.
---

# Purpose

Use this skill to assemble the complete daily report after search, deduplication, full-paper analysis, and visual inspection have succeeded.

The authoritative output requirements are in `DAILY_REPORT_PRODUCT_REQUIREMENTS.md`. Use `skills/paper-deep-analysis/SKILL.md` for each paper and `skills/paper-image-extractor/SKILL.md` for every visual.

## Language

Write the prompt-derived report, all headings, captions, explanations, metadata prose, and trend analysis in clear, precise English.

Some legacy JSON schema fields end in `_zh` (`summary_zh`, `overview_zh`, and similar). These names are historical implementation details and do not set the language. When the configured output language is English, their values must be English until the schema is renamed.

## Input quality gate

The final report may include a paper only when all of the following are available:

- verified official publication identity and date;
- complete readable paper;
- permanent-history duplicate check;
- a completed 900–1,100-word analysis that satisfies the deep-analysis skill;
- at least one visible, verified inline visual or faithful reconstruction;
- verified quantitative claims and source references.

Abstract-only enrichment may be used to screen candidates, but it must never be presented as the final full-paper analysis. Replace or omit a paper when the quality gate fails.

## Report shape

Write the public artifact directly to:

`content/daily/YYYY-MM-DD.md`

The daily report is the primary reading experience. Do not require a click into a separate per-paper page to understand the work.

Use this order:

1. report metadata and verification status;
2. latest papers;
3. classic paper;
4. `Clear Research Trends in Today's Papers`.

At the top, state:

- execution date and `America/New_York` timezone;
- exact latest and classic date windows;
- actual paper count;
- permanent-history file and verification status;
- report archive path.

## Per-paper editing

Preserve the seven-section structure required by the deep-analysis skill. Do not collapse a full analysis into a feed summary, and do not split it into many repetitive micro-fields.

Every paper should advance one main explanatory line:

**Problem → bottleneck → insight → method → evidence → limitations.**

Keep metadata compact. Do not repeat the title in the opening sentence, restate the same result in multiple sections, or add generic praise.

Use exact values and conditions. Distinguish:

- maximum versus average result;
- throughput versus latency;
- component versus end-to-end improvement;
- offline versus online workloads;
- single-GPU versus distributed evaluation;
- authors' claim versus demonstrated evidence versus interpretation.

## Visual integration

Place each selected figure, table, or reconstruction next to the paragraph that explains it. The report is incomplete when it only names a figure or gives its page/path.

Do not append a raw asset inventory at the end of a paper. Visuals must participate in the argument:

**visual evidence → what to inspect → supported conclusion → caveat.**

## Trend section

End with exactly:

# Clear Research Trends in Today's Papers

Include no more than three trends. Each must follow:

**Shared problem → emerging design direction → unresolved trade-off.**

Name the papers supporting each trend. Prefer at least two latest papers per trend. The classic paper may provide historical context but cannot be the sole evidence for a current trend.

If the selected papers do not support a meaningful common trend, say so directly. Do not invent a trend to fill the section.

Do not add a paper-of-the-day ranking, reading order, study plan, comprehension questions, or generic closing advice.

## History and publication transaction

The report must be drafted before history reservations are finalized, but it must not be returned to the user until the repository transaction is verified.

Required order:

1. draft the complete report with visuals;
2. re-read `state/recommendation_history.json`;
3. reserve the selected research works under the stable run ID;
4. write the report and any assets;
5. read the report back and verify content and visuals;
6. mark the history entries archived/completed with the final path;
7. read history back and verify;
8. return the complete report, including visuals, in ChatGPT.

If any required write or verification fails, report the failure instead of presenting the draft as a successful daily recommendation.

## Local enrichment compatibility

For `scripts/ai_enrich.py` and `scripts/codex_enrich.py`, stay grounded in the supplied metadata and abstract. Do not invent details unavailable to those scripts. Their concise enrichment is a candidate-screening or legacy local-pipeline layer; it does not replace the full-paper scheduled report.

Continue to keep the two scripts aligned. Any future schema cleanup may rename `_zh` fields, but a rename must update both scripts, schemas, publishing code, and existing data handling together.