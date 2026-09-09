---
name: paper-note-search
description: Use during DailyPaper generation to check candidates against permanent history, or when asked to find prior papers, reports, aliases, notes, or recommendation evidence. History lookup alone does not authorize a new report.
---

# History and existing material

Read complete history through `scripts/recommendation_history.py`, which reconciles `state/recommendation_history.json`, archived daily reports, and the retained `state/paper_index.json`. A snippet search cannot establish that a work is new. Follow `AGENTS.md` for permanent exclusion and safe history updates.

## Identity checks

Search normalized DOI, versionless arXiv ID, stable DBLP/venue identifiers, exact/normalized titles, former titles, author overlap, and explicit publication/preprint relationships. Different titles, venues, or URLs alone do not make a new work. For a proposed technical extension, compare its main contribution and evaluation with the earlier paper and record the relationship.

An archived report is evidence of prior recommendation even when canonical identifiers are incomplete. Resolve gaps before publication through the existing transaction; do not ignore them or infer empty history.

## Reuse and response

Search `content/papers/`, `content/daily/`, and `content/assets/papers/` with `rg` for notes and visuals. Legacy metadata/index snapshots can assist lookup but are not current selection rules. Verify any reused summary or figure against the selected paper version.

Return stable identifiers, exact repository paths, and the match type: DOI, arXiv base ID, renamed title, or version relationship. Explain unresolved matches instead of simply labeling a candidate duplicate or new.
