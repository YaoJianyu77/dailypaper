---
name: paper-search
description: Legacy note for searching repository paper pages
---

Search is now expected to run against repository content, not an Obsidian vault.

Recommended local search commands:

```bash
rg -n "keyword" content/papers
rg -n "author name" content/papers
```

If you want web search later, add a static search index during `scripts/build_site.py`.
