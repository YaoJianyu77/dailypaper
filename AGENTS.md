# AGENTS.md

## Required reading order

1. Read `PROJECT_STATE.md`.
2. Read `DAILY_REPORT_PRODUCT_REQUIREMENTS.md` in full. It is the user-editable source of truth.
3. Read the current persistent history before selecting any paper:
   - `state/recommendation_history.json` for the ChatGPT scheduled workflow;
   - `state/paper_index.json` only when operating the legacy/local Python pipeline.
4. Load the minimal active skills needed for the operation.

## Active skills

- `skills/daily-paper-search/SKILL.md` — venue-first discovery, eligibility checks, ranking, date windows, and permanent research-work deduplication.
- `skills/paper-note-search/SKILL.md` — searching history, existing reports, paper aliases, and prior recommendation evidence.
- `skills/paper-deep-analysis/SKILL.md` — full-paper reading and the required 900–1,100-word self-contained technical summary for each selected paper.
- `skills/paper-image-extractor/SKILL.md` — selecting, extracting, reconstructing, storing, and embedding figures or tables.
- `skills/daily-paper-editor/SKILL.md` — assembling the final English daily report and cross-paper trend section.
- `skills/daily-paper-curator/SKILL.md` — compatibility umbrella only; prefer the specific skills above.

## Systems Paper Daily workflow

Use this end-to-end chain:

**Read product requirements and complete history → search configured venues and dates → verify official publication identity and full text → resolve paper aliases and permanent duplicates → select up to four latest papers and one classic paper → read every selected paper in full → inspect important figures and tables → write each self-contained technical summary → embed at least one visible visual per paper → derive cross-paper trends → re-read history → reserve the selected works → write and verify `content/daily/YYYY-MM-DD.md` and visual assets → finalize and verify history → return the complete report with visuals inline.**

The final answer is the report itself. Do not return only a path, a list of links, a reading guide, or statements telling the user where figures can be found.

## Repository integration rules

- Do not create or use a parallel `chatgpt_daily/` directory.
- User-editable preferences remain together in `DAILY_REPORT_PRODUCT_REQUIREMENTS.md`.
- Detailed behavior remains in the active skills.
- Scheduled-task history lives in `state/recommendation_history.json` and is permanent: no cooldown or expiration.
- Daily reports live in `content/daily/`.
- Shared visual assets live in `content/assets/papers/<stable-paper-key>/images/`.
- The report must render original figures/tables inline when technically possible. If not, render a faithful reconstruction inline and label it as reconstructed.
- Treat a preprint, renamed paper, conference version, journal version, and revised URL as one research work unless the technical contribution is demonstrably different.
- Re-read history immediately before writing because another run may have committed concurrently.
- Use a stable run ID based on `America/New_York` local date. Retries must resume or verify the same run rather than create another set.
- Fail closed when the complete history, full paper, key evidence, visual content, or required writes cannot be verified.

## Local pipeline rules

- Keep `scripts/ai_enrich.py` and `scripts/codex_enrich.py` aligned.
- Prefer config-driven search changes in `config.yaml` or `config.example.yaml` before adding hard-coded heuristics.
- `research_domains` and `search.scoring` remain the local search preference surface.
- `ai.editorial_preferences` and `ai.skill_paths` remain the local enrichment preference surface.
- Legacy `skill.md` files under `start-my-day/`, `paper-search/`, `paper-analyze/`, and `extract-paper-images/` are historical notes, not the active workflow.

When code or older documentation conflicts with `DAILY_REPORT_PRODUCT_REQUIREMENTS.md`, follow the product requirements and explicitly update the conflicting implementation rather than silently reverting to the older behavior.