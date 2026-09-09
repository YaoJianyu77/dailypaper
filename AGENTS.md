# Agent Instructions

Execution rules belong here; user preferences belong only in `DAILY_REPORT_PRODUCT_REQUIREMENTS.md`.

## Read and route

Read `PROJECT_STATE.md`, then the complete settings page. Before selection, read complete canonical history and prior recommendation evidence through `scripts/recommendation_history.py`. Before implementation changes, read the relevant skills and their callers.

Precedence: the user's explicit request → settings → this file → skill details. Older files, cached prompts, and defaults cannot override settings or require a second preference edit.

When asked to generate DailyPaper, execute these skills in order. Read full history before discovery, then resolve candidate identities at the history stage. The user need not name skills individually.

| Stage | Canonical skill |
|---|---|
| Discover, verify, rank | `skills/daily-paper-search/SKILL.md` |
| Resolve identities and prior recommendations | `skills/paper-note-search/SKILL.md` |
| Read and explain complete papers | `skills/paper-deep-analysis/SKILL.md` |
| Inspect and prepare visuals | `skills/paper-image-extractor/SKILL.md` |
| Assemble and check the article | `skills/daily-paper-editor/SKILL.md` |

`.agents/skills/` links to these folders; `scripts/pipeline_prompts.py` supplies the applicable instructions to each stage. For code, documentation, setup, and tests, use only relevant skills and isolated fixtures. Maintenance must not discover papers, reserve recommendations, alter production history, or publish a report.

## Runtime and permissions

Use `scripts/run_local_daily.py` for production. It must verify the model and reasoning policy from the settings before generation. Apply the exact resolved configuration to every stage and delegated research check; verify parent and descendant settings and reject substitutions. Retain the configuration in preparation checkpoints so retries cannot mix models or reasoning settings.

Production, dry-run, retry, and delegated Codex threads use explicit `approvalPolicy="never"` with the existing `workspaceWrite` sandbox. Verify effective approval and sandbox settings; never inherit an interactive policy. `never` grants no additional filesystem, network, or host permissions. Operations outside the sandbox must fail without escalation, permission grants, or automatic approval.

Use tools to read full papers, inspect pages, calculate results, and prepare visuals in scratch storage. Only the controller writes production content/history or runs Git publication. Stage tasks must not recursively launch generation or publication. Keep transport in `scripts/codex_enrich.py`, prompts/contracts in `scripts/pipeline_prompts.py`, and orchestration in `scripts/daily_pipeline.py`; update callers and isolated tests with contract changes.

## File ownership

- User settings: `DAILY_REPORT_PRODUCT_REQUIREMENTS.md`.
- Infrastructure only: `config.yaml`; additional preference keys are rejected.
- Reports: `content/daily/YYYY-MM-DD.md`; retained images: `content/assets/papers/`.
- Permanent history: `state/recommendation_history.json`. `state/paper_index.json` and archived reports remain independent prior evidence, never replacement histories.
- Preparation/recovery: ignored `.cache/dailypaper/`, never an authoritative ledger.

Preserve reports, images, prior evidence, useful notes, and unrelated changes. Do not change schedules or credentials without explicit authorization. Do not create another product, settings layer, history, or `chatgpt_daily/` directory. The website is the reading surface; an explicitly requested chat report presents the same selection and verified visuals.

## Identity and publication transaction

Normalize DOI, versionless arXiv IDs, stable venue/DBLP identifiers, titles/aliases, authors, and explicit version relationships. Renamed or republished versions of the same work remain excluded. An ambiguous match does not permit re-recommendation.

Reconcile existing evidence without dropping any work, alias, status, or run record. Missing or unread evidence is not empty history. Reserved, imported, archived, and completed works stay excluded permanently; pending reservations never expire automatically.

Use the configured local date's stable run ID, such as `systems-paper-daily:2026-09-08`. Retries resume or verify the same selection and artifacts. Never discard a pending reservation to accommodate changed settings: preserve it, reconcile, and revalidate. Never overwrite a completed report without explicit permission.

Prepare and validate the complete article and assets before reserving. Immediately before state changes, reread current history and check for concurrent changes. Use conditional writes and non-forced Git updates. On conflict, reread, reconcile, and revalidate; never force-push or drop another run's records.

Prefer committing the report, assets, and final history together. If reservation is separate, reserve under the run ID, archive and verify the report, then finalize and verify history. Do not expose partial drafts as completed reports. Preserve recovery artifacts on interruption and report the exact failure.

## Quality and completion

Validate against current settings: publication/date eligibility, permanent identity, full-paper reading, experimental claims and conditions, word counts, visuals, and trends. Inspect the rendered website at its deployment base path; image syntax, file existence, and asset inventories do not prove visible, legible figures or tables.

Read back committed content and history. Distinguish generated, committed, pushed, deployed, and verified states; a commit alone proves no deployment. Verify schedules and unattended capabilities from actual execution, not documentation. Implementation details and test commands are in `docs/implementation.md`.
