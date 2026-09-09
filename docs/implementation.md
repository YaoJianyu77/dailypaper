# Implementation

[Settings](../DAILY_REPORT_PRODUCT_REQUIREMENTS.md) own preferences; [AGENTS.md](../AGENTS.md) owns execution and publication rules; [PROJECT_STATE.md](../PROJECT_STATE.md) records verification and gaps.

## Main path

`install_local_cron.sh` → `run_local_daily.py` → `daily_pipeline.py` → `publish_daily.py` → Git push → the existing Pages workflow.

| Module | Responsibility |
|---|---|
| `report_settings.py` | Parse six settings sections, calendar windows, and infrastructure allowlist |
| `local_schedule.py` | Manage the timezone-aware job and whole-run lock |
| `codex_runtime.py` | Resolve official model/reasoning evidence, verify account access, enforce effective runtime permissions and configuration |
| `codex_checks.py` | Prove PDF reading, image inspection, web search, skill routing, and subagent capabilities with synthetic inputs |
| `codex_enrich.py` | Send stage prompts/images to the verified Codex runtime and validate JSON responses |
| `pipeline_prompts.py` | Select stage skills and construct shared prompts and output schemas |
| `paper_sources.py` | Discover candidates, verify publication, retrieve complete papers and classic-influence evidence |
| `recommendation_history.py` | Resolve identities, reconcile legacy evidence, conditionally update permanent history |
| `daily_pipeline.py` | Prepare and resume selection, analysis, visuals, trends, and reviews |
| `report_validation.py` | Validate evidence/limits, prepare visual assets, assemble Markdown |
| `publish_daily.py` | Validate the isolated website and archive a complete transaction |
| `browser_render.py` | Inspect local build files offline with sandboxed Chromium and capture desktop/mobile evidence |
| `content_store.py` | Find the repository and read/write Markdown frontmatter |
| `site_content.py` | Parse current and legacy report formats and locate source sections |
| `build_site.py` | Build navigation, one reader, and a derived index; copy Markdown and images |
| `site_assets/` | Reader template behavior, archive filters, figure controls, and styles |

All modules above live in `scripts/`. The useful manual extractor lives with its skill at `skills/paper-image-extractor/scripts/extract_images.py`; it supports arXiv source figures and local PDF images. Existing notes can be searched directly with `rg -n 'keyword' content/papers`. Legacy notes, metadata, indexes, and recommendation evidence are retained as data, not active settings or alternative pipelines.

Stage prompts load current settings, execution rules, and each applicable canonical skill once; task text supplies field meanings and controller handoffs. Paper reviews load search, history, analysis, and visual skills. Final article reviews load editing and visual skills, using the completed paper-review receipts for paper-specific checks; article prose is sent once as Markdown, without another copy of each analysis. Unknown review kinds are rejected. The same generated JSON schema supplies both the prompt's output contract and the runtime's structured-output constraint.

## Evidence and recovery

Discovery skips an index for the rest of an invocation after an access challenge, rate limit, or outage. If verified pools remain short, Codex searches official sources; the controller independently checks title, venue, type, and exact publication date. Author pages supply full text, not publication proof. A classic can be checked against retrieved later-use evidence; citation counts alone do not establish influence. Diagnostics stay in `discovery.json`.

Paper acquisition retains the verified main PDF, publisher-linked supplements, and distinct explicitly linked author versions. Original bytes, hashes, source URLs, and page mappings remain available for review. Byte-identical copies are deduplicated. Missing appendices, wrong-work copies, unreadable pages, or aggregate limits stop preparation. Combined page numbers identify visual crops and claim evidence; source page numbers preserve citations to originals.

Ignored `.cache/dailypaper/runs/<date>/` holds `runtime.json`, selection, PDFs/page images, reviewed papers, trends, the rendered site, and `bundle.json`. Runtime receipts freeze model, reasoning, CLI version, and settings digest. Revisions retain the same selected paper and original evidence; persistent review failures stop the run. The final review receives actual website screenshots. Report and asset hashes bind archived files to reviewed artifacts; transaction recovery follows AGENTS.md.

## Codex and scheduling details

The app-server transport provides image-viewing receipts absent from `codex exec --json`. Official recommendation text and the authenticated account catalog identify the research model. Supported reasoning settings must have a uniquely strongest choice established by documented ordering, not model names, defaults, or list position. Source URLs/hashes, selection evidence, effective model/effort, and CLI version are logged under ignored `state/logs/`.

Ordinary `thread/read` omits effective approval/sandbox details, so verification reads the runtime-reported session's `turn_context`, bound to its thread and turn IDs. It never resumes active children. Empty startup metadata is retried read-only for at most 45 seconds; other protocol errors and configuration mismatches are fatal. Parent/descendant checks and reroute rejection run before output is accepted. Controlled filesystem/network denials are part of the synthetic capability check.

Setup installs versioned user-owned Codex binaries to avoid replacing an active NFS executable. Cronie's `CRON_TZ` provides local wall time and DST; installation restores the preceding timezone and preserves unrelated entries. The same advisory lock covers manual and scheduled runs. Changing the schedule in settings requires rerunning setup. The host and its cron daemon must remain running.

## Website

`reader/index.html` loads the date selected by `?date=YYYY-MM-DD`. The builder copies original Markdown bytes to `dist/reports/` and derives `reports/index.json` containing navigation metadata, section line spans, and hashes. Article prose remains in Markdown. The Python parser identifies legacy/current sections; the browser extracts them and renders them with vendored markdown-it. Raw HTML and unsafe Markdown links are disabled. Hash mismatches and missing reports show retry guidance. Versioned assets avoid stale browser scripts during updates.

Only homepage, archive, reader, and generic `404.html` are emitted as HTML. Old `/daily/YYYY-MM-DD/` URLs redirect through that 404 page, retaining anchors. The reader requires JavaScript; homepage and archive remain static. Figures open at original size with fit/zoom/pan controls; wide tables scroll inside the article.

Production and dry-run checks use this same reader. The browser is offline and fulfills same-origin requests only from the isolated build directory; external and escaping paths are denied. Chromium's sandbox remains enabled. Screenshots cover every figure/table, desktop/mobile layouts, and all original-size figure scroll tiles.

The sole workflow, `.github/workflows/pages.yml`, tests and deploys committed content. It uses Ubuntu 22.04 because 24.04's AppArmor policy blocked Playwright Chromium's user namespaces. No sandbox downgrade or host policy changes are used. Generation remains in the existing local runner.

## Isolated checks and preview

```bash
.cache/dailypaper/venv/bin/python -m unittest discover -s tests -v
.cache/dailypaper/venv/bin/python scripts/build_site.py --output-dir dist
.cache/dailypaper/venv/bin/python -m http.server 8000 --directory dist
```

Fixtures use temporary repositories, synthetic PDFs, and mocked models. They do not publish reports or modify production history. Browser regressions cover all archived prose, links, tables, images, date navigation, old URLs, failure states, and unsafe Markdown. Serve local previews over localhost HTTP; the reader cannot fetch Markdown through `file://`.

`bash scripts/install_local_cron.sh --check` separately exercises the authenticated runtime with synthetic inputs, including a native subagent. It consumes model/tool usage and writes diagnostics and normal Codex session records, but no recommendations or history. Use README's runner commands for actual generation and isolated full preparation.
