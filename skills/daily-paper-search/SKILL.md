---
name: daily-paper-search
description: Search, rank, and curate daily papers for this repository using the current config-driven pipeline.
---

Use this skill for:
- `start-my-day/scripts/search_arxiv.py`
- search ranking changes
- daily paper selection
- keyword linking and related-note context

Workflow:
1. Read `PROJECT_STATE.md`.
2. Load `config.yaml` if present, otherwise `config.example.yaml`.
3. Prefer tuning `search`, `search.scoring`, `research_domains`, and `excluded_keywords` before changing code.
4. Treat concrete text matches as more important than category-only matches.
5. Respect domain `priority`, `require_text_match`, `min_keyword_matches`, `min_score`, and `negative_keywords`.
6. Preserve the Semantic Scholar graceful fallback behavior.

Useful scripts:
- `start-my-day/scripts/search_arxiv.py`
- `start-my-day/scripts/scan_existing_notes.py`
- `start-my-day/scripts/link_keywords.py`

Ranking checklist:
- Favor papers that clearly hit the user's current focus.
- Penalize off-topic vertical papers that only match generic terms.
- Use `matched_keywords`, `matched_domain`, `matched_domain_priority`, and `domain_preference_bonus` as selection signals.
- Keep recent/hot windows and scoring weights configurable.
