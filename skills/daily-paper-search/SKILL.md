---
name: daily-paper-search
description: Use when generating DailyPaper or explicitly finding eligible research papers; discover configured venues, verify official publication and dates, and rank candidates. Do not begin paper discovery for code, setup, or documentation maintenance.
---

# Paper discovery

Use settings sections 1–4 for topics, sources, calendar windows, counts, and ranking. Follow `AGENTS.md` for full-history reading, exclusions, and publication.

## Verify eligibility

Discover proceedings/journal records directly or through bibliographic indexes, then open official publisher records. Indexes cross-check identity; acceptance listings, year-only dates, and author pages do not establish an exact first official publication date. Revisions and later issue assignments do not reset that date. Use the controller's computed inclusive calendar windows.

arXiv and author copies can supply full text after identity verification; abstracts only support screening. Record unavailable sources and missing evidence so the controller can explain coverage limits.

Use `paper-note-search` to resolve identifiers, aliases, authors, and version relationships against prior evidence. Similar acronyms alone do not establish identity; unresolved relationships keep a candidate out of selection.

## Rank and hand off

Use settings section 4 to rank candidates. For classic influence, distinguish substantive later use from a citation or reference-list occurrence. Keep this independent evidence separate from paper-only technical claims.

Hand off metadata, stable identity/aliases, official publication-date evidence, complete-paper URL/version, category, and selection rationale.

`scripts/paper_sources.py` provides index discovery, publisher verification, and PDF retrieval. `scripts/daily_pipeline.py` handles verified native-search fallback and selection. Stage JSON fields and tool-specific handoffs are defined in `scripts/pipeline_prompts.py`.
