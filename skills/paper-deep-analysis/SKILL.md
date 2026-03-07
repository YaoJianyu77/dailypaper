---
name: paper-deep-analysis
description: Generate or extend an individual paper page, related metadata, and graph entries in the repository content store.
---

Use this skill for:
- `paper-analyze/scripts/generate_note.py`
- `paper-analyze/scripts/update_graph.py`
- extending a specific paper page under `content/papers/`

Workflow:
1. Read the target paper page if it already exists.
2. Reuse repository metadata where possible: paper ID, title, authors, domain, source URL, PDF URL, summary.
3. Generate the paper page with `paper-analyze/scripts/generate_note.py` when bootstrapping a new note.
4. Update graph metadata with `paper-analyze/scripts/update_graph.py` when relationships or scores matter.
5. If assets are needed, use `skills/paper-image-extractor/SKILL.md`.

Writing rules:
- Keep the generated page grounded in available metadata and abstract text.
- Prefer concise structure over long speculative analysis unless the user explicitly asks for depth.
- Do not overwrite meaningful manual notes without checking the existing file carefully.
