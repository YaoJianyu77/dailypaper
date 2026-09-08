# Verified implementation status

This file records evidence and gaps. [README.md](README.md) is the entry page; [Daily Paper Settings](DAILY_REPORT_PRODUCT_REQUIREMENTS.md) owns preferences; [AGENTS.md](AGENTS.md) owns execution rules.

## Implemented boundary

The local command and manual GitHub Action share `scripts/daily_pipeline.py`. Both model transports use `scripts/pipeline_prompts.py`; settings and output contracts are rebuilt from the six-section settings page. YAML is restricted to infrastructure. The old split quotas, expiring exclusions, abstract caps, fallback summaries, and missing full-analysis command have been removed from the generation path.

`scripts/recommendation_history.py` reads the complete canonical ledger plus prior recommendation evidence in archived reports and the legacy index. Publication reconciles that evidence without resetting existing records. A prepared run is reserved, written, verified, and finalized under a stable date-based ID. Retries verify the same artifacts; a non-forced Git update prevents overwriting another clone's commits.

No production reports, images, or history were generated or migrated during cleanup. Schedules and credentials were not changed. Technical module responsibilities and isolated test commands are in [implementation notes](docs/implementation.md).

## Verification

- All 26 offline tests pass, covering settings-only changes, both transports' full inputs, classic-influence retrieval, permanent aliases/imports, interrupted reservations, rejected evidence, and failed-push recovery against a temporary Git remote.
- Desktop (1440 px) and mobile (390 px) browser checks display the fixture's five figures and five HTML tables, with working figure zoom, no page overflow, and no JavaScript errors.
- All 52 existing reports build; their 51 image references are retained. Existing run/report/asset hashes verify. All 1,127 tracked content, state, cron-helper, and Pages-workflow files remain byte-for-byte unchanged from the cleanup baseline (`539994c`).
- Every prior work identity reaches the model prompts after evidence reconciliation: 622 source records produce 185 distinct work entries without dropping identity tokens. Complete raw evidence remains available to the controller and is preserved by ledger reconciliation.

## Remaining operational limitations

- Live model/provider generation and unattended server permissions have not been exercised by this cleanup. Offline fixtures verify orchestration and rejection paths; they do not certify a model's scientific judgment or provider availability.
- Discovery uses configured venues through DBLP/OpenAlex and verifies publisher evidence. Service indexing, request budgets, rate limits, inaccessible publisher pages, and ambiguous publication dates can reduce coverage. It is not an exhaustive proceedings crawl.
- Full-paper acquisition requires a readable PDF with extractable text on every page. Scanned pages requiring OCR, inaccessible appendices, oversized inputs, model refusals, and unverified publication or classic-influence evidence stop publication; no abstract fallback is used.
- Scientific claims, topic fit, renamed-work relationships without matching identifiers, and visual fidelity also undergo model review. Deterministic checks cover identity matches, evidence receipts, limits, paths, hashes, and rendering; they cannot prove semantic correctness.
- Interrupted reservations require the original preparation cache. Conflicting settings or concurrent Git changes stop safely and require reconciliation and revalidation of the same run. Neither pending reservations nor historical exclusions expire.

The existing Pages workflow builds archived content on pushes to `main`. A successful local build or commit is not evidence of a successful deployment; inspect the corresponding Pages run when deploying.
