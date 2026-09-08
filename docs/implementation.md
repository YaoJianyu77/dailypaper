# Pipeline implementation

Preferences live only in [Daily Paper Settings](../DAILY_REPORT_PRODUCT_REQUIREMENTS.md). This page describes code and manual utilities; operational rules are in [AGENTS.md](../AGENTS.md).

| File | Responsibility |
|---|---|
| `scripts/report_settings.py` | Parse the settings page, calendar windows, and infrastructure allowlist |
| `scripts/paper_sources.py` | Discover venue records, verify publisher evidence, retrieve complete PDFs and later-use evidence for classics |
| `scripts/recommendation_history.py` | Resolve permanent identities, reconcile prior evidence, conditionally write the ledger |
| `scripts/pipeline_prompts.py` | Build shared stage prompts and settings-derived output contracts |
| `scripts/ai_enrich.py`, `scripts/codex_enrich.py` | Share stage inputs; production uses verified local Codex, with the API adapter retained for isolated compatibility checks |
| `scripts/codex_runtime.py` | Resolve live official recommendations, verify account/model/mode, discover skills, and execute sandboxed Codex stages |
| `scripts/codex_checks.py` | Prove PDF reading, rendering, image inspection, web search, subagent settings and workflow routing using a temporary synthetic document |
| `scripts/install_local_cron.sh`, `scripts/local_schedule.py` | Install/update dependencies and the single timezone-aware job; preserve other schedules and enforce a whole-run lock |
| `scripts/daily_pipeline.py` | Prepare and resume selection, full-paper analysis, visuals, trends, and review |
| `scripts/report_validation.py` | Validate evidence and settings limits; assemble Markdown and visual assets |
| `scripts/publish_daily.py` | Validate the isolated site build and archive a prepared transaction |
| `scripts/run_local_daily.py` | Synchronize `main`, run the pipeline, build the site, commit/push exact artifacts |
| `scripts/site_content.py`, `scripts/build_site.py`, `scripts/site_assets/` | Parse and display existing reports |

Preparation caches are ignored under `.cache/dailypaper/runs/<date>/`. They contain the resolved runtime receipt (`runtime.json`), selection, original PDFs, all page text/images, per-paper reviews, and a final bundle. The receipt records evidence and freezes the model, reasoning setting, Codex version and settings digest before selection; it is generated state, not another configuration file. A retry resolves current policy again, then stops if those values differ or an older checkpoint has no receipt. Preserve the pending selection for explicit reconciliation and revalidation. Nothing enters publication until all stages and a site build pass. Publication records hashes and the settings digest in the canonical run ledger; historic fields and import evidence are retained. Retain the cache when recovering an interrupted reservation.

Classic selection can retrieve later citing texts when the initial screening has no independently verifiable influence source. A separate evidence check must establish use, adoption, or another configured influence criterion; a citation count or reference-list entry is insufficient. Unverified slots follow the settings' shortfall policy.

For debugging, `start-my-day/scripts/search_arxiv.py --output <path>` now delegates to the same venue discovery stage; its old filename is retained for existing command callers. `scripts/codex_enrich.py --output <path>` prepares a complete bundle using the verified production runtime. The API adapter is retained for isolated compatibility checks; it cannot bypass the verified Codex model and reasoning policy. `scripts/publish_daily.py --input <bundle>` accepts only a validated bundle, never raw discovery or legacy abstract-enrichment JSON. Use the main runner for normal operation.

## Isolated checks

```bash
uv run --with-requirements requirements.txt python -m unittest discover -s tests -v
```

Fixtures use temporary repositories, generated PDFs, and mocked providers. No real recommendations, model calls, Git pushes, or production history writes occur. The existing reports can be rebuilt without generation with `python scripts/build_site.py --output-dir dist` after installing requirements.

`bash scripts/install_local_cron.sh --check` separately exercises the actual authenticated Codex runtime. It incurs model/tool usage but only writes temporary diagnostic artifacts and ignored operational logs. The production backend uses the same check before discovery, including an actual native subagent. Provider fallback is disabled. Required authorization requests stop unattended execution; the client never approves them or alters account configuration.

Model selection requires one current official recommendation explicitly identifying the most capable Codex model for research, plus an authenticated account catalog entry. It does not rank model names or trust defaults. Reasoning selection requires every advertised setting to appear in official guidance and one uniquely strongest supported choice. The parser recognizes an explicit deepest-reasoning statement or explicit inequality ordering; documentation order and grouped names do not establish rank. For example, a group containing `max` and `xhigh` does not order those two levels. Unknown levels, ambiguous maxima, or changed evidence formats stop selection. The log records source URLs and hashes, recommendation text, supported settings, ordering evidence, chosen values, and CLI version.

The installed runtime's app-server protocol is used because its completed tool items include image-viewing receipts omitted by `codex exec --json`. Full-paper stage calls receive every rendered page as an original-detail image, the full extracted text and source paths, linked instructions, and the controller's Python interpreter. Only the temporary workspace is granted write access; report/history/Git mutations belong to the controller.

Every stage explicitly passes the resolved model and effort. Subagent defaults and the spawn contract require the same values at every delegation depth. The transport reads effective parent and child thread metadata before accepting results, checks CLI versions, and rejects model-reroute events, conflicting spawn arguments, substituted settings, missing metadata, failed turns, or unfinished subagents. Child settings are inspected when native activity is reported; a conflicting child may have started before detection, but its result cannot be accepted into a report. Runtime receipts are retained with preparation checkpoints so retries cannot combine outputs from different configurations.

Cronie interprets the settings' local wall time through `CRON_TZ`; the managed block restores the preceding timezone afterward. Reinstallation migrates this checkout's old runner entry and replaces the same marked job, retaining unrelated lines. An advisory lock covers synchronization, verification, generation and publication, including manual runner invocations. Logs and the last successful runtime receipt live in ignored `state/logs/`. The host must remain on, with its cron daemon running. Changing the scheduled time in the settings requires rerunning the setup command.

The sole GitHub Actions workflow, `.github/workflows/pages.yml`, runs isolated tests and deploys archived content. Production report generation runs through the local cron job.

## Retained manual utilities

These tools support existing notes and assets; they do not publish daily recommendations or own report preferences. Inspect each command's `--help` before using it.

- `rg -n 'keyword|author name' content/papers` searches existing notes.
- `start-my-day/scripts/scan_existing_notes.py` rebuilds the note search index; `link_keywords.py` links note keywords.
- `paper-analyze/scripts/generate_note.py` creates an explicitly requested manual note; `update_graph.py` maintains its graph metadata.
- `extract-paper-images/scripts/extract_images.py` extracts arXiv source-package figures, source PDF figures, or embedded PDF images. The active visual skill explains inspection and placement in the shared asset layout.

The redundant curator index and four historical `skill.md` wrappers had no runtime imports or surviving command dependencies. Their useful utility guidance is retained here and in the active stage skills. Historical setup documents remain under `docs/archive/` and are not runtime instructions.
