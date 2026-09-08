# Pipeline implementation

Preferences live only in [Daily Paper Settings](../DAILY_REPORT_PRODUCT_REQUIREMENTS.md). This page describes code and manual utilities; operational rules are in [AGENTS.md](../AGENTS.md).

| File | Responsibility |
|---|---|
| `scripts/report_settings.py` | Parse the settings page, calendar windows, and infrastructure allowlist |
| `scripts/paper_sources.py` | Discover venue records, verify publisher evidence, retrieve complete PDFs and later-use evidence for classics |
| `scripts/recommendation_history.py` | Resolve permanent identities, reconcile prior evidence, conditionally write the ledger |
| `scripts/pipeline_prompts.py` | Build shared stage prompts and settings-derived output contracts |
| `scripts/ai_enrich.py`, `scripts/codex_enrich.py` | Transport the same stage inputs to hosted models or local Codex |
| `scripts/daily_pipeline.py` | Prepare and resume selection, full-paper analysis, visuals, trends, and review |
| `scripts/report_validation.py` | Validate evidence and settings limits; assemble Markdown and visual assets |
| `scripts/publish_daily.py` | Validate the isolated site build and archive a prepared transaction |
| `scripts/run_local_daily.py` | Synchronize `main`, run the pipeline, build the site, commit/push exact artifacts |
| `scripts/site_content.py`, `scripts/build_site.py`, `scripts/site_assets/` | Parse and display existing reports |

Preparation caches are ignored under `.cache/dailypaper/runs/<date>/`. They contain the selection, original PDFs, all page text/images, per-paper reviews, and a final bundle. Nothing enters publication until all stages and a site build pass. Publication records hashes and the settings digest in the canonical run ledger; historic fields and import evidence are retained. Retain the cache when recovering an interrupted reservation.

Classic selection can retrieve later citing texts when the initial screening has no independently verifiable influence source. A separate evidence check must establish use, adoption, or another configured influence criterion; a citation count or reference-list entry is insufficient. Unverified slots follow the settings' shortfall policy.

For debugging, `start-my-day/scripts/search_arxiv.py --output <path>` now delegates to the same venue discovery stage; its old filename is retained for existing command callers. `scripts/{codex_enrich,ai_enrich}.py --output <path>` prepare the same complete bundle. `scripts/publish_daily.py --input <bundle>` accepts only a validated bundle, never raw discovery or legacy abstract-enrichment JSON. Use the main runner for normal operation.

## Isolated checks

```bash
uv run --with-requirements requirements.txt python -m unittest discover -s tests -v
```

Fixtures use temporary repositories, generated PDFs, and mocked providers. No real recommendations, model calls, Git pushes, or production history writes occur. The existing reports can be rebuilt without generation with `python scripts/build_site.py --output-dir dist` after installing requirements.

## Retained manual utilities

These tools support existing notes and assets; they do not publish daily recommendations or own report preferences. Inspect each command's `--help` before using it.

- `rg -n 'keyword|author name' content/papers` searches existing notes.
- `start-my-day/scripts/scan_existing_notes.py` rebuilds the note search index; `link_keywords.py` links note keywords.
- `paper-analyze/scripts/generate_note.py` creates an explicitly requested manual note; `update_graph.py` maintains its graph metadata.
- `extract-paper-images/scripts/extract_images.py` extracts arXiv source-package figures, source PDF figures, or embedded PDF images. The active visual skill explains inspection and placement in the shared asset layout.

The redundant curator index and four historical `skill.md` wrappers had no runtime imports or surviving command dependencies. Their useful utility guidance is retained here and in the active stage skills. Historical setup documents remain under `docs/archive/` and are not runtime instructions.
