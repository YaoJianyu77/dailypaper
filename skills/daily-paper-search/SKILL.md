---
name: daily-paper-search
description: Use when generating DailyPaper or explicitly finding eligible research papers; discover configured venues, verify official publication and dates, and rank candidates. Do not begin paper discovery for code, setup, or documentation maintenance.
---

# Inputs and authority

Read `DAILY_REPORT_PRODUCT_REQUIREMENTS.md` Sections 1–4 for current topics, sources, time windows, timezone, counts, and selection priorities. Read `PROJECT_STATE.md` for known implementation gaps and `AGENTS.md` for history and publication rules. Do not hard-code a second set of these preferences in this skill.

# Discovery and eligibility

**Configured local date → exact eligible windows → venue-first discovery → official identity/date → readable full paper → topic fit → permanent identity exclusion → ranking.**

Compute calendar-month and calendar-year boundaries from the actual local date, clamping to the last valid day when needed. The classic window ends the day before the latest window starts. Print inclusive dates. Revisions, mirror updates, or issue assignments do not reset first official publication.

For each configured venue, find its proceedings or journal articles directly or through a bibliographic index, then verify the official publisher record. Bibliographic services can discover and cross-check records; they cannot establish publication status by themselves. arXiv or an author copy may provide full text after its identity is verified. An acceptance listing without a qualifying publication date is insufficient when the date affects eligibility. A year-only record cannot justify an invented exact day.

Do not silently narrow broad systems interests to AI or use metadata popularity in place of relevance. Respect configured publication-type exclusions. If sources fail or rate-limit, use other eligible sources and report material coverage limits rather than weakening eligibility.

A final candidate requires the complete readable paper and inspectable key visual evidence. Abstracts can screen candidates but cannot support the final analysis. Look for a verified alternative full-text copy; otherwise replace the candidate or leave a slot unfilled.

# Work identity

Match normalized DOI, versionless arXiv ID, stable bibliographic identifiers, normalized titles, author overlap, and explicit version relationships. Keep verified aliases together. Normalize title punctuation and whitespace without assuming two similar acronyms identify the same work.

Preprint/formal versions, renamed camera-ready titles, mirrors, and extensions of the same core contribution do not become new recommendations. If the evidence cannot resolve identity, hold out the candidate rather than guessing it is new.

Use `skills/paper-note-search/SKILL.md` for evidence lookup and the permanent-history protocol in `AGENTS.md` for exclusion and state updates.

# Selection and handoff

Apply the current counts and priorities in the preference file, not values from old scripts. Do not pad quotas by relaxing dates, sources, relevance, full-text access, or non-repetition. Prefer diversity only after comparable relevance and quality.

For classics, verify continuing influence from later work, baseline use, adoption, deployment, or official recognition. Keep these selection sources separate from the paper-only technical summary.

Hand off verified metadata, stable work identity and aliases, publication-date evidence, full-text location/version, category, and selection evidence to the deep-analysis skill. Discovery does not mark a work successfully recommended. Reserve and finalize only through `AGENTS.md` after the report is prepared and checked.

# Existing helpers

`scripts/paper_sources.py` implements venue-index discovery, publisher verification, and complete PDF retrieval. `start-my-day/scripts/search_arxiv.py` is a command adapter to that discovery stage. Discovery JSON is screening evidence; only the shared pipeline can prepare a publishable bundle. Coverage limitations belong in the selection handoff, not in relaxed eligibility rules.
