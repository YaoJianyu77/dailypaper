---
name: paper-note-search
description: Search existing repository paper pages, daily reports, and keyword indexes efficiently.
---

Use this skill for:
- finding papers already in `content/papers/`
- searching `content/daily/` and `content/meta/`
- refreshing note indexes and keyword links

Workflow:
1. Prefer `rg` over slower search tools.
2. Search `content/papers/` for titles, authors, domains, and keywords.
3. Search `content/daily/` when the user asks about when or why a paper was recommended.
4. Use `start-my-day/scripts/scan_existing_notes.py` to rebuild `state/existing_notes_index.json` when keyword indexes may be stale.
5. Use `start-my-day/scripts/link_keywords.py` when a markdown report should link to existing paper pages.

Result style:
- Prefer exact or title matches first.
- Then show nearby domain or keyword matches.
- Mention the repository path or site path the user should inspect next.
