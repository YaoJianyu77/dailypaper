# Agent Instructions

This file explains execution, not the user's preferences. Do not send the user here to change topics, sources, dates, counts, summary length, or visuals.

## Read before acting

Read `DAILY_REPORT_PRODUCT_REQUIREMENTS.md` completely for the current settings. Read `PROJECT_STATE.md` for verified implementation limitations. Load the relevant active skills for the stage being executed.

The precedence is: the user's current explicit request, then the settings page, then these execution rules, then skill implementation details. Older documentation, example configurations, cached prompts, and script defaults cannot silently override the settings. Do not ask the user to maintain the same preference in several files.

## Skill responsibilities

| Stage | Skill |
|---|---|
| Discover, verify, and rank eligible papers | `skills/daily-paper-search/SKILL.md` |
| Resolve identities and consult prior recommendations | `skills/paper-note-search/SKILL.md` |
| Read and explain the complete paper | `skills/paper-deep-analysis/SKILL.md` |
| Inspect, extract, render, and verify visuals | `skills/paper-image-extractor/SKILL.md` |
| Assemble and check the daily article | `skills/daily-paper-editor/SKILL.md` |

`skills/daily-paper-curator/SKILL.md` is a compatibility index, not an additional competing workflow. Read skills explicitly when the runtime does not discover their current paths automatically. Legacy `skill.md` files inside helper directories and `docs/archive/` are historical references, not current instructions.

## One publication path

**Read settings and complete history → search and verify → deduplicate → read full papers → prepare complete analyses and rendered visuals → validate the article → reserve and commit safely → verify committed content and history → publish the static website.**

The website is the primary reading surface. Do not create a second daily-paper product, configuration, history, or `chatgpt_daily/` directory. A ChatGPT delivery step is not required. When the user explicitly requests a report in chat, provide that report with the available verified visuals as an additional presentation, not a second selection run.

## File ownership

- User preferences: `DAILY_REPORT_PRODUCT_REQUIREMENTS.md` only.
- Reports: `content/daily/YYYY-MM-DD.md`.
- Retained visual assets: `content/assets/papers/`, in the existing per-paper image layout.
- Authoritative permanent recommendation history: `state/recommendation_history.json`.
- Legacy `state/paper_index.json`: prior recommendation evidence and compatibility data; never a replacement for permanent history.
- `config.yaml` and `config.example.yaml`: inputs to the legacy Python helpers, not additional user-facing instructions. Changes here do not by themselves prove compliance with the settings page.

Do not relocate helper scripts, rename schema fields, delete data, install a timer, or change server credentials merely as part of a documentation cleanup.

## Permanent identity and safe publication

Read the full history from a known current version, not a search excerpt. Normalize DOI, versionless arXiv IDs, stable venue/DBLP identifiers, title aliases, and author information. Resolve renamed and republished versions by research-work identity. An ambiguous match is not permission to re-recommend it.

Import and reconcile prior recommendation evidence when necessary; do not infer that an unread or missing index is empty. Preserve every existing work, alias, status, and run record. Reserved, imported, archived, and completed works remain excluded from new runs. Pending reservations must not expire automatically.

Use a stable logical run ID derived from the configured local date, such as `systems-paper-daily:2026-09-08`. Resume or verify the same run on retry; do not create a second paper set. Do not overwrite a completed report without explicit permission.

Prepare the full report and visual assets before reserving works. Immediately before updating state, re-read the current history and check for concurrent changes. Use a conditional file update or a non-forced branch update based on the validated version. On conflict, re-read, reconcile, and revalidate; never force-push or drop another run's records.

Prefer committing the completed report, assets, and final history together. If reservations require a separate write, reserve under the run ID, archive and verify the completed report, then finalize history and verify it. Never expose a partial draft as a completed report. On interruption, retain enough reservation state to recover safely, and report the exact failure instead of claiming success.

## Quality and deployment checks

Read current limits and output structure from the settings page rather than hard-coding copies in this file or the skills. Verify full-text reading, eligibility, identity, exact experimental claims, word counts, visible figures/tables, and the trend section.

Inspect the rendered website output. Markdown image syntax, a successful file write, or an asset inventory alone does not prove that a figure is visible and legible. Check relative asset paths with the site's deployment base path.

Read back the committed report and history. Distinguish generated, committed, pushed, deployed, and verified states in execution status; a commit does not prove deployment. Do not infer unattended permissions or a server schedule from repository documentation.

For a documentation-only request, do not generate a report, alter recommendation history, or run the legacy publisher. For a production-generation request, do not silently use the legacy abstract-enrichment runner as if it fulfilled full-paper analysis and permanent deduplication.
