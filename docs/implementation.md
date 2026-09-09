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
| `scripts/browser_render.py` | Render only local build files offline, with Chromium's sandbox enabled, and capture desktop/mobile evidence |
| `scripts/run_local_daily.py` | Synchronize `main`, run the pipeline, build the site, commit/push exact artifacts |
| `scripts/site_content.py`, `scripts/build_site.py`, `scripts/site_assets/` | Parse and display existing reports |

Preparation caches are ignored under `.cache/dailypaper/runs/<date>/`. They contain the resolved runtime receipt (`runtime.json`), selection, original PDFs, all page text/images, per-paper reviews, and a final bundle. The receipt records evidence and freezes the model, reasoning setting, Codex version and settings digest before selection; it is generated state, not another configuration file. A retry resolves current policy again, then stops if those values differ or an older checkpoint has no receipt. Preserve the pending selection for explicit reconciliation and revalidation. Nothing enters publication until all stages and a site build pass. Publication records hashes and the settings digest in the canonical run ledger; historic fields and import evidence are retained. Retain the cache when recovering an interrupted reservation.

Discovery treats an index access challenge, rate limit, or outage as a coverage failure. It skips that index for the remainder of the invocation instead of repeating the failure for every venue/year; the next invocation can try it again. When indexed results cannot fill a configured pool, the same verified Codex backend runs the search/history skills with native web search, current settings, and complete recommendation evidence. These are candidate leads: the controller independently checks publisher title, venue, publication type and exact date, then applies permanent exclusions. An arbitrary author page cannot declare itself an official publisher. Candidate exclusions and coverage failures appear in logs and the preparation workspace's `discovery.json`. No settings, history, or access restrictions are relaxed.

Classic selection can retrieve later citing texts when the initial screening has no independently verifiable influence source. A separate evidence check must establish use, adoption, or another configured influence criterion; a citation count or reference-list entry is insufficient. Unverified slots follow the settings' shortfall policy.

Complete-paper acquisition includes PDF supplements and appendices linked by the verified official article page. These are additional required documents, not alternative main PDFs. The controller keeps their original bytes and hashes, assembles all pages in source order, renders every page, and supplies the original document/page mapping to analysis and review. Missing supplements, unreadable pages, or an aggregate page count beyond the infrastructure limit stop preparation. Older preparation checkpoints without source receipts stop for revalidation of the same selection; archived reports remain unchanged. This uses the existing bounded controller download path; Codex does not receive network escalation to retrieve a large supplement.

Explicitly linked arXiv copies are also retrieved, preserving supplied version identifiers. A distinct author copy can contain artifact appendices absent from the publisher PDF; it is retained for comparison instead of silently replacing the publication copy. Byte-identical copies are not duplicated. Title mismatch or unavailable linked evidence stops acquisition. All retained documents count toward the existing page limit, and their original hashes and page mappings are verified. Article source links expose the retained documents, and visual references link to the correct original PDF page.

Paper validation and review can request up to two revisions of the same analysis, using the original document, selection, settings, and verified Codex runtime. Runtime/permission errors are fatal and are not treated as editing feedback. Persistent quality failures stop preparation. After paper reviews, the controller builds the complete article and renders it with a fresh, offline browser context. Requests are fulfilled only from the isolated build directory; external and escaping paths are denied. Chromium's OS sandbox remains enabled. The final model review receives actual desktop/mobile screenshots of the article and every figure/table. Screenshot hashes bind that evidence to the reviewed Markdown. Codex threads do not receive a host-browser command interface or broader permissions.

Every figure opens at its original pixel size in a scrollable viewer, with fit, original-size, and zoom controls. Browser verification exercises those controls for every figure at desktop and mobile widths and captures all scroll tiles, so reviewers can inspect labels that cannot remain legible in a narrow preview. Tables retain horizontal scrolling within the article. Coverage explanations belong in the article; verification, commit, push, and deployment status belong in controller execution records, as specified by AGENTS.md.

The existing setup command installs the Python Playwright dependency and its matching Chromium headless shell without installing privileged system packages. Preflight checks the local browser before spending time on research. Missing browser support stops the run without disabling its sandbox. Review stages distinguish source-visual checks from final website checks, avoiding a browser launch inside Codex's network-disabled execution sandbox.

For debugging, `start-my-day/scripts/search_arxiv.py --output <path>` now delegates to the same venue discovery stage; its old filename is retained for existing command callers. `scripts/codex_enrich.py --output <path>` prepares a complete bundle using the verified production runtime. The API adapter is retained for isolated compatibility checks; it cannot bypass the verified Codex model and reasoning policy. `scripts/publish_daily.py --input <bundle>` accepts only a validated bundle, never raw discovery or legacy abstract-enrichment JSON. Use the main runner for normal operation.

## Isolated checks

```bash
uv run --with-requirements requirements.txt python -m unittest discover -s tests -v
```

Fixtures use temporary repositories, generated PDFs, and mocked providers. No real recommendations, model calls, Git pushes, or production history writes occur. The existing reports can be rebuilt without generation with `python scripts/build_site.py --output-dir dist` after installing requirements.

`bash scripts/install_local_cron.sh --check` separately exercises the actual authenticated Codex runtime. It incurs model/tool usage and creates diagnostic artifacts, operational logs and ordinary Codex session records; it never selects papers or writes recommendation history. The production backend uses the same check before discovery, including an actual native subagent. Both parent and child run a controlled probe: a write to a disposable canary outside their workspace and a connection to the controller's local test listener must fail. Provider fallback is disabled.

Model selection requires one current official recommendation explicitly identifying the most capable Codex model for research, plus an authenticated account catalog entry. It does not rank model names or trust defaults. Reasoning selection requires every advertised setting to appear in official guidance and one uniquely strongest supported choice. The parser recognizes an explicit deepest-reasoning statement or explicit inequality ordering; documentation order and grouped names do not establish rank. For example, a group containing `max` and `xhigh` does not order those two levels. Unknown levels, ambiguous maxima, or changed evidence formats stop selection. The log records source URLs and hashes, recommendation text, supported settings, ordering evidence, chosen values, and CLI version.

The installed runtime's app-server protocol is used because its completed tool items include image-viewing receipts omitted by `codex exec --json`. Full-paper stage calls receive every rendered page as an original-detail image, the full extracted text and source paths, linked instructions, and the controller's Python interpreter. Agents use a temporary workspace with Codex's existing temporary-directory allowances; production report/history/Git mutations belong to the controller.

Every stage explicitly passes the resolved model and effort. Subagent defaults and the spawn contract require the same values at every delegation depth. The transport reads effective parent and child thread metadata before accepting results, checks CLI versions, and rejects model-reroute events, conflicting spawn arguments, substituted settings, missing metadata, failed turns, or unfinished subagents. Child settings are inspected when native activity is reported; a conflicting child may have started before detection, but its result cannot be accepted into a report. Runtime receipts are retained with preparation checkpoints so retries cannot combine outputs from different configurations.

Production, dry-run and retry calls explicitly set `approvalPolicy="never"` at thread and turn creation; the app-server also starts with `--ask-for-approval never`. Codex propagates the parent turn's live permission overrides to native descendants. The controller verifies the effective policy, `workspaceWrite` sandbox, disabled sandbox network access, and unchanged writable roots for every parent and child. It never grants authorization requests or changes global account settings. Unexpected requests or permission substitutions stop the run.

The installed runtime's ordinary `thread/read` metadata omits approval and sandbox settings. Generation threads therefore use normal Codex session records. The controller follows the thread's runtime-reported path and reads its `turn_context` permission receipts, verifying the thread identity and turn ID. It does not resume or alter active children. The specific startup error reporting an empty session metadata file is retried for at most 45 seconds before failing; other protocol errors and all setting mismatches remain fatal. No extra agent filesystem or host access is granted. Ephemeral, inference-free discovery probes still verify permissions directly from `thread/start`. Permission-change notifications are also checked during execution.

Cronie interprets the settings' local wall time through `CRON_TZ`; the managed block restores the preceding timezone afterward. Reinstallation migrates this checkout's old runner entry and replaces the same marked job, retaining unrelated lines. An advisory lock covers synchronization, verification, generation and publication, including manual runner invocations. Logs and the last successful runtime receipt live in ignored `state/logs/`. The host must remain on, with its cron daemon running. Changing the scheduled time in the settings requires rerunning the setup command.

The sole GitHub Actions workflow, `.github/workflows/pages.yml`, installs the matching test browser, runs isolated tests, and deploys archived content. Its triggers, permissions and deployment path are unchanged. Production report generation runs through the local cron job.

## Retained manual utilities

These tools support existing notes and assets; they do not publish daily recommendations or own report preferences. Inspect each command's `--help` before using it.

- `rg -n 'keyword|author name' content/papers` searches existing notes.
- `start-my-day/scripts/scan_existing_notes.py` rebuilds the note search index; `link_keywords.py` links note keywords.
- `paper-analyze/scripts/generate_note.py` creates an explicitly requested manual note; `update_graph.py` maintains its graph metadata.
- `extract-paper-images/scripts/extract_images.py` extracts arXiv source-package figures, source PDF figures, or embedded PDF images. The active visual skill explains inspection and placement in the shared asset layout.

The redundant curator index and four historical `skill.md` wrappers had no runtime imports or surviving command dependencies. Their useful utility guidance is retained here and in the active stage skills. Historical setup documents remain under `docs/archive/` and are not runtime instructions.
