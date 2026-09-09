---
name: daily-paper-search
description: Use when generating DailyPaper or explicitly finding eligible research papers; discover configured venues, verify official publication and dates, and rank candidates. Do not begin paper discovery for code, setup, or documentation maintenance.
---

# Paper discovery

Use settings sections 1–4 for topics, sources, calendar windows, counts, and ranking. Follow `AGENTS.md` for full-history reading, exclusions, and publication.

## Verify eligibility

Discover proceedings/journal records directly or through bibliographic indexes, then open official publisher records. Indexes cross-check identity; acceptance listings, year-only dates, and author pages do not establish an exact first official publication date. Revisions and later issue assignments do not reset that date. Use the controller's computed inclusive calendar windows.

arXiv and author copies can supply full text after identity verification. Find the complete readable paper and inspectable visual evidence; abstracts only support screening. Respect publication-type exclusions and report coverage failures without weakening eligibility or narrowing the configured interests to AI.

Use `paper-note-search` to resolve identifiers, aliases, authors, and version relationships against prior evidence. Similar acronyms alone do not establish identity; unresolved relationships keep a candidate out of selection.

## Rank and hand off

Apply configured priorities and quotas. Prefer diversity when research quality and relevance are comparable. Classics need independently verified continuing influence, adoption, baseline use, or official recognition; keep that evidence separate from paper-only technical claims.

Hand off metadata, stable identity/aliases, official publication-date evidence, complete-paper URL/version, category, and selection rationale. Discovery does not reserve or finalize recommendations.

`scripts/paper_sources.py` provides index discovery, publisher verification, and PDF retrieval. `scripts/daily_pipeline.py` handles verified native-search fallback and selection. Stage JSON fields and tool-specific handoffs are defined in `scripts/pipeline_prompts.py`.
