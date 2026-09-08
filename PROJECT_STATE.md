# Verified implementation status

This file records evidence and gaps. [README.md](README.md) is the entry page; [Daily Paper Settings](DAILY_REPORT_PRODUCT_REQUIREMENTS.md) owns preferences; [AGENTS.md](AGENTS.md) owns execution rules.

## Implemented boundary

The production command uses `scripts/daily_pipeline.py`, shared stage prompts, and settings-derived output contracts. YAML is restricted to infrastructure; model choice and required Ultra mode belong to the six-section settings page. The old split quotas, expiring exclusions, abstract caps, fallback summaries, and missing full-analysis command have been removed from the generation path.

Five canonical skill folders are linked through `.agents/skills/`. Both native discovery and stage prompts use them; maintenance requests do not initiate report generation. The Codex app-server transport confirms the effective model and exact `ultra` setting before every stage, disables provider fallback, and retains authentication and permission controls. Each daily invocation checks current official recommendations and the account catalog, then proves tool access with an isolated synthetic PDF before discovery. Resolved model/mode and evidence receipts are logged under ignored `state/logs/`.

`bash scripts/install_local_cron.sh` installs or updates dependencies and manages one Cronie job using the existing runner. The settings currently specify 07:00 America/New_York. The installer preserves unrelated entries and restores their timezone; a whole-run lock prevents overlapping manual or scheduled invocations. Versioned local CLI installs avoid replacing active binaries on NFS.

`scripts/recommendation_history.py` reads the complete canonical ledger plus prior recommendation evidence in archived reports and the legacy index. Publication reconciles that evidence without resetting existing records. A prepared run is reserved, written, verified, and finalized under a stable date-based ID. Retries verify the same artifacts; a non-forced Git update prevents overwriting another clone's commits.

No production reports, images, or history were generated or migrated during this upgrade. The explicitly requested local schedule was installed; credentials and permission settings were preserved. The obsolete manual workflows `daily.yml`, `github-models-smoke.yml`, and `manual-smoke.yml` were removed after checking their references and callers. Only the Pages deployment workflow remains; the local daily cron job is unchanged. Technical module responsibilities and isolated test commands are in [implementation notes](docs/implementation.md).

## Verification

- All 38 offline tests pass, covering settings-only changes, shared full inputs, classic-influence retrieval, permanent aliases/imports, interrupted reservations, rejected evidence, and failed-push recovery against a temporary Git remote. Runtime/setup checks additionally cover changing official recommendations, missing Ultra/account access, per-turn settings, linked discovery, permission requests, timezone preservation, reinstall idempotency, DST, and cross-process exclusion.
- The actual setup command completed twice on the host. Readback confirmed exactly one 07:00 America/New_York job, the existing cron daemon running, and the run lock idle afterward. No daily report was triggered by either installation.
- On 2026-09-08, installed Codex 0.153.4 and the authenticated account verified the officially recommended `gpt-6-astra` with exact `ultra`. The real app-server execution read both synthetic PDF pages and their random evidence tokens, rendered and viewed a figure, executed native web search, and correctly distinguished generation from maintenance. This is a capability check, not a scientific report-quality evaluation.
- Desktop (1440 px) and mobile (390 px) browser checks display the fixture's five figures and five HTML tables, with working figure zoom, no page overflow, and no JavaScript errors.
- All 52 existing reports still build; their 51 image references are retained. Production content/state and the Pages workflow remain unchanged by this upgrade. The earlier cleanup verified all 1,127 tracked content/state, cron-helper and Pages-workflow files against its baseline (`539994c`); this upgrade intentionally replaces the local cron helper and removes the obsolete manual workflows.
- Every prior work identity reaches the model prompts after evidence reconciliation: 622 source records produce 185 distinct work entries without dropping identity tokens. Complete raw evidence remains available to the controller and is preserved by ledger reconciliation.

## Remaining operational limitations

- A complete live research report was intentionally not generated during these tests. Capability checks cannot certify scientific judgment, future service availability, or publisher access. Missing official evidence, unavailable Ultra, changed protocol/documentation, or an interactive authorization request stops unattended execution without a downgrade.
- Discovery uses configured venues through DBLP/OpenAlex and verifies publisher evidence. Service indexing, request budgets, rate limits, inaccessible publisher pages, and ambiguous publication dates can reduce coverage. It is not an exhaustive proceedings crawl.
- Full-paper acquisition requires a readable PDF with extractable text on every page. Scanned pages requiring OCR, inaccessible appendices, oversized inputs, model refusals, and unverified publication or classic-influence evidence stop publication; no abstract fallback is used.
- Scientific claims, topic fit, renamed-work relationships without matching identifiers, and visual fidelity also undergo model review. Deterministic checks cover identity matches, evidence receipts, limits, paths, hashes, and rendering; they cannot prove semantic correctness.
- Interrupted reservations require the original preparation cache. Conflicting settings or concurrent Git changes stop safely and require reconciliation and revalidation of the same run. Neither pending reservations nor historical exclusions expire.

The existing Pages workflow builds archived content on pushes to `main`. A successful local build or commit is not evidence of a successful deployment; inspect the corresponding Pages run when deploying.
