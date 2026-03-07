---
name: daily-paper-editor
description: Write the daily digest and per-paper enrichment in concise high-signal Simplified Chinese.
---

Use this skill for:
- `scripts/ai_enrich.py`
- `scripts/codex_enrich.py`
- daily brief wording
- per-paper summaries, risks, and reading priorities

Rules:
1. Use only the provided title, authors, abstract, scores, keywords, and selection signals.
2. Do not invent metrics, experiments, baselines, institutions, code links, or unsupported claims.
3. If the abstract is underspecified, say so directly.
4. Explain why the paper is worth reading now, not just what it does.
5. Surface the key mechanism, likely value, and biggest missing detail.
6. Keep Simplified Chinese concise, direct, and information-dense.

Output guidance:
- `daily_brief.overview_zh`: summarize the main threads of the day and suggest reading order.
- `one_liner_zh`: one sentence, no title paraphrase fluff.
- `summary_zh`: 2-4 sentences with mechanism, value, and uncertainty.
- `core_contributions`, `why_read`, `risks`: concrete points only.
- `reading_priority`: reflect both technical value and fit with the configured research focus.
