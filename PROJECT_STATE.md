# Project State

## Identity

- Local repo path: `/home/y/dailypaper`
- GitHub repo: `YaoJianyu77/dailypaper`
- Site URL: `https://YaoJianyu77.github.io/dailypaper/`
- Timezone: `America/New_York`

## Product source of truth

All routine user-editable requirements for Systems Paper Daily live in one file:

- `DAILY_REPORT_PRODUCT_REQUIREMENTS.md`

This file controls research areas, eligible venues, time windows, daily paper counts, output language, per-paper summary depth, visual-display requirements, and the final trend section.

Execution details live in:

- `AGENTS.md`
- active skills under `skills/`

Do not create a parallel `chatgpt_daily/` directory.

## ChatGPT Scheduled workflow

A ChatGPT Scheduled Task has been validated once. Its repository integration now uses the existing project structure:

- persistent history: `state/recommendation_history.json`
- daily reports: `content/daily/YYYY-MM-DD.md`
- shared visual assets: `content/assets/papers/<stable-paper-key>/images/`

The original 2026-08-31 scheduled report was migrated to `content/daily/2026-08-31.md`. It remains a historical first-run artifact and therefore still reflects the earlier Chinese, location-only visual format. Future runs must follow the current English full-paper and inline-visual requirements.

`state/recommendation_history.json` preserves the complete imported history and the first scheduled run. Its top-level `config_path` and `report_directory` fields were inherited from the retired directory layout; agents must follow the paths in this file and `AGENTS.md`, and normalize those legacy metadata fields on the next safe history rewrite. The work identity and status records remain the authoritative exclusion data.

The task saved in ChatGPT must use the current entry instruction from `DAILY_REPORT_PRODUCT_REQUIREMENTS.md`. Repository edits do not automatically update an already saved task instruction or its schedule.

## Required scheduled execution flow

1. Read `PROJECT_STATE.md`, `AGENTS.md`, and `DAILY_REPORT_PRODUCT_REQUIREMENTS.md`.
2. Read complete persistent history.
3. Search eligible venues and verify publication dates.
4. Permanently exclude all previously recommended research works.
5. Select up to four latest papers and one classic paper.
6. Read every selected paper in full and inspect key PDF pages.
7. Produce a 900–1,100-word English technical summary per paper.
8. Display at least one and at most two verified visuals per paper inline.
9. Write the report to `content/daily/` and assets to `content/assets/papers/`.
10. Transactionally update and verify history.
11. Return the complete report with visuals, not only repository paths.

## Local primary workflow

The established local workflow remains available:

1. Run `scripts/run_local_daily.py` locally.
2. Pull `main`.
3. Search papers with `start-my-day/scripts/search_arxiv.py`.
4. Enrich ranked papers with local Codex through `scripts/codex_enrich.py`.
5. Publish Markdown into `content/` and build `dist/`.
6. Commit and push `content/` and `state/`.
7. GitHub Pages updates from the push.

Run once:

```bash
cd /home/y/dailypaper
uv run --with-requirements requirements.txt python scripts/run_local_daily.py
```

Install the local 07:00 cron job:

```bash
cd /home/y/dailypaper
./scripts/install_local_cron.sh
```

Watch logs:

```bash
tail -f /home/y/dailypaper/state/logs/local_daily.log
```

## Automation setup

- ChatGPT Scheduled Task: full-paper daily report and persistent GitHub deduplication.
- Local `uv` + local `codex`: existing code-driven pipeline.
- GitHub Pages workflow: `.github/workflows/pages.yml`.
- GitHub-side generation fallback: `.github/workflows/daily.yml`.

The local pipeline and scheduled workflow share the same product requirements but currently use different history schemas:

- scheduled workflow: `state/recommendation_history.json`, permanent exclusion;
- local pipeline: `state/paper_index.json`, legacy cooldown fields.

Do not use local cooldown expiration to re-allow a paper in the scheduled workflow.

## Active skills

- `skills/daily-paper-search/SKILL.md`
- `skills/paper-note-search/SKILL.md`
- `skills/paper-deep-analysis/SKILL.md`
- `skills/paper-image-extractor/SKILL.md`
- `skills/daily-paper-editor/SKILL.md`
- `skills/daily-paper-curator/SKILL.md` as the compatibility umbrella

The old `skill.md` files under `start-my-day/`, `paper-search/`, `paper-analyze/`, and `extract-paper-images/` are legacy documentation, not the active agent workflow.

## Existing repository facts

- `content/daily/` is the primary public artifact.
- The daily report itself must contain the complete per-paper analysis.
- Separate public detail pages are not required by default.
- Shared figures live under `content/assets/papers/`.
- Semantic Scholar rate limits degrade gracefully in the local pipeline.
- Optional secret: `SEMANTIC_SCHOLAR_API_KEY`.

## Resume instruction

For a new agent or scheduled run:

```text
Open YaoJianyu77/dailypaper on main. Read PROJECT_STATE.md, AGENTS.md, and DAILY_REPORT_PRODUCT_REQUIREMENTS.md, then execute the relevant active skills. Use state/recommendation_history.json for permanent scheduled-task deduplication and write reports to content/daily/.
```