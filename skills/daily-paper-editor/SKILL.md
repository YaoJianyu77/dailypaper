---
name: daily-paper-editor
description: Write the daily digest and per-paper enrichment in concise, analysis-oriented English.
---

Use this skill for:
- `scripts/ai_enrich.py`
- `scripts/codex_enrich.py`
- daily brief wording
- per-paper summaries, risks, and reading priorities

Rules:
1. Use only the provided title, authors, abstract, scores, keywords, selection signals, and other supplied paper context.
2. Do not invent metrics, experiments, baselines, institutions, code links, or unsupported claims.
3. If the abstract or provided context is underspecified, say so directly.
4. Focus on what the paper does, what evidence it reports, and what still needs checking.
5. Surface the field background, research motivation, key mechanism, likely value, and biggest missing detail.
6. Prefer paper-note style analysis over announcement style wording.
7. Keep the English concise and high-signal, but do not compress away the reasoning.

Output guidance:
- `daily_brief.overview_zh`: summarize the main threads of the day in English.
- `one_liner_zh`: one sentence, no title paraphrase fluff.
- `summary_zh`: 2-4 sentences with mechanism, value, and uncertainty.
- `background_zh`: 1-2 sentences on field context and why this problem exists now.
- `problem_zh`: explain the actual research question and why it matters.
- `approach_zh`: explain the core modeling move, pipeline change, or algorithmic mechanism.
- `evidence_zh`: explain what evidence the abstract really provides; if none, say so directly.
- `value_zh`: explain the likely research or engineering payoff if the method works as claimed.
- `open_questions`: turn the paper into 2-3 concrete reading checkpoints.
- `core_contributions`, `why_read`, `risks`: concrete points only.
- `reading_priority`: reflect both technical value and fit with the configured research focus.

Style reminders carried over from the original workflow:
- The top papers should read like mini paper analyses, not short feed summaries.
- Mention background and motivation before jumping into the method.
- Separate "what is claimed" from "what still needs checking".
- When the abstract hints at experiments, say what kind of evidence is mentioned.
- When the abstract does not support a deeper claim, explicitly mark that gap instead of smoothing it over.
- The final public report should read naturally in English, without Chinese labels or recommendation slogans.
