---
name: paper-note-search
description: Search persistent recommendation history, archived daily reports, paper aliases, and existing repository notes.
---

# Purpose

Use this skill whenever a task must determine whether a paper or research work has appeared before, find a prior report, resolve renamed versions, or reuse verified repository context.

## Search order

1. `state/recommendation_history.json` — canonical history for every generation entry point.
2. `content/daily/` — archived daily reports and independent evidence of prior recommendation.
3. `state/paper_index.json` — retained prior recommendation evidence, read only by the current pipeline.
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

## Exclusion and concurrency

Follow `AGENTS.md` for permanent exclusions, legacy evidence preservation, reservations, and concurrent writes. `scripts/recommendation_history.py` applies this protocol for every transport. To distinguish a technical extension, compare its main idea and evaluation with the prior work and record the verified relationship; a different publication record alone is insufficient.

## Existing note and asset search

When a paper remains eligible, search existing notes and assets for reusable verified material. Reuse is allowed only after checking it against the current paper version. Existing summaries or extracted figures may be stale, incomplete, or associated with a different version.

For local repository work, `rg` remains the preferred search tool. For explicitly requested note maintenance, `start-my-day/scripts/scan_existing_notes.py` rebuilds the note index and `start-my-day/scripts/link_keywords.py` links keywords. These utilities do not select or publish recommendations.

## Result style

Return concrete matches with stable identifiers and exact repository paths. For deduplication decisions, state the match type—for example DOI match, arXiv-base-ID match, renamed-title match, or conference/preprint relationship—instead of merely saying “duplicate.”
