---
name: daily-paper-search
description: Search, verify, rank, and curate Systems Paper Daily candidates using the product requirements and permanent GitHub history.
---

# Purpose

Use this skill for paper discovery, venue and date verification, eligibility filtering, ranking, and permanent research-work deduplication.

## Required inputs

Read these before searching:

1. `PROJECT_STATE.md`
2. `DAILY_REPORT_PRODUCT_REQUIREMENTS.md`
3. `state/recommendation_history.json`
4. `config.yaml` only when the local Python search pipeline is being used

The product requirements control the research areas, venue whitelist, time windows, quotas, output language, and permanent duplicate policy. Local config values may refine retrieval mechanics but must not weaken those requirements.

## Search flow

**Execution date → exact latest/classic windows → configured venue pages and indexes → candidate metadata → official publication verification → accessible full text → research-area fit → permanent-history exclusion → quality ranking → final set.**

### 1. Calculate the pools

Use the current date in `America/New_York`.

- Latest pool: preceding six calendar months, including the execution date.
- Classic pool: preceding five years, excluding the latest window.

Print the exact inclusive ranges in the report. Use the first official online-publication date. Do not treat an arXiv revision, code update, or later issue assignment as a new publication.

### 2. Search venue-first

Search only the conferences and journals currently listed in `DAILY_REPORT_PRODUCT_REQUIREMENTS.md`.

Publication verification priority:

1. official conference or journal page;
2. USENIX, ACM Digital Library, IEEE Xplore, or official proceedings;
3. DBLP/OpenAlex/Semantic Scholar for discovery and cross-checking;
4. arXiv, author pages, or institutional pages for an accessible full-text copy.

arXiv alone is not publication evidence. Reject workshop papers, posters, tutorials, extended abstracts, and unverified preprints unless the product requirements explicitly permit them.

### 3. Require readable full text

A candidate is eligible for the final set only when the complete paper can be read and its important figures, tables, experiments, footnotes, and relevant appendices can be inspected. Abstract-only access is insufficient for a detailed recommendation.

If the official copy is inaccessible, look for a verified author or arXiv copy of the same work. If full text still cannot be read, replace the paper or leave the slot unfilled.

## Permanent research-work identity

Before ranking, resolve each candidate to a stable research-work identity.

Use identifiers in this order:

1. normalized DOI;
2. arXiv ID without `vN`;
3. DBLP key or another stable publication ID;
4. normalized title and meaningful author overlap;
5. explicit evidence linking renamed, preprint, conference, journal, or extended versions.

Normalize titles by lowercasing, removing punctuation, collapsing whitespace, and removing harmless venue/version suffixes. Do not rely on exact title equality alone.

Treat these as the same work unless the main technical contribution is demonstrably different:

- arXiv v1 and later arXiv versions;
- preprint and conference version;
- renamed camera-ready version;
- conference and journal version that primarily extends evaluation or exposition;
- different landing pages or mirrors.

## Permanent history exclusion

Canonical scheduled-task history:

- `state/recommendation_history.json`

Read the entire file before candidate selection. Any work recorded as imported, reserved, archived, completed, or otherwise already recommended is permanently ineligible. There is no cooldown and no expiration.

Also search existing `content/daily/` reports when an identifier or alias is uncertain. A prior recommendation discovered in an archived report must be treated as exclusion evidence even if an index record is incomplete.

Fail closed when:

- history cannot be read completely;
- history is malformed or internally inconsistent in a way that affects deduplication;
- candidate identity cannot be resolved confidently;
- the current history changes between initial selection and the pre-write check and the conflict cannot be reconciled.

## Selection

Target, never quota:

- four latest papers;
- one classic paper.

Rank latest papers by:

1. fit with configured systems interests;
2. importance of the bottleneck;
3. originality and causal clarity of the idea;
4. strength of the evaluation;
5. practical or research value.

For a classic paper, verify continuing influence through later systems, recurring baseline use, adoption, deployment, an official award, or another concrete signal. Citation count alone is not enough.

Prefer topic diversity only after relevance and quality. Never pad the list by repeating a work, widening the time window, relaxing the venue list, or using an abstract-only candidate.

## Transaction and concurrency rules

Use a stable run ID:

`systems-paper-daily:YYYY-MM-DD`

After the complete report has been drafted but before publishing:

1. re-read `state/recommendation_history.json`;
2. repeat identity and duplicate checks for all selected works;
3. reserve all selected work IDs in one coherent history update;
4. write the report and visual assets;
5. verify the report;
6. mark the reservations archived/completed and record the report path;
7. re-read and verify the final history.

A retry for the same date must resume or verify the existing run. It must not select a second set of papers.

## Local-pipeline compatibility

When modifying `start-my-day/scripts/search_arxiv.py`, prefer configuration changes under `search`, `search.scoring`, `research_domains`, and `excluded_keywords`. Preserve graceful fallback behavior for Semantic Scholar and other metadata services.

The legacy local index `state/paper_index.json` may still contain cooldown fields, but the ChatGPT scheduled workflow must not use cooldown-based re-eligibility. Any previously recommended work remains excluded.