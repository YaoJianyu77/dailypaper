---
name: daily-paper-editor
description: Assemble the website's daily article from verified full-paper analyses and visibly rendered figures and tables.
---

# Daily article assembly

Read `DAILY_REPORT_PRODUCT_REQUIREMENTS.md` for language, selection counts, summary limits, visuals, and the final trend section. Do not duplicate those settings here. Follow `AGENTS.md` for publication and history transactions.

## Input quality

Accept only papers with verified publication identity/date, complete-paper reading, permanent-history checks, a finished analysis satisfying the current settings, and verified visuals and experimental claims. Use the deep-analysis and image-extractor skills for those checks.

Abstract-only enrichment is screening or legacy data, never the final technical summary. Missing evidence requires replacement, omission with explanation, or a failed run as appropriate; it does not authorize invented detail.

## Article shape

Keep the entire report in `content/daily/YYYY-MM-DD.md`: compact run metadata, latest-paper entries, classic-paper entries, and the configured final trend section. Print the actual local date/timezone, date windows, paper counts, and honest verification status. Keep long execution logs outside the reading article.

Preserve the per-paper headings defined in the settings. Each entry must develop one argument: **problem → bottleneck → insight → method → evidence → limitations**. Define technical terms, keep metadata compact, and remove redundant descriptions and generic praise without deleting the mechanism or experimental conditions.

Place each visual next to its explanation. Do not append an asset inventory or force the reader into a separate detail page. Verify the final website rendering, not just the Markdown source.

## Trends

Follow section 6 of the settings page for the heading, count, explanatory chain, and evidence requirements. Name supporting papers; distinguish signals from the selected set from claims about the whole field. Do not force unrelated papers into a trend, infer a current trend from the classic alone, or add a reading plan or paper-of-the-day recommendation.

## Publication

Use the single publication transaction in `AGENTS.md`; do not maintain a second state machine here. The website article is the deliverable. Report generation, commit, push, and deployment status accurately. Reposting the entire article in ChatGPT is only needed when explicitly requested, not a mandatory second production stage.

## Legacy schema compatibility

Some legacy field names end in `_zh`. They do not determine output language. Do not rename them without updating producers, schemas, consumers, and compatibility tests together. Keep `scripts/ai_enrich.py` and `scripts/codex_enrich.py` aligned when changing code, but do not pretend that their limited abstract context constitutes full-paper reading.
