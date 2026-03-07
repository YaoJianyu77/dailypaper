---
name: start-my-day
description: Legacy wrapper for the repository-based daily paper pipeline
---

This file is kept only as a historical reference.

The active workflow is no longer an Obsidian or Claude skill workflow.
Use the repository scripts directly instead:

```bash
python start-my-day/scripts/search_arxiv.py --config config.yaml --output state/arxiv_filtered.json
python scripts/publish_daily.py --input state/arxiv_filtered.json
python scripts/build_site.py --output-dir dist
```

Outputs:

- `content/daily/` for daily reports
- `content/papers/` for paper pages
- `content/meta/` for latest/archive metadata
- `dist/` for the generated static website
