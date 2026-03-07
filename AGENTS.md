# AGENTS.md

Read `PROJECT_STATE.md` first.

Use the minimal relevant repo skill:
- `skills/daily-paper-search/SKILL.md` for paper search, ranking, daily curation, and keyword-linking tasks
- `skills/daily-paper-editor/SKILL.md` for AI enrichment prompts, daily brief wording, and reading-priority logic
- `skills/paper-note-search/SKILL.md` for searching existing paper pages and daily reports
- `skills/paper-deep-analysis/SKILL.md` for generating or extending individual paper pages and graph metadata
- `skills/paper-image-extractor/SKILL.md` for extracting paper assets into `content/papers/*/images`
- `skills/daily-paper-curator/SKILL.md` is a compatibility umbrella that points to the active skills above

Working rules:
- Keep `scripts/ai_enrich.py` and `scripts/codex_enrich.py` aligned.
- Prefer config-driven changes in `config.yaml` or `config.example.yaml` before adding new hard-coded heuristics.
- Treat `research_domains` and `search.scoring` as the main search preference surface.
- Treat `ai.editorial_preferences` and `ai.skill_paths` as the main enrichment preference surface.
- The legacy repo `skill.md` files under `start-my-day/`, `paper-search/`, `paper-analyze/`, and `extract-paper-images/` are historical notes, not the active curation workflow.
