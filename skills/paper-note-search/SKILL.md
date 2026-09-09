---
name: paper-note-search
description: Use during DailyPaper generation to check candidates against permanent history, or when asked to find prior papers, reports, aliases, notes, or recommendation evidence. History lookup alone does not authorize a new report.
---

# History and existing material

Use `scripts/recommendation_history.py` to read and reconcile the evidence sources owned by `AGENTS.md`. Follow its full-history, permanent-exclusion, and safe-update rules.

## Identity checks

Apply the identity normalization in `AGENTS.md`; cross-check title aliases with author overlap and explicit publication/preprint relationships. For a proposed technical extension, compare its main contribution and evaluation with the earlier paper and record the relationship.

When an archived report has incomplete canonical identifiers, use its cited source and authors to resolve the relationship before publication.

## Reuse and response

Search `content/papers/`, `content/daily/`, and `content/assets/papers/` with `rg` for notes and visuals. Legacy metadata/index snapshots can assist lookup but are not current selection rules. Verify any reused summary or figure against the selected paper version.

Return stable identifiers, exact repository paths, and the match type: DOI, arXiv base ID, renamed title, or version relationship. Explain unresolved matches instead of simply labeling a candidate duplicate or new.
