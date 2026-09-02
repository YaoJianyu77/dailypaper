---
name: paper-note-search
description: Search persistent recommendation history, archived daily reports, paper aliases, and existing repository notes.
---

# Purpose

Use this skill whenever a task must determine whether a paper or research work has appeared before, find a prior report, resolve renamed versions, or reuse verified repository context.

## Search order

1. `state/recommendation_history.json` — canonical ChatGPT scheduled-task history.
2. `content/daily/` — archived daily reports and independent evidence of prior recommendation.
3. `state/paper_index.json` — legacy/local-pipeline index and additional import evidence.
4. `content/papers/` and `content/assets/papers/` — existing notes and visual assets.
5. `content/meta/` and `state/existing_notes_index.json` — navigation and keyword indexes.

Read the complete canonical history before making a non-duplicate claim. A snippet search is not sufficient for a final eligibility decision.

## Identity search

Search each candidate by:

- normalized DOI;
- arXiv ID without version suffix;
- DBLP key or other stable publication ID;
- exact title;
- normalized title;
- former or alternate titles;
- first author and meaningful coauthor overlap;
- official publication and preprint relationship.

Prefer identifier matches, but do not miss the same research work because its title, venue, or URL changed.

Treat an archived daily report as authoritative evidence that the work was recommended even when the canonical history has an incomplete identifier. Add or repair the history record before publication when safe to do so.

## Permanent exclusion semantics

Any work previously recommended is permanently excluded. Ignore legacy `cooldown_until` dates for the scheduled workflow. A work does not become eligible again when:

- its cooldown expires;
- a new arXiv version appears;
- the camera-ready title changes;
- the conference paper receives a journal extension;
- a different mirror or publisher URL is found.

Only treat an extension as a distinct work when its main technical idea and evaluation are demonstrably different, and record the relationship explicitly.

## Concurrency check

Immediately before reserving selected papers, re-read the current canonical history and repeat all identity searches. If another run added a selected work, discard it and reselect before publishing. Do not overwrite concurrent updates.

## Existing note and asset search

When a paper remains eligible, search existing notes and assets for reusable verified material. Reuse is allowed only after checking it against the current paper version. Existing summaries or extracted figures may be stale, incomplete, or associated with a different version.

For local repository work, `rg` remains the preferred search tool. Use `start-my-day/scripts/scan_existing_notes.py` to rebuild `state/existing_notes_index.json` when needed, and `start-my-day/scripts/link_keywords.py` only when the report is configured to link keywords.

## Result style

Return concrete matches with stable identifiers and exact repository paths. For deduplication decisions, state the match type—for example DOI match, arXiv-base-ID match, renamed-title match, or conference/preprint relationship—instead of merely saying “duplicate.”