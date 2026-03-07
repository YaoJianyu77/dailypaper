---
name: paper-deep-analysis
description: Generate richer individual paper pages with method notes, evidence notes, figure usage, and graph metadata.
---

Use this skill for:
- `paper-analyze/scripts/generate_note.py`
- `paper-analyze/scripts/update_graph.py`
- extending a specific paper page under `content/papers/`
- richer top-paper pages produced from the daily workflow

Workflow:
1. Read the target paper page if it already exists and avoid wiping out meaningful manual notes.
2. Reuse repository metadata where possible: paper ID, title, authors, domain, source URL, PDF URL, summary, scores, keywords, and extracted assets.
3. Structure the note like a compact research memo, not a landing page blurb.
4. If assets exist under `images/`, use the most informative ones first: architecture, pipeline, and main-results figures before decorative plots.
5. Update graph metadata when relationships or reading order matter.

Desired note shape:
- Research background and motivation
- Problem framing
- Method or pipeline snapshot
- Evidence or experiment notes
- Research or engineering value
- Reading checklist
- Core contributions
- Risks, limitations, and what still needs verification

Writing rules:
- Stay grounded in the provided metadata, abstract, extracted figures, and any supplied paper context.
- Prefer concrete sections over generic praise.
- When evidence is missing, say the abstract or available context does not fully specify it.
- Use images to support browsing, not as decoration.
- Preserve existing useful human-written content whenever you extend a page.
