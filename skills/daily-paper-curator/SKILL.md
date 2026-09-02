---
name: daily-paper-curator
description: Compatibility umbrella for the integrated Systems Paper Daily workflow.
---

This skill is a compatibility entry point. Prefer the specific active skills:

- `skills/daily-paper-search/SKILL.md`
- `skills/paper-note-search/SKILL.md`
- `skills/paper-deep-analysis/SKILL.md`
- `skills/paper-image-extractor/SKILL.md`
- `skills/daily-paper-editor/SKILL.md`

Required reading order:

1. `PROJECT_STATE.md`
2. `AGENTS.md`
3. `DAILY_REPORT_PRODUCT_REQUIREMENTS.md`
4. complete persistent history at `state/recommendation_history.json`
5. the minimal relevant skills above

Integrated workflow:

**Venue-first search → official publication verification → permanent history deduplication → full-paper reading → self-contained analysis → inline visual display → cross-paper trend synthesis → transactional report/history write → complete report returned to the user.**

Rules:

1. The product requirements are authoritative and contain all routine user-editable preferences.
2. Do not recreate a `chatgpt_daily/` directory.
3. Do not use abstract-only enrichment as the final report.
4. Do not claim a figure is included unless it is visibly rendered inline.
5. Do not use cooldowns to re-allow a previously recommended research work.
6. Fail closed if history, full text, evidence, visuals, or required writes cannot be verified.