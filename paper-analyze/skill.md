---
name: paper-analyze
description: Legacy wrapper for repository-based paper page generation
---

This file is retained for compatibility only.

The repository no longer depends on Obsidian.
Generate paper pages directly inside `content/papers/`:

```bash
python paper-analyze/scripts/generate_note.py \
  --paper-id 2602.12345 \
  --title "Paper Title" \
  --authors "Author A, Author B" \
  --domain "Agents"
```

Update graph metadata with:

```bash
python paper-analyze/scripts/update_graph.py \
  --paper-id 2602.12345 \
  --title "Paper Title" \
  --domain "Agents" \
  --score 8.4
```
